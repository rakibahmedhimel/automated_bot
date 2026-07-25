from datetime import date, time
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.breaks import ScheduleBreak
from backend.app.models.company import Company
from backend.app.models.schedule import (
    ScheduleOverride,
    ScheduleOverridePeriod,
    WeeklySchedule,
)


def _company_exists(db: Session, company_id: UUID) -> bool:
    return (
        db.query(Company.id)
        .filter(Company.id == company_id)
        .first()
        is not None
    )


def _periods_overlap(
    first_start: time,
    first_end: time,
    second_start: time,
    second_end: time,
) -> bool:
    return first_start < second_end and first_end > second_start


def _validate_periods(periods: list[dict]) -> str | None:
    ordered_periods = sorted(
        periods,
        key=lambda period: period["start_time"],
    )

    for period in ordered_periods:
        if period["start_time"] >= period["end_time"]:
            return "Each period start time must be before its end time"

    for previous, current in zip(
        ordered_periods,
        ordered_periods[1:],
    ):
        if _periods_overlap(
            previous["start_time"],
            previous["end_time"],
            current["start_time"],
            current["end_time"],
        ):
            return "Schedule periods cannot overlap"

    return None


def create_weekly_schedules(
    db: Session,
    company_id: UUID,
    day_of_week: int,
    periods: list[dict],
):
    if not _company_exists(db, company_id):
        return None, "Company not found"

    if not periods:
        return None, "At least one weekly schedule period is required"

    error = _validate_periods(periods)
    if error:
        return None, error

    existing_schedules = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.company_id == company_id,
            WeeklySchedule.day_of_week == day_of_week,
            WeeklySchedule.is_active.is_(True),
        )
        .all()
    )

    for period in periods:
        for existing in existing_schedules:
            if _periods_overlap(
                period["start_time"],
                period["end_time"],
                existing.start_time,
                existing.end_time,
            ):
                return None, "Weekly schedule periods cannot overlap"

    schedules = [
        WeeklySchedule(
            company_id=company_id,
            day_of_week=day_of_week,
            start_time=period["start_time"],
            end_time=period["end_time"],
            is_active=True,
        )
        for period in periods
    ]
    db.add_all(schedules)

    try:
        db.commit()
        for schedule in schedules:
            db.refresh(schedule)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to create weekly schedules"

    return schedules, None


def create_weekly_schedule(
    db: Session,
    company_id: UUID,
    day_of_week: int,
    start_time: time,
    end_time: time,
):
    schedules, error = create_weekly_schedules(
        db=db,
        company_id=company_id,
        day_of_week=day_of_week,
        periods=[
            {
                "start_time": start_time,
                "end_time": end_time,
            }
        ],
    )
    return (
        schedules[0] if schedules else None,
        error,
    )


def update_weekly_schedule(
    db: Session,
    company_id: UUID,
    schedule_id: UUID,
    update_data: dict,
):
    schedule = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.id == schedule_id,
            WeeklySchedule.company_id == company_id,
        )
        .first()
    )
    if not schedule:
        return None, "Weekly schedule period not found"

    day_of_week = update_data.get(
        "day_of_week",
        schedule.day_of_week,
    )
    start_time = update_data.get(
        "start_time",
        schedule.start_time,
    )
    end_time = update_data.get(
        "end_time",
        schedule.end_time,
    )
    is_active = update_data.get(
        "is_active",
        schedule.is_active,
    )

    if start_time >= end_time:
        return None, "Start time must be before end time"

    if is_active:
        overlapping = (
            db.query(WeeklySchedule)
            .filter(
                WeeklySchedule.company_id == company_id,
                WeeklySchedule.day_of_week == day_of_week,
                WeeklySchedule.is_active.is_(True),
                WeeklySchedule.id != schedule_id,
                WeeklySchedule.start_time < end_time,
                WeeklySchedule.end_time > start_time,
            )
            .first()
        )
        if overlapping:
            return None, "Weekly schedule periods cannot overlap"

    for field, value in update_data.items():
        setattr(schedule, field, value)

    try:
        db.commit()
        db.refresh(schedule)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to update weekly schedule period"

    return schedule, None


def delete_weekly_schedule(
    db: Session,
    company_id: UUID,
    schedule_id: UUID,
):
    schedule = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.id == schedule_id,
            WeeklySchedule.company_id == company_id,
        )
        .first()
    )
    if not schedule:
        return False, "Weekly schedule period not found"

    db.delete(schedule)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return False, "Unable to delete weekly schedule period"

    return True, None


def create_schedule_override(
    db: Session,
    company_id: UUID,
    override_date: date,
    is_closed: bool,
    reason: str | None,
    periods: list[dict],
):
    if not _company_exists(db, company_id):
        return None, "Company not found"

    if is_closed and periods:
        return None, "Closed overrides cannot include schedule periods"

    error = _validate_periods(periods)
    if error:
        return None, error

    override = (
        db.query(ScheduleOverride)
        .filter(
            ScheduleOverride.company_id == company_id,
            ScheduleOverride.date == override_date,
        )
        .first()
    )

    if override:
        override.is_closed = is_closed
        override.reason = reason
        override.periods.clear()
    else:
        override = ScheduleOverride(
            company_id=company_id,
            date=override_date,
            is_closed=is_closed,
            reason=reason,
        )
        db.add(override)

    if not is_closed:
        override.periods.extend(
            ScheduleOverridePeriod(
                start_time=period["start_time"],
                end_time=period["end_time"],
            )
            for period in periods
        )

    try:
        db.commit()
        db.refresh(override)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to save schedule override"

    return override, None


def delete_schedule_override(
    db: Session,
    company_id: UUID,
    override_id: UUID,
):
    override = (
        db.query(ScheduleOverride)
        .filter(
            ScheduleOverride.id == override_id,
            ScheduleOverride.company_id == company_id,
        )
        .first()
    )
    if not override:
        return False, "Schedule override not found"

    db.delete(override)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return False, "Unable to delete schedule override"

    return True, None


def create_schedule_break(
    db: Session,
    company_id: UUID,
    break_date: date,
    start_time: time,
    end_time: time,
    break_type: str,
    reason: str | None = None,
):
    if not _company_exists(db, company_id):
        return None, "Company not found"

    if start_time >= end_time:
        return None, "Break start time must be before end time"

    overlapping = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.company_id == company_id,
            ScheduleBreak.date == break_date,
            ScheduleBreak.start_time < end_time,
            ScheduleBreak.end_time > start_time,
        )
        .first()
    )
    if overlapping:
        return None, "Schedule breaks cannot overlap"

    schedule_break = ScheduleBreak(
        company_id=company_id,
        date=break_date,
        start_time=start_time,
        end_time=end_time,
        break_type=break_type,
        reason=reason,
    )
    db.add(schedule_break)

    try:
        db.commit()
        db.refresh(schedule_break)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to create schedule break"

    return schedule_break, None


def update_schedule_break(
    db: Session,
    company_id: UUID,
    break_id: UUID,
    update_data: dict,
):
    schedule_break = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.id == break_id,
            ScheduleBreak.company_id == company_id,
        )
        .first()
    )
    if not schedule_break:
        return None, "Schedule break not found"

    break_date = update_data.get("date", schedule_break.date)
    start_time = update_data.get(
        "start_time",
        schedule_break.start_time,
    )
    end_time = update_data.get(
        "end_time",
        schedule_break.end_time,
    )

    if start_time >= end_time:
        return None, "Break start time must be before end time"

    overlapping = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.company_id == company_id,
            ScheduleBreak.date == break_date,
            ScheduleBreak.id != break_id,
            ScheduleBreak.start_time < end_time,
            ScheduleBreak.end_time > start_time,
        )
        .first()
    )
    if overlapping:
        return None, "Schedule breaks cannot overlap"

    for field, value in update_data.items():
        setattr(schedule_break, field, value)

    try:
        db.commit()
        db.refresh(schedule_break)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to update schedule break"

    return schedule_break, None


def delete_schedule_break(
    db: Session,
    company_id: UUID,
    break_id: UUID,
):
    schedule_break = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.id == break_id,
            ScheduleBreak.company_id == company_id,
        )
        .first()
    )
    if not schedule_break:
        return False, "Schedule break not found"

    db.delete(schedule_break)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        return False, "Unable to delete schedule break"

    return True, None

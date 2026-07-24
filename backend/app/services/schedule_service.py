from datetime import date, time
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.breaks import ScheduleBreak
from backend.app.models.schedule import (
    ScheduleOverride,
    ScheduleOverridePeriod,
    WeeklySchedule,
)


def create_weekly_schedule(
    db: Session,
    company_id: UUID,
    day_of_week: int,
    start_time: time,
    end_time: time,
):
    if start_time >= end_time:
        return None, "Start time must be before end time"

    schedule = WeeklySchedule(
        company_id=company_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        is_active=True,
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return schedule, None


def create_schedule_override(
    db: Session,
    company_id: UUID,
    override_date: date,
    is_closed: bool,
    reason: str | None,
    periods: list[dict],
):
    existing_override = (
        db.query(ScheduleOverride)
        .filter(
            ScheduleOverride.company_id == company_id,
            ScheduleOverride.date == override_date,
        )
        .first()
    )

    if existing_override:
        existing_override.is_closed = is_closed
        existing_override.reason = reason

        db.query(ScheduleOverridePeriod).filter(
            ScheduleOverridePeriod.override_id
            == existing_override.id,
        ).delete()

        override = existing_override

    else:
        override = ScheduleOverride(
            company_id=company_id,
            date=override_date,
            is_closed=is_closed,
            reason=reason,
        )

        db.add(override)
        db.flush()

    if not is_closed:
        for period in periods:
            start_time = period["start_time"]
            end_time = period["end_time"]

            if start_time >= end_time:
                db.rollback()
                return None, (
                    "Each period start time must be before "
                    "its end time"
                )

            override_period = ScheduleOverridePeriod(
                override_id=override.id,
                start_time=start_time,
                end_time=end_time,
            )

            db.add(override_period)

    db.commit()
    db.refresh(override)

    return override, None


def create_schedule_break(
    db: Session,
    company_id: UUID,
    break_date: date,
    start_time: time,
    end_time: time,
    break_type: str,
    reason: str | None = None,
):
    if start_time >= end_time:
        return None, "Break start time must be before end time"

    schedule_break = ScheduleBreak(
        company_id=company_id,
        date=break_date,
        start_time=start_time,
        end_time=end_time,
        break_type=break_type,
        reason=reason,
    )

    db.add(schedule_break)
    db.commit()
    db.refresh(schedule_break)

    return schedule_break, None
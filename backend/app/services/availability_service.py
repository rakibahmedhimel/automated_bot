from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.appointment import Appointment
from backend.app.models.breaks import ScheduleBreak
from backend.app.models.company import Company
from backend.app.models.schedule import (
    ScheduleOverride,
    ScheduleOverridePeriod,
    WeeklySchedule,
)
from backend.app.models.service import Service


def get_available_slots(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    requested_date: date,
):
    company = (
        db.query(Company)
        .filter(
            Company.id == company_id,
            Company.is_active.is_(True),
        )
        .first()
    )

    if not company:
        return None

    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.company_id == company_id,
            Service.is_active.is_(True),
        )
        .first()
    )

    if not service:
        return None

    override = (
        db.query(ScheduleOverride)
        .filter(
            ScheduleOverride.company_id == company_id,
            ScheduleOverride.date == requested_date,
        )
        .first()
    )

    if override:
        if override.is_closed:
            return []

        override_periods = (
            db.query(ScheduleOverridePeriod)
            .filter(
                ScheduleOverridePeriod.override_id
                == override.id,
            )
            .order_by(
                ScheduleOverridePeriod.start_time,
            )
            .all()
        )

        schedule_periods = [
            (
                period.start_time,
                period.end_time,
            )
            for period in override_periods
        ]

    else:
        day_of_week = requested_date.weekday()

        weekly_schedules = (
            db.query(WeeklySchedule)
            .filter(
                WeeklySchedule.company_id == company_id,
                WeeklySchedule.day_of_week == day_of_week,
                WeeklySchedule.is_active.is_(True),
            )
            .order_by(
                WeeklySchedule.start_time,
            )
            .all()
        )

        schedule_periods = [
            (
                schedule.start_time,
                schedule.end_time,
            )
            for schedule in weekly_schedules
        ]

    if not schedule_periods:
        return []

    breaks = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.company_id == company_id,
            ScheduleBreak.date == requested_date,
        )
        .all()
    )

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.company_id == company_id,
            Appointment.appointment_date
            == requested_date,
            Appointment.status == "confirmed",
        )
        .all()
    )

    service_duration = timedelta(
        minutes=service.duration_minutes,
    )

    buffer_duration = timedelta(
        minutes=service.buffer_minutes,
    )

    available_slots = []

    for period_start, period_end in schedule_periods:
        current_datetime = datetime.combine(
            requested_date,
            period_start,
        )

        period_end_datetime = datetime.combine(
            requested_date,
            period_end,
        )

        while (
            current_datetime + service_duration
            <= period_end_datetime
        ):
            slot_start = current_datetime.time()

            slot_end_datetime = (
                current_datetime + service_duration
            )

            slot_end = slot_end_datetime.time()

            slot_blocked = False

            for schedule_break in breaks:
                if (
                    slot_start
                    < schedule_break.end_time
                    and slot_end
                    > schedule_break.start_time
                ):
                    slot_blocked = True
                    break

            if not slot_blocked:
                for appointment in appointments:
                    if (
                        slot_start
                        < appointment.end_time
                        and slot_end
                        > appointment.start_time
                    ):
                        slot_blocked = True
                        break

            if not slot_blocked:
                available_slots.append(
                    {
                        "start_time": slot_start,
                        "end_time": slot_end,
                    }
                )

            current_datetime += (
                service_duration
                + buffer_duration
            )

    return available_slots
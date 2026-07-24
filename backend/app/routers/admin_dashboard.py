from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.appointment import Appointment
from backend.app.models.breaks import ScheduleBreak
from backend.app.models.company import Company
from backend.app.models.schedule import (
    ScheduleOverride,
    WeeklySchedule,
)
from backend.app.models.schedule_request import ScheduleRequest
from backend.app.models.service import Service

router = APIRouter(
    prefix="/admin/companies/{company_id}/dashboard",
    tags=["Admin Dashboard"],
)


@router.get("/")
def get_admin_dashboard(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    today = date.today()
    upcoming_date = today + timedelta(days=30)

    services = (
        db.query(Service)
        .filter(
            Service.company_id == company_id,
            Service.is_active.is_(True),
        )
        .all()
    )

    weekly_schedule = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.company_id == company_id,
            WeeklySchedule.is_active.is_(True),
        )
        .order_by(
            WeeklySchedule.day_of_week,
            WeeklySchedule.start_time,
        )
        .all()
    )

    overrides = (
        db.query(ScheduleOverride)
        .filter(
            ScheduleOverride.company_id == company_id,
            ScheduleOverride.date >= today,
            ScheduleOverride.date <= upcoming_date,
        )
        .order_by(ScheduleOverride.date)
        .all()
    )

    breaks = (
        db.query(ScheduleBreak)
        .filter(
            ScheduleBreak.company_id == company_id,
            ScheduleBreak.date >= today,
            ScheduleBreak.date <= upcoming_date,
        )
        .order_by(
            ScheduleBreak.date,
            ScheduleBreak.start_time,
        )
        .all()
    )

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.company_id == company_id,
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= upcoming_date,
        )
        .order_by(
            Appointment.appointment_date,
            Appointment.start_time,
        )
        .all()
    )

    schedule_requests = (
        db.query(ScheduleRequest)
        .filter(
            ScheduleRequest.company_id == company_id,
            ScheduleRequest.status == "pending",
        )
        .order_by(
            ScheduleRequest.created_at.desc(),
        )
        .all()
    )

    return {
        "company": company,
        "services": services,
        "weekly_schedule": weekly_schedule,
        "schedule_overrides": overrides,
        "breaks": breaks,
        "upcoming_appointments": appointments,
        "pending_schedule_requests": schedule_requests,
    }
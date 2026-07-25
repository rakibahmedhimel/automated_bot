from datetime import date, time
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.company import Company
from backend.app.models.schedule_request import (
    ScheduleRequest,
)
from backend.app.models.service import Service


def create_schedule_request(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    requested_date: date,
    preferred_start_time: time | None = None,
    preferred_end_time: time | None = None,
    message: str | None = None,
    external_user_id: str | None = None,
    customer_name: str | None = None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        return None, "Company not found"

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
        return None, "Service not found"

    if (
        preferred_start_time is not None
        and preferred_end_time is not None
        and preferred_start_time >= preferred_end_time
    ):
        return None, (
            "Preferred start time must be before preferred end time"
        )

    schedule_request = ScheduleRequest(
        company_id=company_id,
        service_id=service_id,
        requested_date=requested_date,
        preferred_start_time=preferred_start_time,
        preferred_end_time=preferred_end_time,
        message=message,
        external_user_id=external_user_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        status="pending",
    )

    db.add(schedule_request)
    try:
        db.commit()
        db.refresh(schedule_request)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to create schedule request"

    return schedule_request, None

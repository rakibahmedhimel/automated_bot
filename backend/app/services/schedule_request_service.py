from datetime import date, time
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models.schedule_request import (
    ScheduleRequest,
)


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
    db.commit()
    db.refresh(schedule_request)

    return schedule_request, None
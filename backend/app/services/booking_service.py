from datetime import date, time
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.appointment import Appointment
from backend.app.models.company import Company
from backend.app.models.service import Service
from backend.app.services.availability_service import (
    get_available_slots,
)


def create_appointment(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    appointment_date: date,
    start_time: time,
    external_user_id: str | None = None,
    customer_name: str | None = None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
    commit: bool = True,
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

    try:
        available_slots = get_available_slots(
            db=db,
            company_id=company_id,
            service_id=service_id,
            requested_date=appointment_date,
        )
    except ValueError as exc:
        return None, str(exc)

    if available_slots is None:
        return None, "Company or service not found"

    selected_slot = next(
        (
            slot
            for slot in available_slots
            if slot["start_time"] == start_time
        ),
        None,
    )

    if not selected_slot:
        return None, (
            "This time slot is no longer available"
        )

    appointment = Appointment(
        company_id=company_id,
        service_id=service_id,
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=selected_slot["end_time"],
        status="confirmed",
        external_user_id=external_user_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
    )

    db.add(appointment)

    try:
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(appointment)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to create appointment"

    return appointment, None

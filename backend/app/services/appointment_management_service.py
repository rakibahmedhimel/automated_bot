from datetime import date, time
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.appointment import Appointment
from backend.app.services.booking_service import create_appointment


def list_customer_appointments(
    db: Session,
    company_id: UUID,
    external_user_id: str | None = None,
    customer_email: str | None = None,
    service_id: UUID | None = None,
    appointment_date: date | None = None,
    start_time: time | None = None,
):
    query = db.query(Appointment).filter(
        Appointment.company_id == company_id,
    )
    if external_user_id:
        query = query.filter(
            Appointment.external_user_id == external_user_id,
        )
    elif customer_email:
        query = query.filter(
            Appointment.customer_email == customer_email,
        )
    else:
        return None, "Customer identity is required"

    if service_id:
        query = query.filter(Appointment.service_id == service_id)
    if appointment_date:
        query = query.filter(
            Appointment.appointment_date == appointment_date,
        )
    if start_time:
        query = query.filter(Appointment.start_time == start_time)

    appointments = (
        query.order_by(
            Appointment.appointment_date,
            Appointment.start_time,
        )
        .all()
    )
    return appointments, None


def reschedule_appointment(
    db: Session,
    company_id: UUID,
    appointment_id: UUID,
    new_date: date,
    new_start_time: time,
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.company_id == company_id,
            Appointment.status == "confirmed",
        )
        .first()
    )
    if not appointment:
        return None, "Confirmed appointment not found"

    replacement, error = create_appointment(
        db=db,
        company_id=company_id,
        service_id=appointment.service_id,
        appointment_date=new_date,
        start_time=new_start_time,
        external_user_id=appointment.external_user_id,
        customer_name=appointment.customer_name,
        customer_email=appointment.customer_email,
        customer_phone=appointment.customer_phone,
        commit=False,
    )
    if error:
        db.rollback()
        return None, error

    appointment.status = "cancelled"
    appointment.cancellation_reason = (
        f"Rescheduled to {new_date.isoformat()} "
        f"at {new_start_time.isoformat()}"
    )
    try:
        db.commit()
        db.refresh(replacement)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to reschedule appointment"

    return replacement, None

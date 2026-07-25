from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.appointment import Appointment


def cancel_appointment(
    db: Session,
    company_id: UUID,
    appointment_id: UUID,
    cancellation_reason: str | None = None,
):
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.company_id == company_id,
        )
        .first()
    )

    if not appointment:
        return None, "Appointment not found"

    if appointment.status == "cancelled":
        return None, "Appointment is already cancelled"

    if appointment.status == "completed":
        return None, "Completed appointments cannot be cancelled"

    if appointment.status == "no_show":
        return None, "No-show appointments cannot be cancelled"

    appointment.status = "cancelled"
    appointment.cancellation_reason = (
        cancellation_reason
    )

    try:
        db.commit()
        db.refresh(appointment)
    except SQLAlchemyError:
        db.rollback()
        return None, "Unable to cancel appointment"

    return appointment, None

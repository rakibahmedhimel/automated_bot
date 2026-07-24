from uuid import UUID

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

    db.commit()
    db.refresh(appointment)

    return appointment, None
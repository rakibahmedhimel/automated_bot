from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentResponse,
    AppointmentStatusUpdate,
)
from backend.app.services.booking_service import (
    create_appointment,
)
from backend.app.services.cancellation_service import (
    cancel_appointment,
)

router = APIRouter(
    prefix="/companies/{company_id}/appointments",
    tags=["Appointments"],
)


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    company_id: UUID,
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
):
    appointment, error = create_appointment(
        db=db,
        company_id=company_id,
        service_id=appointment_data.service_id,
        appointment_date=appointment_data.appointment_date,
        start_time=appointment_data.start_time,
        external_user_id=appointment_data.external_user_id,
        customer_name=appointment_data.customer_name,
        customer_email=appointment_data.customer_email,
        customer_phone=appointment_data.customer_phone,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return appointment


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment_route(
    company_id: UUID,
    appointment_id: UUID,
    cancel_data: AppointmentCancel,
    db: Session = Depends(get_db),
):
    appointment, error = cancel_appointment(
        db=db,
        company_id=company_id,
        appointment_id=appointment_id,
        cancellation_reason=(
            cancel_data.cancellation_reason
        ),
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return appointment


@router.patch(
    "/{appointment_id}/status",
    response_model=AppointmentResponse,
)
def update_appointment_status(
    company_id: UUID,
    appointment_id: UUID,
    status_data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
):
    from backend.app.models.appointment import Appointment

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.company_id == company_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    appointment.status = status_data.status

    db.commit()
    db.refresh(appointment)

    return appointment


@router.get(
    "/my",
    response_model=list[AppointmentResponse],
)
def get_my_appointments(
    company_id: UUID,
    external_user_id: str,
    db: Session = Depends(get_db),
):
    from backend.app.models.appointment import Appointment

    return (
        db.query(Appointment)
        .filter(
            Appointment.company_id == company_id,
            Appointment.external_user_id == external_user_id,
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.start_time.desc(),
        )
        .all()
    )

@router.get(
    "/lookup",
    response_model=list[AppointmentResponse],
)
def lookup_appointments(
    company_id: UUID,
    customer_email: str,
    db: Session = Depends(get_db),
):
    from backend.app.models.appointment import Appointment

    return (
        db.query(Appointment)
        .filter(
            Appointment.company_id == company_id,
            Appointment.customer_email == customer_email,
        )
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.start_time.desc(),
        )
        .all()
    )

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    company_id: UUID,
    appointment_id: UUID,
    db: Session = Depends(get_db),
):
    from backend.app.models.appointment import Appointment

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.company_id == company_id,
        )
        .first()
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    return appointment
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.services.availability_service import (
    get_available_slots,
)
from backend.app.services.booking_service import (
    create_appointment,
)
from backend.app.services.cancellation_service import (
    cancel_appointment,
)
from backend.app.services.schedule_request_service import (
    create_schedule_request,
)
from backend.app.services.appointment_management_service import (
    list_customer_appointments,
    reschedule_appointment,
)


def tool_get_available_slots(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    requested_date: date,
):
    return get_available_slots(
        db=db,
        company_id=company_id,
        service_id=service_id,
        requested_date=requested_date,
    )


def tool_book_appointment(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    appointment_date,
    start_time,
    external_user_id=None,
    customer_name=None,
    customer_email=None,
    customer_phone=None,
):
    return create_appointment(
        db=db,
        company_id=company_id,
        service_id=service_id,
        appointment_date=appointment_date,
        start_time=start_time,
        external_user_id=external_user_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
    )


def tool_cancel_appointment(
    db: Session,
    company_id: UUID,
    appointment_id: UUID,
    cancellation_reason=None,
):
    return cancel_appointment(
        db=db,
        company_id=company_id,
        appointment_id=appointment_id,
        cancellation_reason=cancellation_reason,
    )


def tool_request_schedule(
    db: Session,
    company_id: UUID,
    service_id: UUID,
    requested_date,
    preferred_start_time=None,
    preferred_end_time=None,
    message=None,
    external_user_id=None,
    customer_name=None,
    customer_email=None,
    customer_phone=None,
):
    return create_schedule_request(
        db=db,
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
    )


def tool_list_customer_appointments(
    db: Session,
    company_id: UUID,
    external_user_id=None,
    customer_email=None,
    service_id=None,
    appointment_date=None,
    start_time=None,
):
    return list_customer_appointments(
        db=db,
        company_id=company_id,
        external_user_id=external_user_id,
        customer_email=customer_email,
        service_id=service_id,
        appointment_date=appointment_date,
        start_time=start_time,
    )


def tool_reschedule_appointment(
    db: Session,
    company_id: UUID,
    appointment_id: UUID,
    new_date,
    new_start_time,
):
    return reschedule_appointment(
        db=db,
        company_id=company_id,
        appointment_id=appointment_id,
        new_date=new_date,
        new_start_time=new_start_time,
    )

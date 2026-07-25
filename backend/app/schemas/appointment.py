from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    service_id: UUID
    appointment_date: date
    start_time: time

    external_user_id: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


class AppointmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    service_id: UUID

    appointment_date: date
    start_time: time
    end_time: time

    status: str

    external_user_id: str | None
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None

    cancellation_reason: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class AppointmentStatusUpdate(BaseModel):
    status: Literal[
        "confirmed",
        "cancelled",
        "completed",
        "no_show",
    ]


class AppointmentCancel(BaseModel):
    cancellation_reason: str | None = None

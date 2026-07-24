from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduleRequestCreate(BaseModel):
    service_id: UUID
    requested_date: date
    preferred_start_time: time | None = None
    preferred_end_time: time | None = None
    message: str | None = None

    external_user_id: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None

class ScheduleRequestStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "approved",
        "rejected",
    ]

class ScheduleRequestResponse(BaseModel):
    id: UUID
    company_id: UUID
    service_id: UUID

    requested_date: date
    preferred_start_time: time | None
    preferred_end_time: time | None

    message: str | None
    status: str

    external_user_id: str | None
    customer_name: str | None
    customer_email: str | None
    customer_phone: str | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
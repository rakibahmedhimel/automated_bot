from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CustomerConversationCreate(BaseModel):
    external_user_id: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    appointment_id: UUID | None = None
    schedule_request_id: UUID | None = None
    subject: str = Field(min_length=1, max_length=255)
    initial_message: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.external_user_id and not self.customer_email:
            raise ValueError(
                "external_user_id or customer_email is required"
            )
        return self


class CustomerConversationResponse(BaseModel):
    id: UUID
    company_id: UUID
    external_user_id: str | None
    customer_name: str | None
    customer_email: str | None
    appointment_id: UUID | None
    schedule_request_id: UUID | None
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    latest_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    external_user_id: str | None = None
    customer_email: str | None = None


class AdminMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class CustomerMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_type: Literal["customer", "admin"]
    content: str
    created_at: datetime
    read_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationStatusUpdate(BaseModel):
    status: Literal["open", "closed"]

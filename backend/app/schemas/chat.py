from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    external_user_id: str | None = None
    title: str | None = None


class ChatSessionUpdate(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=80,
    )


class ChatSessionResponse(BaseModel):
    id: UUID
    company_id: UUID
    external_user_id: str | None
    title: str | None
    is_archived: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class ChatMessageCreate(BaseModel):
    content: str
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

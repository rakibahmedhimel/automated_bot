from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatSessionCreate(BaseModel):
    external_user_id: str | None = None
    title: str | None = None


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


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
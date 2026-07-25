from datetime import datetime

from pydantic import BaseModel, Field


class OpenAIKeyUpdate(BaseModel):
    api_key: str = Field(min_length=8)


class OpenAISettingResponse(BaseModel):
    provider: str = "openai"
    configured: bool
    masked_key: str | None
    updated_at: datetime | None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int = Field(gt=0)
    buffer_minutes: int = Field(default=0, ge=0)


class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    buffer_minutes: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    
class ServiceResponse(ServiceBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

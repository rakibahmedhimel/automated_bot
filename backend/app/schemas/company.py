from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompanyBase(BaseModel):
    name: str
    slug: str
    timezone: str = "Asia/Dhaka"


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
    
class CompanyResponse(CompanyBase):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
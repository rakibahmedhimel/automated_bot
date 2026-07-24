from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchedulePeriodCreate(BaseModel):
    start_time: time
    end_time: time

class ScheduleOverridePeriodCreate(BaseModel):
    start_time: time
    end_time: time

class WeeklyScheduleCreate(BaseModel):
    day_of_week: int = Field(
        ge=0,
        le=6,
    )
    periods: list[ScheduleOverridePeriodCreate] = Field(
        default_factory=list
    )

class WeeklyScheduleResponse(BaseModel):
    id: UUID
    company_id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class ScheduleOverridePeriodResponse(BaseModel):
    id: UUID
    override_id: UUID
    start_time: time
    end_time: time
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

class ScheduleOverrideCreate(BaseModel):
    date: date
    is_closed: bool = False
    reason: str | None = None
    periods: list[ScheduleOverridePeriodCreate] = []

class ScheduleOverrideResponse(BaseModel):
    id: UUID
    company_id: UUID
    date: date
    is_closed: bool
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
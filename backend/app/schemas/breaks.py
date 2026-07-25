from datetime import date as DateType
from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduleBreakCreate(BaseModel):
    date: DateType
    start_time: time
    end_time: time
    break_type: str
    reason: str | None = None


class ScheduleBreakUpdate(BaseModel):
    date: DateType | None = None
    start_time: time | None = None
    end_time: time | None = None
    break_type: str | None = None
    reason: str | None = None


class ScheduleBreakResponse(BaseModel):
    id: UUID
    company_id: UUID
    date: DateType
    start_time: time
    end_time: time
    break_type: str
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )

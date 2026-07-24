from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduleBreakCreate(BaseModel):
    date: date
    start_time: time
    end_time: time
    break_type: str
    reason: str | None = None


class ScheduleBreakResponse(BaseModel):
    id: UUID
    company_id: UUID
    date: date
    start_time: time
    end_time: time
    break_type: str
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
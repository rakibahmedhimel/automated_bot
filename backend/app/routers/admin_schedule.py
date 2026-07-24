from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.breaks import (
    ScheduleBreakCreate,
    ScheduleBreakResponse,
)
from backend.app.schemas.schedule import (
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    WeeklyScheduleCreate,
    WeeklyScheduleResponse,
)
from backend.app.services.schedule_service import (
    create_schedule_break,
    create_schedule_override,
    create_weekly_schedule,
)

router = APIRouter(
    prefix="/companies/{company_id}/admin/schedule",
    tags=["Admin Schedule"],
)


@router.post(
    "/weekly",
    response_model=WeeklyScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_weekly_schedule_route(
    company_id: UUID,
    schedule_data: WeeklyScheduleCreate,
    db: Session = Depends(get_db),
):
    if len(schedule_data.periods) != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Weekly schedule currently accepts "
                "one period per request"
            ),
        )

    period = schedule_data.periods[0]

    schedule, error = create_weekly_schedule(
        db=db,
        company_id=company_id,
        day_of_week=schedule_data.day_of_week,
        start_time=period.start_time,
        end_time=period.end_time,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return schedule


@router.post(
    "/override",
    response_model=ScheduleOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule_override_route(
    company_id: UUID,
    override_data: ScheduleOverrideCreate,
    db: Session = Depends(get_db),
):
    override, error = create_schedule_override(
        db=db,
        company_id=company_id,
        override_date=override_data.date,
        is_closed=override_data.is_closed,
        reason=override_data.reason,
        periods=[
            {
                "start_time": period.start_time,
                "end_time": period.end_time,
            }
            for period in override_data.periods
        ],
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return override


@router.post(
    "/break",
    response_model=ScheduleBreakResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule_break_route(
    company_id: UUID,
    break_data: ScheduleBreakCreate,
    db: Session = Depends(get_db),
):
    schedule_break, error = create_schedule_break(
        db=db,
        company_id=company_id,
        break_date=break_data.date,
        start_time=break_data.start_time,
        end_time=break_data.end_time,
        break_type=break_data.break_type,
        reason=break_data.reason,
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    return schedule_break
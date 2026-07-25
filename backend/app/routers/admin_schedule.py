from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from backend.app.core.database import get_db
from backend.app.models.breaks import ScheduleBreak
from backend.app.models.schedule import (
    ScheduleOverride,
    WeeklySchedule,
)
from backend.app.schemas.breaks import (
    ScheduleBreakCreate,
    ScheduleBreakResponse,
    ScheduleBreakUpdate,
)
from backend.app.schemas.schedule import (
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    WeeklyScheduleCreate,
    WeeklyScheduleResponse,
    WeeklyScheduleUpdate,
)
from backend.app.services.schedule_service import (
    create_schedule_break,
    create_schedule_override,
    create_weekly_schedules,
    delete_schedule_break,
    delete_schedule_override,
    delete_weekly_schedule,
    update_schedule_break,
    update_weekly_schedule,
)

router = APIRouter(
    prefix="/companies/{company_id}/admin/schedule",
    tags=["Admin Schedule"],
)


def _raise_service_error(error: str) -> None:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if "not found" in error.lower()
        else status.HTTP_400_BAD_REQUEST
    )
    raise HTTPException(
        status_code=status_code,
        detail=error,
    )


@router.get(
    "/weekly",
    response_model=list[WeeklyScheduleResponse],
)
def get_weekly_schedules(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    return (
        db.query(WeeklySchedule)
        .filter(WeeklySchedule.company_id == company_id)
        .order_by(
            WeeklySchedule.day_of_week,
            WeeklySchedule.start_time,
        )
        .all()
    )


@router.post(
    "/weekly",
    response_model=list[WeeklyScheduleResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_weekly_schedule_route(
    company_id: UUID,
    schedule_data: WeeklyScheduleCreate,
    db: Session = Depends(get_db),
):
    schedules, error = create_weekly_schedules(
        db=db,
        company_id=company_id,
        day_of_week=schedule_data.day_of_week,
        periods=[
            {
                "start_time": period.start_time,
                "end_time": period.end_time,
            }
            for period in schedule_data.periods
        ],
    )
    if error:
        _raise_service_error(error)
    return schedules


@router.patch(
    "/weekly/{schedule_id}",
    response_model=WeeklyScheduleResponse,
)
def update_weekly_schedule_route(
    company_id: UUID,
    schedule_id: UUID,
    schedule_data: WeeklyScheduleUpdate,
    db: Session = Depends(get_db),
):
    schedule, error = update_weekly_schedule(
        db=db,
        company_id=company_id,
        schedule_id=schedule_id,
        update_data=schedule_data.model_dump(
            exclude_unset=True,
        ),
    )
    if error:
        _raise_service_error(error)
    return schedule


@router.delete(
    "/weekly/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_weekly_schedule_route(
    company_id: UUID,
    schedule_id: UUID,
    db: Session = Depends(get_db),
):
    _, error = delete_weekly_schedule(
        db=db,
        company_id=company_id,
        schedule_id=schedule_id,
    )
    if error:
        _raise_service_error(error)


@router.get(
    "/override",
    response_model=list[ScheduleOverrideResponse],
)
def get_schedule_overrides(
    company_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(ScheduleOverride)
        .options(selectinload(ScheduleOverride.periods))
        .filter(ScheduleOverride.company_id == company_id)
    )
    if start_date is not None:
        query = query.filter(ScheduleOverride.date >= start_date)
    if end_date is not None:
        query = query.filter(ScheduleOverride.date <= end_date)
    return query.order_by(ScheduleOverride.date).all()


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
        _raise_service_error(error)
    return override


@router.delete(
    "/override/{override_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_schedule_override_route(
    company_id: UUID,
    override_id: UUID,
    db: Session = Depends(get_db),
):
    _, error = delete_schedule_override(
        db=db,
        company_id=company_id,
        override_id=override_id,
    )
    if error:
        _raise_service_error(error)


@router.get(
    "/break",
    response_model=list[ScheduleBreakResponse],
)
def get_schedule_breaks(
    company_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ScheduleBreak).filter(
        ScheduleBreak.company_id == company_id,
    )
    if start_date is not None:
        query = query.filter(ScheduleBreak.date >= start_date)
    if end_date is not None:
        query = query.filter(ScheduleBreak.date <= end_date)
    return query.order_by(
        ScheduleBreak.date,
        ScheduleBreak.start_time,
    ).all()


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
        _raise_service_error(error)
    return schedule_break


@router.patch(
    "/break/{break_id}",
    response_model=ScheduleBreakResponse,
)
def update_schedule_break_route(
    company_id: UUID,
    break_id: UUID,
    break_data: ScheduleBreakUpdate,
    db: Session = Depends(get_db),
):
    schedule_break, error = update_schedule_break(
        db=db,
        company_id=company_id,
        break_id=break_id,
        update_data=break_data.model_dump(
            exclude_unset=True,
        ),
    )
    if error:
        _raise_service_error(error)
    return schedule_break


@router.delete(
    "/break/{break_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_schedule_break_route(
    company_id: UUID,
    break_id: UUID,
    db: Session = Depends(get_db),
):
    _, error = delete_schedule_break(
        db=db,
        company_id=company_id,
        break_id=break_id,
    )
    if error:
        _raise_service_error(error)

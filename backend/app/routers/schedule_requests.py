from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.schedule_request import ScheduleRequest
from backend.app.schemas.schedule_request import (
    ScheduleRequestCreate,
    ScheduleRequestResponse,
    ScheduleRequestStatusUpdate,
)
from backend.app.services.schedule_request_service import (
    create_schedule_request,
)

router = APIRouter(
    prefix="/companies/{company_id}/schedule-requests",
    tags=["Schedule Requests"],
)


@router.post(
    "/",
    response_model=ScheduleRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_schedule(
    company_id: UUID,
    request_data: ScheduleRequestCreate,
    db: Session = Depends(get_db),
):
    schedule_request, error = create_schedule_request(
        db=db,
        company_id=company_id,
        service_id=request_data.service_id,
        requested_date=request_data.requested_date,
        preferred_start_time=request_data.preferred_start_time,
        preferred_end_time=request_data.preferred_end_time,
        message=request_data.message,
        external_user_id=request_data.external_user_id,
        customer_name=request_data.customer_name,
        customer_email=request_data.customer_email,
        customer_phone=request_data.customer_phone,
    )

    if error:
        raise HTTPException(
            status_code=400,
            detail=error,
        )

    return schedule_request


@router.get(
    "/",
    response_model=list[ScheduleRequestResponse],
)
def get_schedule_requests(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    return (
        db.query(ScheduleRequest)
        .filter(
            ScheduleRequest.company_id == company_id,
        )
        .order_by(
            ScheduleRequest.created_at.desc(),
        )
        .all()
    )

@router.patch(
    "/{request_id}/status",
    response_model=ScheduleRequestResponse,
)
def update_schedule_request_status(
    company_id: UUID,
    request_id: UUID,
    status_data: ScheduleRequestStatusUpdate,
    db: Session = Depends(get_db),
):
    schedule_request = (
        db.query(ScheduleRequest)
        .filter(
            ScheduleRequest.id == request_id,
            ScheduleRequest.company_id == company_id,
        )
        .first()
    )

    if not schedule_request:
        raise HTTPException(
            status_code=404,
            detail="Schedule request not found",
        )

    schedule_request.status = status_data.status

    db.commit()
    db.refresh(schedule_request)

    return schedule_request





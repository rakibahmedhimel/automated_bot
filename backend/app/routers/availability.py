from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.availability_service import (
    get_available_slots,
)

router = APIRouter(
    prefix="/companies/{company_id}/availability",
    tags=["Availability"],
)


@router.get("/")
def get_available_slots_route(
    company_id: UUID,
    service_id: UUID,
    requested_date: date,
    db: Session = Depends(get_db),
):
    try:
        slots = get_available_slots(
            db=db,
            company_id=company_id,
            service_id=service_id,
            requested_date=requested_date,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if slots is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Company or service not found"
            ),
        )

    return {
        "company_id": company_id,
        "service_id": service_id,
        "date": requested_date,
        "slots": slots,
    }

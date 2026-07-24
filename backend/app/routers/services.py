from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.service import Service
from backend.app.schemas.service import (
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter(
    prefix="/companies/{company_id}/services",
    tags=["Services"],
)


@router.post(
    "/",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    company_id: UUID,
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
):
    service = Service(
        company_id=company_id,
        name=service_data.name,
        description=service_data.description,
        duration_minutes=(
            service_data.duration_minutes
        ),
        buffer_minutes=(
            service_data.buffer_minutes
        ),
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@router.get(
    "/",
    response_model=list[ServiceResponse],
)
def get_services(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    return (
        db.query(Service)
        .filter(
            Service.company_id == company_id,
            Service.is_active.is_(True),
        )
        .order_by(Service.created_at)
        .all()
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
)
def get_service(
    company_id: UUID,
    service_id: UUID,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.company_id == company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    return service


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
)
def update_service(
    company_id: UUID,
    service_id: UUID,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
):
    service = (
        db.query(Service)
        .filter(
            Service.id == service_id,
            Service.company_id == company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    update_data = service_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service
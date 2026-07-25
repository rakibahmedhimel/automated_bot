from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.appointment import Appointment
from backend.app.models.company import Company
from backend.app.models.customer_conversation import (
    CustomerConversation,
    CustomerConversationMessage,
)
from backend.app.models.schedule_request import ScheduleRequest
from backend.app.schemas.customer_conversation import (
    AdminMessageCreate,
    ConversationStatusUpdate,
    CustomerConversationCreate,
    CustomerConversationResponse,
    CustomerMessageCreate,
    CustomerMessageResponse,
)

router = APIRouter(tags=["Customer conversations"])
admin_router = APIRouter(tags=["Admin customer conversations"])


def _company_or_404(db: Session, company_id: UUID):
    if not db.query(Company.id).filter(Company.id == company_id).first():
        raise HTTPException(status_code=404, detail="Company not found")


def _identity_filter(external_user_id: str | None, customer_email: str | None):
    conditions = []
    if external_user_id:
        conditions.append(
            CustomerConversation.external_user_id == external_user_id
        )
    if customer_email:
        conditions.append(
            CustomerConversation.customer_email == customer_email
        )
    if not conditions:
        raise HTTPException(
            status_code=400,
            detail="external_user_id or customer_email is required",
        )
    return or_(*conditions)


def _customer_conversation(
    db: Session,
    company_id: UUID,
    conversation_id: UUID,
    external_user_id: str | None,
    customer_email: str | None,
):
    conversation = (
        db.query(CustomerConversation)
        .filter(
            CustomerConversation.id == conversation_id,
            CustomerConversation.company_id == company_id,
            _identity_filter(external_user_id, customer_email),
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _commit(db: Session, detail: str):
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=detail) from exc


@router.post(
    "/companies/{company_id}/customer-conversations",
    response_model=CustomerConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    company_id: UUID,
    data: CustomerConversationCreate,
    db: Session = Depends(get_db),
):
    _company_or_404(db, company_id)
    if data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == data.appointment_id,
            Appointment.company_id == company_id,
        ).first()
        if not appointment:
            raise HTTPException(400, "Appointment does not belong to company")
        if data.external_user_id and appointment.external_user_id != data.external_user_id:
            raise HTTPException(400, "Appointment does not belong to customer")
        if data.customer_email and appointment.customer_email != data.customer_email:
            raise HTTPException(400, "Appointment does not belong to customer")
    if data.schedule_request_id:
        request = db.query(ScheduleRequest).filter(
            ScheduleRequest.id == data.schedule_request_id,
            ScheduleRequest.company_id == company_id,
        ).first()
        if not request:
            raise HTTPException(400, "Schedule request does not belong to company")
        if data.external_user_id and request.external_user_id != data.external_user_id:
            raise HTTPException(400, "Schedule request does not belong to customer")
        if data.customer_email and request.customer_email != data.customer_email:
            raise HTTPException(400, "Schedule request does not belong to customer")

    conversation = CustomerConversation(
        company_id=company_id,
        external_user_id=data.external_user_id,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        appointment_id=data.appointment_id,
        schedule_request_id=data.schedule_request_id,
        subject=data.subject.strip(),
    )
    db.add(conversation)
    db.flush()
    if data.initial_message:
        db.add(CustomerConversationMessage(
            conversation_id=conversation.id,
            sender_type="customer",
            content=data.initial_message.strip(),
        ))
    _commit(db, "Unable to create conversation")
    db.refresh(conversation)
    return conversation


@router.get(
    "/companies/{company_id}/customer-conversations",
    response_model=list[CustomerConversationResponse],
)
def list_customer_conversations(
    company_id: UUID,
    external_user_id: str | None = None,
    customer_email: str | None = None,
    appointment_id: UUID | None = None,
    schedule_request_id: UUID | None = None,
    conversation_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    _company_or_404(db, company_id)
    query = db.query(CustomerConversation).filter(
        CustomerConversation.company_id == company_id,
        _identity_filter(external_user_id, customer_email),
    )
    if appointment_id:
        query = query.filter(CustomerConversation.appointment_id == appointment_id)
    if schedule_request_id:
        query = query.filter(
            CustomerConversation.schedule_request_id == schedule_request_id
        )
    if conversation_status:
        if conversation_status not in {"open", "closed"}:
            raise HTTPException(400, "Invalid conversation status")
        query = query.filter(CustomerConversation.status == conversation_status)
    return query.order_by(CustomerConversation.updated_at.desc()).all()


@router.get(
    "/companies/{company_id}/customer-conversations/{conversation_id}/messages",
    response_model=list[CustomerMessageResponse],
)
def list_customer_messages(
    company_id: UUID,
    conversation_id: UUID,
    external_user_id: str | None = None,
    customer_email: str | None = None,
    db: Session = Depends(get_db),
):
    conversation = _customer_conversation(
        db, company_id, conversation_id, external_user_id, customer_email
    )
    return conversation.messages


@router.post(
    "/companies/{company_id}/customer-conversations/{conversation_id}/messages",
    response_model=CustomerMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_customer_message(
    company_id: UUID,
    conversation_id: UUID,
    data: CustomerMessageCreate,
    db: Session = Depends(get_db),
):
    conversation = _customer_conversation(
        db,
        company_id,
        conversation_id,
        data.external_user_id,
        data.customer_email,
    )
    if conversation.status == "closed":
        raise HTTPException(400, "Conversation is closed")
    message = CustomerConversationMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        content=data.content.strip(),
    )
    db.add(message)
    conversation.updated_at = func.now()
    _commit(db, "Unable to send message")
    db.refresh(message)
    return message


def _admin_conversation(db: Session, company_id: UUID, conversation_id: UUID):
    conversation = db.query(CustomerConversation).filter(
        CustomerConversation.id == conversation_id,
        CustomerConversation.company_id == company_id,
    ).first()
    if not conversation:
        raise HTTPException(404, "Conversation not found")
    return conversation


@admin_router.get(
    "/admin/companies/{company_id}/customer-conversations",
    response_model=list[CustomerConversationResponse],
)
def list_admin_conversations(
    company_id: UUID,
    conversation_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    _company_or_404(db, company_id)
    query = db.query(CustomerConversation).filter(
        CustomerConversation.company_id == company_id
    )
    if conversation_status:
        if conversation_status not in {"open", "closed"}:
            raise HTTPException(400, "Invalid conversation status")
        query = query.filter(CustomerConversation.status == conversation_status)
    return query.order_by(CustomerConversation.updated_at.desc()).all()


@admin_router.get(
    "/admin/companies/{company_id}/customer-conversations/{conversation_id}/messages",
    response_model=list[CustomerMessageResponse],
)
def list_admin_messages(
    company_id: UUID,
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    return _admin_conversation(db, company_id, conversation_id).messages


@admin_router.post(
    "/admin/companies/{company_id}/customer-conversations/{conversation_id}/messages",
    response_model=CustomerMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_admin_message(
    company_id: UUID,
    conversation_id: UUID,
    data: AdminMessageCreate,
    db: Session = Depends(get_db),
):
    conversation = _admin_conversation(db, company_id, conversation_id)
    if conversation.status == "closed":
        raise HTTPException(400, "Conversation is closed")
    message = CustomerConversationMessage(
        conversation_id=conversation.id,
        sender_type="admin",
        content=data.content.strip(),
    )
    db.add(message)
    conversation.updated_at = func.now()
    _commit(db, "Unable to send message")
    db.refresh(message)
    return message


@admin_router.patch(
    "/admin/companies/{company_id}/customer-conversations/{conversation_id}",
    response_model=CustomerConversationResponse,
)
def update_conversation_status(
    company_id: UUID,
    conversation_id: UUID,
    data: ConversationStatusUpdate,
    db: Session = Depends(get_db),
):
    conversation = _admin_conversation(db, company_id, conversation_id)
    conversation.status = data.status
    _commit(db, "Unable to update conversation")
    db.refresh(conversation)
    return conversation

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.chat import (
    ChatMessage,
    ChatSession,
)
from backend.app.models.company import Company
from backend.app.models.service import Service
from backend.app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from backend.app.services.ai_service import run_ai_agent

router = APIRouter(
    prefix="/companies/{company_id}/chat",
    tags=["AI Chat"],
)

TITLE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "can",
    "could",
    "for",
    "i",
    "is",
    "me",
    "my",
    "of",
    "on",
    "please",
    "the",
    "to",
    "want",
    "with",
    "you",
}
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def _derive_chat_title(
    content: str,
    services: list[Service],
) -> str:
    normalized = content.lower()
    service_name = next(
        (
            service.name
            for service in services
            if service.name.lower() in normalized
        ),
        None,
    )

    if any(word in normalized for word in ("cancel", "cancellation")):
        return "Cancel appointment"

    if any(word in normalized for word in ("available", "availability")):
        return (
            f"{service_name} availability"
            if service_name
            else "Appointment availability"
        )

    if any(word in normalized for word in ("book", "booking", "appointment")):
        weekday = next(
            (
                day
                for day in WEEKDAYS
                if day.lower() in normalized
            ),
            None,
        )
        if weekday:
            return f"{weekday} booking request"
        if service_name:
            return f"{service_name} booking"

    if service_name:
        return f"{service_name} information"

    words = [
        word
        for word in re.findall(r"[A-Za-z0-9']+", content)
        if word.lower() not in TITLE_STOP_WORDS
    ][:6]
    if len(words) < 2:
        words.append("conversation")
    return " ".join(words).strip().title()


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    company_id: UUID,
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db),
):
    company = (
        db.query(Company.id)
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    session_query = db.query(ChatSession).filter(
        ChatSession.company_id == company_id,
    )
    if session_data.external_user_id:
        session_query = session_query.filter(
            ChatSession.external_user_id
            == session_data.external_user_id,
        )
    else:
        session_query = session_query.filter(
            ChatSession.external_user_id.is_(None),
        )

    default_title = f"Conversation {session_query.count() + 1}"
    chat_session = ChatSession(
        company_id=company_id,
        external_user_id=session_data.external_user_id,
        title=session_data.title or default_title,
    )

    db.add(chat_session)
    try:
        db.commit()
        db.refresh(chat_session)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create chat session",
        )

    return chat_session


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
def rename_chat_session(
    company_id: UUID,
    session_id: UUID,
    session_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
):
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.company_id == company_id,
        )
        .first()
    )
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    chat_session.title = session_data.title.strip()
    try:
        db.commit()
        db.refresh(chat_session)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to rename chat session",
        )
    return chat_session


@router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
)
def get_chat_sessions(
    company_id: UUID,
    external_user_id: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ChatSession).filter(
        ChatSession.company_id == company_id,
        ChatSession.is_archived.is_(False),
    )

    if external_user_id:
        query = query.filter(
            ChatSession.external_user_id
            == external_user_id,
        )

    return (
        query.order_by(
            ChatSession.created_at.desc(),
        )
        .all()
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_chat_messages(
    company_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
):
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.company_id == company_id,
        )
        .first()
    )

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
        )
        .order_by(ChatMessage.created_at)
        .all()
    )

@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def archive_chat_session(
    company_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
):
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.company_id == company_id,
        )
        .first()
    )

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    chat_session.is_archived = True

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to archive chat session",
        )

@router.post(
    "/sessions/{session_id}/messages",
)
def send_chat_message(
    company_id: UUID,
    session_id: UUID,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
):
    chat_session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.company_id == company_id,
        )
        .first()
    )

    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    first_user_message = (
        db.query(ChatMessage.id)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user",
        )
        .first()
        is None
    )
    if (
        first_user_message
        and (
            not chat_session.title
            or chat_session.title.startswith("Conversation ")
        )
    ):
        services = (
            db.query(Service)
            .filter(
                Service.company_id == company_id,
                Service.is_active.is_(True),
            )
            .all()
        )
        chat_session.title = _derive_chat_title(
            message_data.content,
            services,
        )

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
    )

    db.add(user_message)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to save chat message",
        )

    previous_messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
        )
        .order_by(ChatMessage.created_at)
        .all()
    )

    messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in previous_messages
    ]

    ai_response = run_ai_agent(
        db=db,
        company_id=company_id,
        messages=messages,
        external_user_id=chat_session.external_user_id,
        customer_context={
            "customer_name": message_data.customer_name,
            "customer_email": message_data.customer_email,
            "customer_phone": message_data.customer_phone,
        },
        chat_session=chat_session,
    )

    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response["message"],
    )

    db.add(assistant_message)
    try:
        db.commit()
        db.refresh(assistant_message)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to save AI response",
        )

    return {
        "message": assistant_message,
    }

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.chat import (
    ChatMessage,
    ChatSession,
)
from backend.app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from backend.app.services.ai_service import run_ai_agent

router = APIRouter(
    prefix="/companies/{company_id}/chat",
    tags=["AI Chat"],
)


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
    chat_session = ChatSession(
        company_id=company_id,
        external_user_id=session_data.external_user_id,
        title=session_data.title,
    )

    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

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

    db.commit()

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

    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
    )

    db.add(user_message)
    db.commit()

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
    )

    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response["message"],
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return {
        "message": assistant_message,
    }
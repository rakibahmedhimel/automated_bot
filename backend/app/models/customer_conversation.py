import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class CustomerConversation(Base):
    __tablename__ = "customer_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    external_user_id = Column(String, nullable=True, index=True)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True, index=True)
    appointment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id"),
        nullable=True,
    )
    schedule_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedule_requests.id"),
        nullable=True,
    )
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open", index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages = relationship(
        "CustomerConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="CustomerConversationMessage.created_at",
    )

    @property
    def latest_message(self):
        return self.messages[-1].content if self.messages else None


class CustomerConversationMessage(Base):
    __tablename__ = "customer_conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    read_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship(
        "CustomerConversation",
        back_populates="messages",
    )

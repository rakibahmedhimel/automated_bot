import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from backend.app.core.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )

    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
        index=True,
    )

    appointment_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    start_time = Column(
        Time,
        nullable=False,
    )

    end_time = Column(
        Time,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="confirmed",
        index=True,
    )

    external_user_id = Column(
        String,
        nullable=True,
        index=True,
    )

    customer_name = Column(
        String,
        nullable=True,
    )

    customer_email = Column(
        String,
        nullable=True,
    )

    customer_phone = Column(
        String,
        nullable=True,
    )

    cancellation_reason = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import Clinic, User
    from app.models.patient import Patient


class ConversationType(StrEnum):
    PATIENT_CLINIC = "PATIENT_CLINIC"
    PATIENT_DENTIST = "PATIENT_DENTIST"
    STAFF_INTERNAL = "STAFF_INTERNAL"


class Conversation(Base, UUIDAuditMixin):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_clinic_id", "clinic_id"),
        Index("ix_conversations_patient_id", "patient_id"),
    )

    clinic_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    conversation_type: Mapped[ConversationType] = mapped_column(
        Enum(ConversationType, name="conversation_type"),
        default=ConversationType.PATIENT_CLINIC,
        nullable=False,
    )
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    clinic: Mapped[Clinic] = relationship("Clinic")
    patient: Mapped[Patient | None] = relationship("Patient")
    participants: Mapped[list[ConversationParticipant]] = relationship(
        "ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class ConversationParticipant(Base, UUIDAuditMixin):
    __tablename__ = "conversation_participants"
    __table_args__ = (
        Index("ix_conv_part_conversation_id", "conversation_id"),
        Index("ix_conv_part_user_id", "user_id"),
        Index("ix_conv_part_patient_id", "patient_id"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=True
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="participants")
    user: Mapped[User | None] = relationship("User")
    patient: Mapped[Patient | None] = relationship("Patient")


class Message(Base, UUIDAuditMixin):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
        Index("ix_messages_created_at", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sender_patient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str | None] = mapped_column(Text)
    attachments_json: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
    sender_user: Mapped[User | None] = relationship("User", foreign_keys=[sender_user_id])
    sender_patient: Mapped[Patient | None] = relationship("Patient", foreign_keys=[sender_patient_id])

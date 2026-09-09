from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.communication import ConversationType


class MessageAttachment(BaseModel):
    name: str
    url: str
    size: int | None = None
    mime_type: str | None = None


class MessageCreate(BaseModel):
    content: str | None = None
    attachments: list[MessageAttachment] | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_user_id: UUID | None = None
    sender_patient_id: UUID | None = None
    sender_name: str | None = None
    content: str | None = None
    attachments_json: str | None = None
    is_read: bool
    created_at: datetime


class ConversationParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    user_id: UUID | None = None
    patient_id: UUID | None = None
    participant_name: str | None = None
    last_read_at: datetime | None = None
    is_muted: bool


class ConversationCreate(BaseModel):
    title: str = Field(..., max_length=200)
    conversation_type: ConversationType = ConversationType.PATIENT_CLINIC
    patient_id: UUID | None = None
    participant_user_ids: list[UUID] = Field(default_factory=list)
    initial_message: str | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    title: str
    conversation_type: ConversationType
    patient_id: UUID | None = None
    patient_name: str | None = None
    status: str
    last_message_at: datetime | None = None
    unread_count: int = 0
    created_at: datetime


class ConversationDetail(ConversationRead):
    participants: list[ConversationParticipantRead] = Field(default_factory=list)
    messages: list[MessageRead] = Field(default_factory=list)


class MessageStatusUpdate(BaseModel):
    is_read: bool = True


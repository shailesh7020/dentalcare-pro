from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.communication import (
    Conversation,
    ConversationParticipant,
    Message,
)
from app.schemas.communication import ConversationCreate, MessageCreate


class CommunicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------
    # Conversations
    # ----------------------------------------------------
    async def create_conversation(
        self, clinic_id: UUID, payload: ConversationCreate, actor_id: UUID | None = None
    ) -> Conversation:
        conv = Conversation(
            id=uuid4(),
            clinic_id=clinic_id,
            title=payload.title,
            conversation_type=payload.conversation_type,
            patient_id=payload.patient_id,
            status="ACTIVE",
            last_message_at=datetime.now(UTC),
            created_by=actor_id,
        )
        self.db.add(conv)
        await self.db.flush()

        # Add participant users
        for uid in payload.participant_user_ids:
            part = ConversationParticipant(
                id=uuid4(),
                conversation_id=conv.id,
                user_id=uid,
                patient_id=None,
            )
            self.db.add(part)

        # Add patient participant if linked
        if payload.patient_id:
            part_pat = ConversationParticipant(
                id=uuid4(),
                conversation_id=conv.id,
                user_id=None,
                patient_id=payload.patient_id,
            )
            self.db.add(part_pat)

        # Initial message if provided
        if payload.initial_message:
            msg = Message(
                id=uuid4(),
                conversation_id=conv.id,
                sender_user_id=actor_id,
                content=payload.initial_message,
                is_read=False,
            )
            self.db.add(msg)

        await self.db.flush()
        return conv

    async def get_conversation(self, clinic_id: UUID, conversation_id: UUID) -> Conversation | None:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
                selectinload(Conversation.participants).selectinload(ConversationParticipant.patient),
                selectinload(Conversation.messages).selectinload(Message.sender_user),
                selectinload(Conversation.messages).selectinload(Message.sender_patient),
                selectinload(Conversation.patient),
            )
            .where(
                Conversation.id == conversation_id,
                Conversation.clinic_id == clinic_id,
                Conversation.deleted_at.is_(None),
            )
        )
        return await self.db.scalar(stmt)

    async def list_conversations(
        self,
        clinic_id: UUID,
        user_id: UUID | None = None,
        patient_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.participants),
                selectinload(Conversation.patient),
            )
            .where(
                Conversation.clinic_id == clinic_id,
                Conversation.deleted_at.is_(None),
            )
        )

        if user_id:
            stmt = stmt.join(Conversation.participants).where(ConversationParticipant.user_id == user_id)
        elif patient_id:
            stmt = stmt.where(Conversation.patient_id == patient_id)

        stmt = stmt.order_by(Conversation.last_message_at.desc().nullslast()).offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ----------------------------------------------------
    # Messages
    # ----------------------------------------------------
    async def create_message(
        self,
        conversation_id: UUID,
        payload: MessageCreate,
        sender_user_id: UUID | None = None,
        sender_patient_id: UUID | None = None,
    ) -> Message:
        attachments_str = (
            json.dumps([a.model_dump() for a in payload.attachments]) if payload.attachments else None
        )
        msg = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            sender_user_id=sender_user_id,
            sender_patient_id=sender_patient_id,
            content=payload.content,
            attachments_json=attachments_str,
            is_read=False,
        )
        self.db.add(msg)

        # Update last_message_at on conversation
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(last_message_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        await self.db.flush()
        return msg

    async def list_messages(
        self, conversation_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Message]:
        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender_user),
                selectinload(Message.sender_patient),
            )
            .where(
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
            )
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def mark_messages_read(
        self, conversation_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> int:
        stmt = (
            update(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_read.is_(False),
                Message.deleted_at.is_(None),
            )
            .values(is_read=True, updated_at=datetime.now(UTC))
        )
        if user_id:
            # mark messages not sent by this user
            stmt = stmt.where(Message.sender_user_id != user_id)
        elif patient_id:
            # mark messages not sent by this patient
            stmt = stmt.where(Message.sender_patient_id != patient_id)

        res = await self.db.execute(stmt)
        await self.db.flush()
        return getattr(res, "rowcount", 1) or 0

    async def get_unread_count(
        self, conversation_id: UUID, user_id: UUID | None = None, patient_id: UUID | None = None
    ) -> int:
        stmt = (
            select(func.count(Message.id))
            .where(
                Message.conversation_id == conversation_id,
                Message.is_read.is_(False),
                Message.deleted_at.is_(None),
            )
        )
        if user_id:
            stmt = stmt.where(Message.sender_user_id != user_id)
        elif patient_id:
            stmt = stmt.where(Message.sender_patient_id != patient_id)
        return (await self.db.scalar(stmt)) or 0


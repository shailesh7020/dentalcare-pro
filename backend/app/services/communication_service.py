from __future__ import annotations

import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import (
    ConversationType,
    Message,
)
from app.models.identity import Role, User
from app.models.notification import DeliveryChannel, NotificationPriority, NotificationType
from app.models.patient import Patient
from app.repositories.communication_repository import CommunicationRepository
from app.schemas.communication import (
    ConversationCreate,
    ConversationDetail,
    ConversationParticipantRead,
    ConversationRead,
    MessageCreate,
    MessageRead,
    MessageStatusUpdate,
)
from app.schemas.notification import NotificationCreate
from app.services.notifications.notification_service import NotificationService


class CommunicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CommunicationRepository(db)
        self.notif_service = NotificationService(db)

    async def create_patient_clinic_thread(
        self, clinic_id: UUID, patient_id: UUID, actor: User, title: str | None = None
    ) -> ConversationDetail:
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        conv_title = title or f"Patient Care: {patient.first_name} {patient.last_name}"
        conv = await self.repo.create_conversation(
            clinic_id,
            ConversationCreate(
                title=conv_title,
                conversation_type=ConversationType.PATIENT_CLINIC,
                patient_id=patient_id,
                participant_user_ids=[actor.id] if actor.role != Role.PATIENT else [],
            ),
            actor_id=actor.id if actor.role != Role.PATIENT else None,
        )
        await self.db.commit()
        return await self.get_conversation(clinic_id, conv.id, actor)

    async def create_conversation(
        self,
        clinic_id: UUID,
        arg1: ConversationCreate | User,
        arg2: User | ConversationCreate,
    ) -> ConversationDetail:
        if isinstance(arg1, User):
            actor = arg1
            payload = arg2
        else:
            payload = arg1
            actor = arg2

        actor_id = actor.id if actor.role != Role.PATIENT else None
        conv = await self.repo.create_conversation(clinic_id, payload, actor_id=actor_id)
        await self.db.commit()
        return await self.get_conversation(clinic_id, conv.id, actor)

    async def get_conversation(
        self, clinic_id: UUID, arg1: UUID | User, arg2: User | UUID
    ) -> ConversationDetail:
        conversation_id = arg1 if isinstance(arg1, UUID) else arg2
        actor = arg2 if isinstance(arg1, UUID) else arg1

        conv = await self.repo.get_conversation(clinic_id, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        # Authorization check
        if actor.role == Role.PATIENT and conv.patient_id != actor.patient_id:
            raise HTTPException(status_code=403, detail="Unauthorized conversation access.")

        parts_read = []
        for p in getattr(conv, "participants", []):
            name = "Participant"
            if getattr(p, "user", None):
                name = f"{p.user.first_name} {p.user.last_name}"
            elif getattr(p, "patient", None):
                name = f"{p.patient.first_name} {p.patient.last_name}"
            parts_read.append(
                ConversationParticipantRead(
                    id=p.id,
                    conversation_id=p.conversation_id,
                    user_id=p.user_id,
                    patient_id=p.patient_id,
                    participant_name=name,
                    last_read_at=p.last_read_at,
                    is_muted=p.is_muted,
                )
            )

        msgs_read = []
        for m in getattr(conv, "messages", []):
            sname = "Sender"
            if getattr(m, "sender_user", None):
                sname = f"{m.sender_user.first_name} {m.sender_user.last_name}"
            elif getattr(m, "sender_patient", None):
                sname = f"{m.sender_patient.first_name} {m.sender_patient.last_name}"
            msgs_read.append(
                MessageRead(
                    id=m.id,
                    conversation_id=m.conversation_id,
                    sender_user_id=m.sender_user_id,
                    sender_patient_id=m.sender_patient_id,
                    sender_name=sname,
                    content=m.content,
                    attachments_json=m.attachments_json,
                    is_read=m.is_read,
                    created_at=m.created_at,
                )
            )

        # Count unread messages
        is_patient = actor.role == Role.PATIENT
        unread_count = await self.repo.get_unread_count(
            conversation_id,
            user_id=None if is_patient else actor.id,
            patient_id=actor.patient_id if is_patient else None,
        )

        pat_name = None
        if getattr(conv, "patient", None):
            pat_name = f"{conv.patient.first_name} {conv.patient.last_name}"

        return ConversationDetail(
            id=conv.id,
            clinic_id=conv.clinic_id,
            title=conv.title,
            conversation_type=conv.conversation_type,
            patient_id=conv.patient_id,
            patient_name=pat_name,
            status=conv.status,
            last_message_at=conv.last_message_at,
            unread_count=unread_count,
            created_at=conv.created_at,
            participants=parts_read,
            messages=msgs_read,
        )

    async def get_conversation_detail(
        self, clinic_id: UUID, arg1: UUID | User, arg2: User | UUID
    ) -> ConversationDetail:
        return await self.get_conversation(clinic_id, arg1, arg2)

    async def list_conversations(
        self,
        clinic_id: UUID,
        actor: User,
        conv_type: ConversationType | None = None,
        patient_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
        skip: int = 0,
    ) -> list[ConversationRead]:
        real_skip = offset if offset else skip
        target_patient = actor.patient_id if actor.role == Role.PATIENT else patient_id

        convs = await self.repo.list_conversations(
            clinic_id,
            patient_id=target_patient,
            conversation_type=conv_type,
            skip=real_skip,
            limit=limit,
        )

        results: list[ConversationRead] = []
        for c in convs:
            pat_name = None
            if getattr(c, "patient", None):
                pat_name = f"{c.patient.first_name} {c.patient.last_name}"
            results.append(
                ConversationRead(
                    id=c.id,
                    clinic_id=c.clinic_id,
                    title=c.title,
                    conversation_type=c.conversation_type,
                    patient_id=c.patient_id,
                    patient_name=pat_name,
                    status=c.status,
                    last_message_at=c.last_message_at,
                    created_at=c.created_at,
                )
            )
        return results

    async def get_messages(
        self,
        clinic_id: UUID,
        actor: User,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MessageRead]:
        await self.get_conversation(clinic_id, conversation_id, actor)
        msgs = await self.repo.list_messages(conversation_id, skip=offset, limit=limit)
        return [
            MessageRead(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_user_id=m.sender_user_id,
                sender_patient_id=m.sender_patient_id,
                sender_name=(
                    f"{m.sender_user.first_name} {m.sender_user.last_name}"
                    if getattr(m, "sender_user", None)
                    else f"{m.sender_patient.first_name} {m.sender_patient.last_name}"
                    if getattr(m, "sender_patient", None)
                    else None
                ),
                content=m.content,
                attachments_json=m.attachments_json,
                is_read=m.is_read,
                created_at=m.created_at,
            )
            for m in msgs
        ]

    async def send_message(
        self,
        clinic_id: UUID,
        arg1: User | UUID,
        arg2: UUID | User | MessageCreate,
        arg3: MessageCreate | User | None = None,
    ) -> MessageRead:
        if isinstance(arg1, User):
            actor = arg1
            conversation_id = arg2
            payload = arg3
        elif isinstance(arg2, User):
            conversation_id = arg1
            actor = arg2
            payload = arg3
        else:
            conversation_id = arg1
            payload = arg2
            actor = arg3

        conv = await self.repo.get_conversation(clinic_id, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        is_patient = actor.role == Role.PATIENT
        sender_user_id = None if is_patient else actor.id
        sender_patient_id = actor.patient_id if is_patient else None

        msg = await self.repo.create_message(
            conversation_id,
            payload,
            sender_user_id=sender_user_id,
            sender_patient_id=sender_patient_id,
        )

        sender_name = f"{actor.first_name} {actor.last_name}"
        if is_patient:
            staff_parts = [p.user_id for p in getattr(conv, "participants", []) if p.user_id]
            for suid in staff_parts:
                notif_payload = NotificationCreate(
                    notification_type=NotificationType.SYSTEM_ALERT,
                    priority=NotificationPriority.NORMAL,
                    delivery_channel=DeliveryChannel.IN_APP,
                    recipient_user_id=suid,
                    title=f"New message from patient: {actor.first_name} {actor.last_name}",
                    message=payload.content or "Sent an attachment.",
                    data_json=json.dumps({"conversation_id": str(conversation_id)}),
                )
                await self.notif_service.send_notification(clinic_id, notif_payload, actor=actor)
        else:
            if conv.patient_id:
                notif_payload = NotificationCreate(
                    notification_type=NotificationType.SYSTEM_ALERT,
                    priority=NotificationPriority.NORMAL,
                    delivery_channel=DeliveryChannel.IN_APP,
                    patient_id=conv.patient_id,
                    title=f"Message from {actor.first_name} ({getattr(conv.clinic, 'name', 'Clinic') if getattr(conv, 'clinic', None) else 'Clinic'})",
                    message=payload.content or "Sent an attachment.",
                    data_json=json.dumps({"conversation_id": str(conversation_id)}),
                )
                await self.notif_service.send_notification(clinic_id, notif_payload, actor=actor)

        await self.db.commit()

        return MessageRead(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_user_id=msg.sender_user_id,
            sender_patient_id=msg.sender_patient_id,
            sender_name=sender_name,
            content=msg.content,
            attachments_json=msg.attachments_json,
            is_read=msg.is_read,
            created_at=msg.created_at,
        )

    async def mark_read(self, clinic_id: UUID, conversation_id: UUID, actor: User) -> int:
        is_patient = actor.role == Role.PATIENT
        user_id = None if is_patient else actor.id
        patient_id = actor.patient_id if is_patient else None
        count = await self.repo.mark_messages_read(
            conversation_id, user_id=user_id, patient_id=patient_id
        )
        await self.db.commit()
        return count

    async def mark_conversation_read(self, clinic_id: UUID, arg1: User | UUID, arg2: UUID | User) -> int:
        actor = arg1 if isinstance(arg1, User) else arg2
        conversation_id = arg2 if isinstance(arg1, User) else arg1
        return await self.mark_read(clinic_id, conversation_id, actor)

    async def update_message_status(
        self, clinic_id: UUID, message_id: UUID, payload: MessageStatusUpdate
    ) -> MessageRead:
        msg = await self.db.get(Message, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found.")
        msg.is_read = payload.is_read
        await self.db.commit()
        return MessageRead(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_user_id=msg.sender_user_id,
            sender_patient_id=msg.sender_patient_id,
            sender_name=None,
            content=msg.content,
            attachments_json=msg.attachments_json,
            is_read=msg.is_read,
            created_at=msg.created_at,
        )

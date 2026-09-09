from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.models.communication import ConversationType
from app.models.identity import User
from app.schemas.communication import (
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    MessageCreate,
    MessageRead,
    MessageStatusUpdate,
)
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/communications", tags=["Communications & Messaging"])


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    conversation_type: ConversationType | None = Query(default=None),
    patient_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.list_conversations(
        clinic_id=actor.clinic_id,
        actor=actor,
        conv_type=conversation_type,
        patient_id=patient_id,
        limit=limit,
        offset=offset,
    )


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.create_conversation(actor.clinic_id, actor, payload)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.get_conversation_detail(actor.clinic_id, actor, conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: UUID,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.get_messages(actor.clinic_id, actor, conversation_id, limit=limit, offset=offset)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.send_message(actor.clinic_id, actor, conversation_id, payload)


@router.post("/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(
    conversation_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    if not actor.clinic_id:
        return {"read": 0}
    service = CommunicationService(db)
    count = await service.mark_conversation_read(actor.clinic_id, actor, conversation_id)
    return {"read": count}


@router.patch("/messages/{message_id}/status", response_model=MessageRead)
async def update_message_status(
    message_id: UUID,
    payload: MessageStatusUpdate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = CommunicationService(db)
    return await service.update_message_status(actor.clinic_id, message_id, payload)

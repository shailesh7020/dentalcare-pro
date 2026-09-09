import json
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditEvent, User
from app.repositories.chair_repository import ChairRepository
from app.schemas.appointment import ChairCreate, ChairRead, ChairUpdate


class ChairService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ChairRepository(db)

    async def create(self, clinic_id: UUID, payload: ChairCreate, actor: User) -> ChairRead:
        existing = await self.repo.get_by_name(clinic_id, payload.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Chair with name '{payload.name}' already exists in this clinic",
            )
        chair = await self.repo.create(clinic_id, payload)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="CHAIR",
                entity_id=str(chair.id),
                metadata_json=json.dumps({"name": chair.name, "room_number": chair.room_number}),
            )
        )
        await self.db.commit()
        await self.db.refresh(chair)
        return ChairRead.model_validate(chair)

    async def get(self, clinic_id: UUID, chair_id: UUID) -> ChairRead:
        chair = await self.repo.get(clinic_id, chair_id)
        if not chair:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chair not found in current clinic",
            )
        return ChairRead.model_validate(chair)

    async def list(self, clinic_id: UUID, include_inactive: bool = False) -> list[ChairRead]:
        chairs = await self.repo.list(clinic_id, include_inactive)
        return [ChairRead.model_validate(chair) for chair in chairs]

    async def update(
        self, clinic_id: UUID, chair_id: UUID, payload: ChairUpdate, actor: User
    ) -> ChairRead:
        chair = await self.repo.get(clinic_id, chair_id)
        if not chair:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chair not found in current clinic",
            )
        if payload.name and payload.name != chair.name:
            existing = await self.repo.get_by_name(clinic_id, payload.name)
            if existing and existing.id != chair_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Chair with name '{payload.name}' already exists in this clinic",
                )
        updated = await self.repo.update(chair, payload)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="CHAIR",
                entity_id=str(chair.id),
                metadata_json=json.dumps(payload.model_dump(exclude_unset=True)),
            )
        )
        await self.db.commit()
        await self.db.refresh(updated)
        return ChairRead.model_validate(updated)

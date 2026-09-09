from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Chair
from app.schemas.appointment import ChairCreate, ChairUpdate


class ChairRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, clinic_id: UUID, payload: ChairCreate) -> Chair:
        chair = Chair(
            id=uuid4(),
            clinic_id=clinic_id,
            name=payload.name,
            room_number=payload.room_number,
            status=payload.status,
            is_active=True,
            notes=payload.notes,
        )
        self.db.add(chair)
        await self.db.flush()
        return chair

    async def get(self, clinic_id: UUID, chair_id: UUID) -> Chair | None:
        query = select(Chair).where(
            Chair.clinic_id == clinic_id,
            Chair.id == chair_id,
            Chair.deleted_at.is_(None),
        )
        return await self.db.scalar(query)

    async def get_by_name(self, clinic_id: UUID, name: str) -> Chair | None:
        query = select(Chair).where(
            Chair.clinic_id == clinic_id,
            Chair.name == name,
            Chair.deleted_at.is_(None),
        )
        return await self.db.scalar(query)

    async def list(self, clinic_id: UUID, include_inactive: bool = False) -> list[Chair]:
        query = select(Chair).where(
            Chair.clinic_id == clinic_id,
            Chair.deleted_at.is_(None),
        )
        if not include_inactive:
            query = query.where(Chair.is_active.is_(True))
        query = query.order_by(Chair.name.asc())
        return list((await self.db.scalars(query)).all())

    async def update(self, chair: Chair, payload: ChairUpdate) -> Chair:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(chair, field, value)
        await self.db.flush()
        return chair

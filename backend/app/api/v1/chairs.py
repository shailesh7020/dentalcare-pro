from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.appointment import ChairCreate, ChairRead, ChairScheduleRead, ChairUpdate
from app.services.appointment_service import AppointmentService
from app.services.chair_service import ChairService

router = APIRouter(prefix="/chairs", tags=["Chairs"])


@router.get(
    "",
    response_model=list[ChairRead],
    summary="List dental chairs",
    description="Returns all dental operatories/chairs in the authenticated user's clinic.",
)
async def list_chairs(
    include_inactive: bool = Query(False),
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST, Role.RECEPTIONIST, Role.ASSISTANT)),
    db: AsyncSession = Depends(get_db),
) -> list[ChairRead]:
    service = ChairService(db)
    return await service.list(actor.clinic_id, include_inactive)  # type: ignore


@router.post(
    "",
    response_model=ChairRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create dental chair",
    description="Registers a new dental chair/operatory in the clinic.",
)
async def create_chair(
    payload: ChairCreate,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ChairRead:
    service = ChairService(db)
    return await service.create(actor.clinic_id, payload, actor)  # type: ignore


@router.get(
    "/{id}",
    response_model=ChairRead,
    summary="Get chair details",
)
async def get_chair(
    id: UUID,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST, Role.RECEPTIONIST, Role.ASSISTANT)),
    db: AsyncSession = Depends(get_db),
) -> ChairRead:
    service = ChairService(db)
    return await service.get(actor.clinic_id, id)  # type: ignore


@router.patch(
    "/{id}",
    response_model=ChairRead,
    summary="Update dental chair",
)
async def update_chair(
    id: UUID,
    payload: ChairUpdate,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ChairRead:
    service = ChairService(db)
    return await service.update(actor.clinic_id, id, payload, actor)  # type: ignore


@router.get(
    "/{id}/schedule",
    response_model=ChairScheduleRead,
    summary="Get chair schedule",
    description="Returns appointments scheduled on this chair for a specific date or date range.",
)
async def get_chair_schedule(
    id: UUID,
    target_date: date | None = Query(None, alias="date"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST, Role.RECEPTIONIST, Role.ASSISTANT)),
    db: AsyncSession = Depends(get_db),
) -> ChairScheduleRead:
    chair_service = ChairService(db)
    apt_service = AppointmentService(db)
    chair = await chair_service.get(actor.clinic_id, id)  # type: ignore

    s_date = start_date or target_date or datetime.now(UTC).date()
    e_date = end_date or target_date or s_date

    appointments = await apt_service.list(
        clinic_id=actor.clinic_id,  # type: ignore
        chair_id=id,
        start_date=s_date,
        end_date=e_date,
    )
    return ChairScheduleRead(chair=chair, appointments=appointments)

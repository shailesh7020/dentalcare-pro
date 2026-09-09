from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.appointment import DentistScheduleRead
from app.schemas.auth import UserRead
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/dentists", tags=["Dentists"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List clinic dentists",
    description="Returns all active dentists assigned to the authenticated user's clinic.",
)
async def list_dentists(
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    query = (
        select(User)
        .where(
            User.clinic_id == actor.clinic_id,
            User.role == Role.DENTIST,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        .order_by(User.first_name.asc(), User.last_name.asc())
    )
    result = await db.scalars(query)
    return list(result.all())


@router.get(
    "/{id}/schedule",
    response_model=DentistScheduleRead,
    summary="Get dentist schedule and availability",
    description="Returns dentist working hours and blocked times within the requested window.",
)
async def get_dentist_schedule(
    id: UUID,
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> DentistScheduleRead:
    service = AppointmentService(db)
    s_date = start_date if isinstance(start_date, date) else datetime.now(UTC).date()
    e_date = end_date if isinstance(end_date, date) else (s_date + timedelta(days=7))
    return await service.get_dentist_schedule(actor.clinic_id, id, s_date, e_date)  # type: ignore

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.appointment import (
    CalendarDayResponse,
    CalendarMonthResponse,
    CalendarWeekResponse,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get(
    "/day",
    response_model=CalendarDayResponse,
    summary="Get day calendar",
    description="Returns all chairs and appointments for a specific day in the clinic.",
)
async def get_day_calendar(
    target_date: date | None = Query(None, alias="date"),
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
) -> CalendarDayResponse:
    service = AppointmentService(db)
    day = target_date or datetime.now(UTC).date()
    return await service.get_day_calendar(actor.clinic_id, day)  # type: ignore


@router.get(
    "/week",
    response_model=CalendarWeekResponse,
    summary="Get week calendar",
    description="Returns appointments for a 7-day period starting on the given date.",
)
async def get_week_calendar(
    start_date: date | None = Query(None),
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
) -> CalendarWeekResponse:
    service = AppointmentService(db)
    today = datetime.now(UTC).date()
    s_date = start_date or (today - timedelta(days=today.weekday()))  # default to Monday
    e_date = s_date + timedelta(days=6)
    return await service.get_week_calendar(actor.clinic_id, s_date, e_date)  # type: ignore


@router.get(
    "/month",
    response_model=CalendarMonthResponse,
    summary="Get month calendar",
    description="Returns all appointments for the specified year and month.",
)
async def get_month_calendar(
    year: int | None = Query(None),
    month: int | None = Query(None),
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
) -> CalendarMonthResponse:
    service = AppointmentService(db)
    now = datetime.now(UTC).date()
    y = year or now.year
    m = month or now.month
    return await service.get_month_calendar(actor.clinic_id, y, m)  # type: ignore

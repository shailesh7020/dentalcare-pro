from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.appointment import AppointmentStatus, VisitType
from app.models.identity import Role, User
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentDetail,
    AppointmentQueueItem,
    AppointmentRead,
    AppointmentReschedule,
    AppointmentUpdate,
    DashboardStatsResponse,
)
from app.schemas.treatment import TreatmentDetail
from app.services.appointment_service import AppointmentService
from app.services.treatment_service import TreatmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "",
    response_model=AppointmentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create appointment",
    description="Schedules a new dental appointment with dentist, chair, and patient availability verification.",
)
async def create_appointment(
    payload: AppointmentCreate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required"
        )
    service = AppointmentService(db)
    return await service.create(actor.clinic_id, payload, actor)


@router.get(
    "",
    response_model=list[AppointmentRead],
    summary="List appointments",
    description="Lists appointments with multi-field search, date range, status, chair, and dentist filters.",
)
async def list_appointments(
    patient_id: UUID | None = Query(None),
    dentist_id: UUID | None = Query(None),
    chair_id: UUID | None = Query(None),
    target_date: date | None = Query(None, alias="date"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: AppointmentStatus | None = Query(None),
    visit_type: VisitType | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    sort_asc: bool = Query(True),
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
) -> list[AppointmentRead]:
    service = AppointmentService(db)
    return await service.list(
        clinic_id=actor.clinic_id,  # type: ignore
        patient_id=patient_id,
        dentist_id=dentist_id,
        chair_id=chair_id,
        target_date=target_date,
        start_date=start_date,
        end_date=end_date,
        status=status,
        visit_type=visit_type,
        search=search,
        skip=skip,
        limit=limit,
        sort_asc=sort_asc,
    )


@router.get(
    "/queue",
    response_model=list[AppointmentQueueItem],
    summary="Get reception queue",
    description="Returns categorized queue for reception: scheduled, checked in, in-treatment, and completed today.",
)
async def get_queue(
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
) -> list[AppointmentQueueItem]:
    service = AppointmentService(db)
    day = target_date or datetime.now(UTC).date()
    return await service.get_queue(actor.clinic_id, day)  # type: ignore


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Get appointment statistics",
    description="Returns aggregate appointment counters and revenue indicators for the dashboard.",
)
async def get_stats(
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
) -> DashboardStatsResponse:
    service = AppointmentService(db)
    day = target_date or datetime.now(UTC).date()
    return await service.get_stats(actor.clinic_id, day)  # type: ignore


@router.get(
    "/patient/{patient_id}",
    response_model=list[AppointmentRead],
    summary="Get patient appointments",
    description="Returns full appointment history for a given patient.",
)
async def get_patient_appointments(
    patient_id: UUID,
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
) -> list[AppointmentRead]:
    service = AppointmentService(db)
    return await service.list(
        clinic_id=actor.clinic_id,  # type: ignore
        patient_id=patient_id,
        sort_asc=False,
    )


@router.get(
    "/{id}",
    response_model=AppointmentDetail,
    summary="Get appointment details",
    description="Returns full appointment profile including patient medical alerts and timeline events.",
)
async def get_appointment(
    id: UUID,
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
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.get(actor.clinic_id, id)  # type: ignore


@router.patch(
    "/{id}",
    response_model=AppointmentDetail,
    summary="Update appointment",
    description="Updates appointment clinical notes or scheduling parameters.",
)
async def update_appointment(
    id: UUID,
    payload: AppointmentUpdate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.update(actor.clinic_id, id, payload, actor)  # type: ignore


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete appointment",
    description="Soft-deletes an appointment record.",
)
async def delete_appointment(
    id: UUID,
    actor: User = Depends(require_roles(Role.SUPER_ADMIN, Role.CLINIC_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AppointmentService(db)
    await service.delete(actor.clinic_id, id, actor)  # type: ignore


@router.post(
    "/{id}/confirm",
    response_model=AppointmentDetail,
    summary="Confirm appointment",
)
async def confirm_appointment(
    id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.confirm(actor.clinic_id, id, actor)  # type: ignore


@router.post(
    "/{id}/checkin",
    response_model=AppointmentDetail,
    summary="Check in patient",
    description="Marks patient checked in at reception and enters them into the waiting queue.",
)
async def checkin_appointment(
    id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.checkin(actor.clinic_id, id, actor)  # type: ignore


@router.post(
    "/{id}/start",
    response_model=AppointmentDetail,
    summary="Start treatment",
    description="Marks appointment in treatment and moves patient from waiting queue to active chair.",
)
async def start_treatment(
    id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.start_treatment(actor.clinic_id, id, actor)  # type: ignore


@router.post(
    "/{id}/complete",
    response_model=AppointmentDetail,
    summary="Complete appointment",
    description="Concludes treatment visit and records follow-up notifications.",
)
async def complete_appointment(
    id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.complete(actor.clinic_id, id, actor)  # type: ignore


@router.post(
    "/{id}/cancel",
    response_model=AppointmentDetail,
    summary="Cancel appointment",
    description="Cancels appointment with mandatory reason.",
)
async def cancel_appointment(
    id: UUID,
    payload: AppointmentCancel,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.cancel(actor.clinic_id, id, payload, actor)  # type: ignore


@router.post(
    "/{id}/reschedule",
    response_model=AppointmentDetail,
    summary="Reschedule appointment",
    description="Moves appointment to a new date, time, dentist, or chair with conflict checking.",
)
async def reschedule_appointment(
    id: UUID,
    payload: AppointmentReschedule,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> AppointmentDetail:
    service = AppointmentService(db)
    return await service.reschedule(actor.clinic_id, id, payload, actor)  # type: ignore


@router.get(
    "/{id}/treatment",
    response_model=TreatmentDetail | None,
    summary="Get clinical treatment for appointment",
    description="Returns the treatment record linked to this appointment, if one exists.",
)
async def get_appointment_treatment_endpoint(
    id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail | None:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required"
        )
    service = TreatmentService(db)
    return await service.get_by_appointment(actor.clinic_id, id)


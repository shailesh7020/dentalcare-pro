from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.odontogram import (
    OdontogramDashboardStats,
    PatientOdontogramRead,
    ToothConditionCreate,
    ToothDetail,
    ToothHistoryRead,
    ToothProcedureCreate,
    ToothSurfaceRead,
    ToothSurfaceUpdate,
    ToothUpdate,
)
from app.services.odontogram_service import OdontogramService

router = APIRouter(tags=["Odontogram"])


@router.get(
    "/patients/{id}/odontogram",
    response_model=PatientOdontogramRead,
    summary="Get patient odontogram",
    description="Fetches or auto-initializes the patient's dental chart with teeth, surfaces, and KPI metrics.",
)
async def get_patient_odontogram(
    id: UUID,
    dentition: str = Query("ADULT", pattern="^(ADULT|PRIMARY)$", description="Dentition type (ADULT or PRIMARY)"),
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
) -> PatientOdontogramRead:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.get_patient_odontogram(
        actor.clinic_id, id, dentition_type=dentition, user_id=actor.id
    )


@router.get(
    "/teeth/{id}",
    response_model=ToothDetail,
    summary="Get single tooth detail",
    description="Fetches detailed tooth state with independent surfaces, clinical notes, and chronological history.",
)
async def get_tooth(
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
) -> ToothDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.get_tooth(actor.clinic_id, id)


@router.patch(
    "/teeth/{id}",
    response_model=ToothDetail,
    summary="Update tooth status",
    description="Updates primary status, flags, or notes of a tooth with clinical invariant validation.",
)
async def update_tooth(
    id: UUID,
    payload: ToothUpdate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ToothDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.update_tooth(actor.clinic_id, id, payload, actor)


@router.patch(
    "/teeth/{id}/surfaces/{surface}",
    response_model=ToothSurfaceRead,
    summary="Update tooth surface",
    description="Updates condition, treatment, or color of an individual tooth surface.",
)
async def update_tooth_surface(
    id: UUID,
    surface: str,
    payload: ToothSurfaceUpdate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ToothSurfaceRead:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.update_surface(actor.clinic_id, id, surface, payload, actor)


@router.get(
    "/teeth/{id}/history",
    response_model=list[ToothHistoryRead],
    summary="Get tooth clinical history",
    description="Fetches immutable chronological audit stream of all clinical modifications to a tooth.",
)
async def get_tooth_history(
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
) -> list[ToothHistoryRead]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.get_tooth_history(actor.clinic_id, id)


@router.post(
    "/teeth/{id}/conditions",
    response_model=ToothDetail,
    summary="Record clinical condition",
    description="Records a dental diagnosis condition (e.g. Caries, Fracture) on a tooth and its surfaces.",
)
async def add_tooth_condition(
    id: UUID,
    payload: ToothConditionCreate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ToothDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.add_condition(actor.clinic_id, id, payload, actor)


@router.post(
    "/teeth/{id}/procedures",
    response_model=ToothDetail,
    summary="Chart dental procedure",
    description="Applies a restorative or clinical procedure with surface mapping directly on the tooth.",
)
async def add_tooth_procedure(
    id: UUID,
    payload: ToothProcedureCreate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ToothDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.add_procedure(actor.clinic_id, id, payload, actor)


@router.get(
    "/patients/{id}/tooth-history",
    response_model=list[ToothHistoryRead],
    summary="Get patient dental chart history",
    description="Fetches chronological audit stream of all tooth changes across the entire mouth.",
)
async def get_patient_tooth_history(
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
) -> list[ToothHistoryRead]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    return await service.get_patient_history(actor.clinic_id, id)


@router.get(
    "/odontogram/dashboard/stats",
    response_model=OdontogramDashboardStats,
    summary="Odontogram KPI metrics",
    description="Returns aggregate counts of active caries, missing teeth, root canals, crowns, implants, and restorations.",
)
async def get_odontogram_dashboard_stats(
    patient_id: UUID | None = None,
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
) -> OdontogramDashboardStats:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = OdontogramService(db)
    stats_dict = await service.repo.get_dashboard_stats(actor.clinic_id, patient_id)
    return OdontogramDashboardStats(**stats_dict)

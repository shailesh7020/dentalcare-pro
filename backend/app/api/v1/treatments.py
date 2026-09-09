from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.models.treatment import TreatmentStatus
from app.schemas.treatment import (
    TreatmentCancel,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentDashboardStats,
    TreatmentDetail,
    TreatmentRead,
    TreatmentUpdate,
)
from app.services.treatment_service import TreatmentService

router = APIRouter(prefix="/treatments", tags=["Treatments"])


@router.post(
    "",
    response_model=TreatmentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinical treatment",
    description="Creates a clinical treatment record for an appointment with procedures and SOAP notes.",
)
async def create_treatment(
    payload: TreatmentCreate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.create_treatment(actor.clinic_id, payload, actor)


@router.get(
    "/dashboard/stats",
    response_model=TreatmentDashboardStats,
    summary="Treatment dashboard metrics",
    description="Returns aggregate counts of planned, in-progress, completed treatments, and follow-ups due.",
)
async def get_treatment_dashboard_stats(
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDashboardStats:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.get_dashboard_stats(actor.clinic_id)


@router.get(
    "",
    response_model=list[TreatmentRead],
    summary="List and filter treatments",
    description="Searchable and filterable list of treatments within the authenticated clinic.",
)
async def list_treatments(
    search: str | None = Query(None, description="Search term across treatment #, patient, diagnosis"),
    status: TreatmentStatus | None = Query(None, description="Filter by status"),
    dentist_id: UUID | None = Query(None, description="Filter by clinician"),
    patient_id: UUID | None = Query(None, description="Filter by patient"),
    target_date: date | None = Query(None, description="Filter by creation date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> list[TreatmentRead]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=400, detail="Clinic context required."
        )
    # Check for direct parameter passing in unit tests
    safe_search = search if isinstance(search, str) else None
    safe_status = status if isinstance(status, TreatmentStatus) else None
    safe_dentist = dentist_id if isinstance(dentist_id, UUID) else None
    safe_patient = patient_id if isinstance(patient_id, UUID) else None
    safe_date = target_date if isinstance(target_date, date) else None

    safe_skip = skip if isinstance(skip, int) else 0
    safe_limit = limit if isinstance(limit, int) else 50

    service = TreatmentService(db)
    return await service.list_treatments(
        clinic_id=actor.clinic_id,
        search=safe_search,
        status=safe_status,
        dentist_id=safe_dentist,
        patient_id=safe_patient,
        target_date=safe_date,
        skip=safe_skip,
        limit=safe_limit,
    )


@router.get(
    "/{treatment_id}",
    response_model=TreatmentDetail,
    summary="Get treatment details",
    description="Fetches comprehensive treatment details including procedures, follow-ups, and patient alerts.",
)
async def get_treatment(
    treatment_id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.get_treatment(actor.clinic_id, treatment_id)


@router.patch(
    "/{treatment_id}",
    response_model=TreatmentDetail,
    summary="Update treatment record",
    description="Modifies clinical findings, SOAP notes, or procedures on an open treatment.",
)
async def update_treatment(
    treatment_id: UUID,
    payload: TreatmentUpdate,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.update_treatment(actor.clinic_id, treatment_id, payload, actor)


@router.post(
    "/{treatment_id}/complete",
    response_model=TreatmentDetail,
    summary="Complete treatment",
    description="Marks treatment completed, locks the record as immutable, and optionally completes linked appointment.",
)
async def complete_treatment(
    treatment_id: UUID,
    payload: TreatmentComplete,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.complete_treatment(actor.clinic_id, treatment_id, payload, actor)


@router.post(
    "/{treatment_id}/cancel",
    response_model=TreatmentDetail,
    summary="Cancel treatment",
    description="Cancels an open treatment with a mandatory clinical cancellation reason.",
)
async def cancel_treatment(
    treatment_id: UUID,
    payload: TreatmentCancel,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.cancel_treatment(actor.clinic_id, treatment_id, payload, actor)


@router.delete(
    "/{treatment_id}",
    summary="Soft-delete treatment",
    description="Soft-deletes an uncompleted treatment. Accessible only to clinic administrators.",
)
async def delete_treatment(
    treatment_id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.delete_treatment(actor.clinic_id, treatment_id, actor)


@router.get(
    "/patient/{patient_id}",
    response_model=list[TreatmentRead],
    summary="List treatments for patient",
    description="Returns all historical and ongoing treatments for a specific patient.",
)
async def list_patient_treatments(
    patient_id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> list[TreatmentRead]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.list_by_patient(actor.clinic_id, patient_id)


@router.get(
    "/appointment/{appointment_id}",
    response_model=TreatmentDetail | None,
    summary="Get treatment for appointment",
    description="Returns the clinical treatment record associated with a given appointment, if any.",
)
async def get_appointment_treatment(
    appointment_id: UUID,
    actor: User = Depends(
        require_roles(
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.ASSISTANT,
            Role.RECEPTIONIST,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> TreatmentDetail | None:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = TreatmentService(db)
    return await service.get_by_appointment(actor.clinic_id, appointment_id)

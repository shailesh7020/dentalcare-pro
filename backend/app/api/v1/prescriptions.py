from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.prescription import (
    MedicineCatalogCreate,
    MedicineCatalogRead,
    PrescriptionCancel,
    PrescriptionCreate,
    PrescriptionDashboardStats,
    PrescriptionDetail,
    PrescriptionIssue,
    PrescriptionTemplateCreate,
    PrescriptionTemplateRead,
    PrescriptionUpdate,
)
from app.services.prescription_pdf_service import PrescriptionPDFService
from app.services.prescription_service import PrescriptionService

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

CLINICAL_STAFF = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST]
ALL_STAFF = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
]


@router.post(
    "",
    response_model=PrescriptionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinical prescription",
    description="Creates a prescription for a patient encounter linked to treatment and appointment.",
)
async def create_prescription(
    payload: PrescriptionCreate,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.create_prescription(actor.clinic_id, payload, actor)


@router.get(
    "/dashboard/stats",
    response_model=PrescriptionDashboardStats,
    summary="Prescription dashboard metrics",
    description="Returns aggregate counts of total, today's, issued, draft, cancelled prescriptions, and follow-ups due.",
)
async def get_prescription_dashboard_stats(
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDashboardStats:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.get_dashboard_stats(actor.clinic_id)


@router.get(
    "/medicines/search",
    response_model=list[MedicineCatalogRead],
    summary="Search medication catalog",
    description="Searches global and clinic-specific medication catalog with autocomplete support.",
)
async def search_medicines(
    q: str | None = Query(None, description="Search term for brand or generic name"),
    category: str | None = Query(None, description="Filter by clinical category"),
    form: str | None = Query(None, description="Filter by dosage form"),
    limit: int = Query(30, ge=1, le=100),
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[MedicineCatalogRead]:
    service = PrescriptionService(db)
    return await service.search_medicines(
        clinic_id=actor.clinic_id, query=q, category=category, form=form, limit=limit
    )


@router.post(
    "/medicines",
    response_model=MedicineCatalogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add custom medicine to catalog",
    description="Adds a clinic-specific medicine into the searchable catalog.",
)
async def create_custom_medicine(
    payload: MedicineCatalogCreate,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> MedicineCatalogRead:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.create_medicine(actor.clinic_id, payload, actor)


@router.get(
    "/templates",
    response_model=list[PrescriptionTemplateRead],
    summary="List procedure prescription templates",
    description="Returns pre-configured clinical templates (Extraction, RCT, Implant, Scaling, Pediatric).",
)
async def list_prescription_templates(
    category: str | None = Query(None, description="Filter by template category"),
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[PrescriptionTemplateRead]:
    service = PrescriptionService(db)
    return await service.list_templates(clinic_id=actor.clinic_id, category=category)


@router.post(
    "/templates",
    response_model=PrescriptionTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom prescription template",
    description="Creates a customized prescription template for the clinic.",
)
async def create_custom_template(
    payload: PrescriptionTemplateCreate,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionTemplateRead:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.create_template(actor.clinic_id, payload, actor)


@router.get(
    "/patient/{patient_id}",
    response_model=list[PrescriptionDetail],
    summary="Patient prescription history",
    description="Returns all prescriptions for a specific patient in chronological order.",
)
async def get_patient_prescriptions(
    patient_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[PrescriptionDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.get_patient_prescriptions(actor.clinic_id, patient_id)


@router.get(
    "/treatment/{treatment_id}",
    response_model=list[PrescriptionDetail],
    summary="Treatment prescriptions",
    description="Returns prescriptions associated with a specific treatment record.",
)
async def get_treatment_prescriptions(
    treatment_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[PrescriptionDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.get_treatment_prescriptions(actor.clinic_id, treatment_id)


@router.get(
    "/appointment/{appointment_id}",
    response_model=list[PrescriptionDetail],
    summary="Appointment prescriptions",
    description="Returns prescriptions associated with a specific appointment visit.",
)
async def get_appointment_prescriptions(
    appointment_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[PrescriptionDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.get_appointment_prescriptions(actor.clinic_id, appointment_id)


@router.get(
    "",
    response_model=list[PrescriptionDetail],
    summary="List clinic prescriptions",
    description="Returns filtered prescriptions for the current clinic.",
)
async def list_prescriptions(
    patient_id: UUID | None = Query(None),
    treatment_id: UUID | None = Query(None),
    dentist_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> list[PrescriptionDetail]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.list_prescriptions(
        clinic_id=actor.clinic_id,
        patient_id=patient_id,
        treatment_id=treatment_id,
        dentist_id=dentist_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionDetail,
    summary="Get prescription detail",
    description="Retrieves a complete prescription with patient, clinician, and item breakdown.",
)
async def get_prescription(
    prescription_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.get_prescription(actor.clinic_id, prescription_id)


@router.patch(
    "/{prescription_id}",
    response_model=PrescriptionDetail,
    summary="Update draft prescription",
    description="Updates diagnosis, medications, or instructions on an unissued draft prescription.",
)
async def update_prescription(
    prescription_id: UUID,
    payload: PrescriptionUpdate,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.update_prescription(
        actor.clinic_id, prescription_id, payload, actor
    )


@router.post(
    "/{prescription_id}/issue",
    response_model=PrescriptionDetail,
    summary="Officially issue prescription",
    description="Locks prescription into an immutable clinical record and marks it ISSUED.",
)
async def issue_prescription(
    prescription_id: UUID,
    payload: PrescriptionIssue | None = None,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.issue_prescription(actor.clinic_id, prescription_id, actor)


@router.post(
    "/{prescription_id}/cancel",
    response_model=PrescriptionDetail,
    summary="Cancel prescription",
    description="Cancels an active or draft prescription with a recorded clinical reason.",
)
async def cancel_prescription(
    prescription_id: UUID,
    payload: PrescriptionCancel,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.cancel_prescription(
        actor.clinic_id, prescription_id, payload.reason, actor
    )


@router.post(
    "/{prescription_id}/duplicate",
    response_model=PrescriptionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate prescription",
    description="Creates a new draft prescription prefilled with items from an existing prescription.",
)
async def duplicate_prescription(
    prescription_id: UUID,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> PrescriptionDetail:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    return await service.duplicate_prescription(
        actor.clinic_id, prescription_id, actor
    )


@router.delete(
    "/{prescription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete draft prescription",
    description="Soft-deletes a draft prescription. Issued prescriptions cannot be deleted.",
)
async def delete_prescription(
    prescription_id: UUID,
    actor: User = Depends(require_roles(*CLINICAL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    await service.delete_prescription(actor.clinic_id, prescription_id, actor)


@router.get(
    "/{prescription_id}/pdf",
    summary="Download printable prescription PDF",
    description="Generates an official A4 printable dental prescription with clinic header and credentials.",
)
async def download_prescription_pdf(
    prescription_id: UUID,
    actor: User = Depends(require_roles(*ALL_STAFF)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    service = PrescriptionService(db)
    rx = await service.get_prescription(actor.clinic_id, prescription_id)

    pdf_bytes = PrescriptionPDFService.generate_pdf(rx)
    filename = f"Prescription-{rx.prescription_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )

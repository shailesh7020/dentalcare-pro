from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user, require_roles
from app.models.consent_form import FormStatus, FormType
from app.models.identity import Role, User
from app.schemas.consent_form import (
    ConsentRecordCreate,
    ConsentRecordRead,
    FormTemplateCreate,
    FormTemplateRead,
    FormTemplateUpdate,
    PatientFormCreate,
    PatientFormRead,
    PatientFormReview,
    PatientFormSubmit,
)
from app.services.consent_form_service import ConsentFormService

router = APIRouter(prefix="/consents-forms", tags=["Consent & Digital Forms"])

STAFF_ROLES = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
]

ADMIN_ROLES = [Role.SUPER_ADMIN, Role.CLINIC_ADMIN]


@router.get("/templates", response_model=list[FormTemplateRead])
async def list_form_templates(
    form_type: FormType | None = Query(default=None),
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[FormTemplateRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.list_templates(actor.clinic_id, form_type)


@router.post("/templates", response_model=FormTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_form_template(
    payload: FormTemplateCreate,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> FormTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.create_template(actor.clinic_id, payload)


@router.get("/templates/{template_id}", response_model=FormTemplateRead)
async def get_form_template(
    template_id: UUID,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> FormTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.get_template(actor.clinic_id, template_id)


@router.put("/templates/{template_id}", response_model=FormTemplateRead)
async def update_form_template(
    template_id: UUID,
    payload: FormTemplateUpdate,
    actor: User = Depends(require_roles(*ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> FormTemplateRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.update_template(actor.clinic_id, template_id, payload)


@router.get("/patient-forms", response_model=list[PatientFormRead])
async def list_patient_forms(
    patient_id: UUID | None = Query(default=None),
    status_filter: FormStatus | None = Query(default=None, alias="status"),
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[PatientFormRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.list_patient_forms(actor.clinic_id, patient_id=patient_id, status=status_filter)


@router.post("/patient-forms", response_model=PatientFormRead, status_code=status.HTTP_201_CREATED)
async def assign_patient_form(
    payload: PatientFormCreate,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientFormRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.assign_patient_form(actor.clinic_id, payload)


@router.get("/patient-forms/{form_id}", response_model=PatientFormRead)
async def get_patient_form(
    form_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientFormRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    form = await service.get_patient_form(actor.clinic_id, form_id)
    if actor.role == Role.PATIENT and form.patient_id != actor.patient_id:
        raise HTTPException(status_code=403, detail="Unauthorized form access.")
    return form


@router.post("/patient-forms/{form_id}/submit", response_model=PatientFormRead)
async def submit_patient_form(
    form_id: UUID,
    payload: PatientFormSubmit,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientFormRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    form = await service.get_patient_form(actor.clinic_id, form_id)
    if actor.role == Role.PATIENT and form.patient_id != actor.patient_id:
        raise HTTPException(status_code=403, detail="Unauthorized form access.")
    return await service.submit_patient_form(actor.clinic_id, form_id, payload)


@router.post("/patient-forms/{form_id}/review", response_model=PatientFormRead)
async def review_patient_form(
    form_id: UUID,
    payload: PatientFormReview,
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientFormRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.review_patient_form(actor.clinic_id, form_id, actor.id, payload)


@router.get("/consents", response_model=list[ConsentRecordRead])
async def list_consent_records(
    patient_id: UUID | None = Query(default=None),
    treatment_id: UUID | None = Query(default=None),
    actor: User = Depends(require_roles(*STAFF_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[ConsentRecordRead]:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    service = ConsentFormService(db)
    return await service.list_consent_records(actor.clinic_id, patient_id=patient_id, treatment_id=treatment_id)


@router.post("/consents", response_model=ConsentRecordRead, status_code=status.HTTP_201_CREATED)
async def record_signed_consent(
    payload: ConsentRecordCreate,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentRecordRead:
    if not actor.clinic_id:
        raise HTTPException(status_code=400, detail="Clinic context required.")
    if actor.role == Role.PATIENT and payload.patient_id != actor.patient_id:
        raise HTTPException(status_code=403, detail="Cannot record consent for another patient.")
    service = ConsentFormService(db)
    return await service.record_consent(actor.clinic_id, payload)

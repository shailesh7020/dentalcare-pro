from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.dependencies.auth import current_user, require_roles
from app.models import BloodGroup, Gender, Patient, Role, User
from app.schemas.patient import (
    DentalHistoryInput,
    DocumentRead,
    DocumentUploadResponse,
    MedicalHistoryInput,
    PatientDetail,
    PatientInput,
    PatientList,
    PatientMutationResponse,
    PatientRead,
    PatientUpdate,
    TimelineRead,
)
from app.schemas.treatment import TreatmentRead
from app.services.patient_service import PatientService
from app.services.treatment_service import TreatmentService

router = APIRouter(prefix="/patients", tags=["Patients"])
WRITE_ROLES = (Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.DENTIST, Role.RECEPTIONIST)
DELETE_ROLES = (Role.SUPER_ADMIN, Role.CLINIC_ADMIN, Role.RECEPTIONIST)


def read_patient(patient: Patient) -> PatientRead:
    return PatientRead.model_validate(patient)


async def detail_patient(service: PatientService, patient: Patient) -> PatientDetail:
    medical, dental = await service.repository.histories(patient.id)
    return PatientDetail(
        **read_patient(patient).model_dump(),
        alternate_mobile=patient.alternate_mobile,
        address=patient.address,
        state=patient.state,
        country=patient.country,
        pin_code=patient.pin_code,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_number=patient.emergency_contact_number,
        emergency_contact_relation=patient.emergency_contact_relation,
        insurance_provider=patient.insurance_provider,
        insurance_policy_number=patient.insurance_policy_number,
        preferred_language=patient.preferred_language,
        notes=patient.notes,
        aadhaar_number=patient.aadhaar_number,
        marital_status=patient.marital_status,
        occupation=patient.occupation,
        medical_history=MedicalHistoryInput.model_validate(medical) if medical else None,
        dental_history=DentalHistoryInput.model_validate(dental) if dental else None,
    )


@router.post(
    "",
    response_model=PatientMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a patient",
    description="Registers a clinic-scoped patient and optionally creates medical and dental histories.",
)
async def create_patient(
    payload: PatientInput,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientMutationResponse:
    patient, warnings = await PatientService(db, actor).create(payload)
    return PatientMutationResponse(patient=read_patient(patient), duplicate_warnings=warnings)


@router.get(
    "",
    response_model=PatientList,
    summary="List clinic patients",
    description="Searches patient number, name, mobile number, or email within the authenticated clinic with status, gender, and blood group filters.",
)
async def list_patients(
    search: str | None = Query(default=None, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    sort: str = Query(
        default="created_at",
        pattern="^(patient_number|name|created_at|date_of_birth|mobile_number)$",
    ),
    descending: bool = True,
    status_filter: str = Query(
        default="active", alias="status", pattern="^(active|archived|all)$"
    ),
    gender: Gender | None = Query(default=None),
    blood_group: BloodGroup | None = Query(default=None),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientList:
    service = PatientService(db, actor)
    patients, total = await service.repository.list_patients(
        service.clinic_id,
        search=search,
        skip=skip,
        limit=limit,
        sort=sort,
        descending=descending,
        status=status_filter,
        gender=gender.value if gender else None,
        blood_group=blood_group.value if blood_group else None,
    )
    return PatientList(
        items=[read_patient(patient) for patient in patients], total=total, skip=skip, limit=limit
    )


@router.get("/search", response_model=PatientList, summary="Search clinic patients")
async def search_patients(
    q: str = Query(min_length=1, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientList:
    return await list_patients(
        search=q,
        skip=skip,
        limit=limit,
        sort="created_at",
        descending=True,
        status_filter="active",
        gender=None,
        blood_group=None,
        actor=actor,
        db=db,
    )


@router.get("/{patient_id}", response_model=PatientDetail, summary="Get a patient profile")
async def get_patient(
    patient_id: UUID, actor: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> PatientDetail:
    service = PatientService(db, actor)
    patient = await service.get(patient_id, viewed=True)
    return await detail_patient(service, patient)


@router.patch(
    "/{patient_id}",
    response_model=PatientMutationResponse,
    summary="Update a patient profile",
)
async def update_patient(
    patient_id: UUID,
    payload: PatientUpdate,
    actor: User = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientMutationResponse:
    patient, warnings = await PatientService(db, actor).update(patient_id, payload)
    return PatientMutationResponse(patient=read_patient(patient), duplicate_warnings=warnings)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive a patient")
async def delete_patient(
    patient_id: UUID,
    actor: User = Depends(require_roles(*DELETE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PatientService(db, actor).delete(patient_id)


@router.post(
    "/{patient_id}/restore", response_model=PatientRead, summary="Restore an archived patient"
)
async def restore_patient(
    patient_id: UUID,
    actor: User = Depends(require_roles(*DELETE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PatientRead:
    return read_patient(await PatientService(db, actor).restore(patient_id))


@router.get(
    "/{patient_id}/timeline", response_model=list[TimelineRead], summary="Get patient timeline"
)
async def patient_timeline(
    patient_id: UUID, actor: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[TimelineRead]:
    service = PatientService(db, actor)
    await service.get(patient_id)
    return [
        TimelineRead.model_validate(event)
        for event in await service.repository.timeline(service.clinic_id, patient_id)
    ]


@router.get(
    "/{patient_id}/documents",
    response_model=list[DocumentRead],
    summary="List patient documents",
    description="Lists all uploaded documents, photos, and consent forms for the patient.",
)
async def list_documents(
    patient_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentRead]:
    service = PatientService(db, actor)
    documents = await service.list_documents(patient_id)
    return [
        DocumentRead(
            id=doc.id,
            patient_id=doc.patient_id,
            clinic_id=doc.clinic_id,
            file_name=doc.file_name,
            content_type=doc.content_type,
            document_type=doc.document_type,
            storage_key=doc.storage_key,
            url=f"/api/v1/patients/{patient_id}/documents/{doc.id}/download",
            created_at=doc.created_at,
        )
        for doc in documents
    ]


@router.post(
    "/{patient_id}/documents",
    response_model=DocumentUploadResponse,
    summary="Upload a patient photo or document",
    description="Accepts JPEG, PNG, and PDF files up to 10 MB using the configured storage service.",
)
async def upload_document(
    patient_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    document_type: str = Query(default="DOCUMENT"),
    actor: User = Depends(require_roles(*WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    service = PatientService(db, actor)
    patient = await service.get(patient_id)
    key, url = await request.app.state.storage.save_patient_upload(
        service.clinic_id, patient.id, file
    )
    document = await service.upload_document(
        patient_id=patient.id,
        file_name=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        storage_key=key,
        url=url,
        document_type=document_type,
    )
    return DocumentUploadResponse(
        id=str(document.id),
        file_name=document.file_name,
        content_type=document.content_type,
        document_type=document.document_type,
        url=f"/api/v1/patients/{patient.id}/documents/{document.id}/download",
    )


@router.get(
    "/{patient_id}/documents/{document_id}/download",
    summary="Download a patient document",
    description="Streams an uploaded patient document with authenticated clinic isolation.",
)
async def download_document(
    patient_id: UUID,
    document_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    service = PatientService(db, actor)
    document = await service.get_document(patient_id, document_id)
    settings = get_settings()
    file_path = settings.storage_local_path / document.storage_key
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=document.file_name,
    )


@router.get(
    "/{patient_id}/treatments",
    response_model=list[TreatmentRead],
    summary="List all treatments for a patient",
    description="Fetches treatment history for a specific patient within the clinic.",
)
async def list_patient_treatments_endpoint(
    patient_id: UUID,
    actor: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TreatmentRead]:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required"
        )
    service = TreatmentService(db)
    return await service.list_by_patient(actor.clinic_id, patient_id)



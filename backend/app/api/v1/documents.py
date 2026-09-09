from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.models.identity import User
from app.models.mobile import MobileClinicalMedia
from app.schemas.mobile import MobileClinicalMediaRead
from app.services.clinical_storage_service import ClinicalStorageService

router = APIRouter(prefix="/documents", tags=["Clinical Documents & File Storage"])


@router.post("/upload", response_model=MobileClinicalMediaRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    patient_id: UUID = Form(...),
    category: str = Form(default="document"),
    tooth_number: int | None = Form(default=None),
    notes: str | None = Form(default=None),
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MobileClinicalMediaRead:
    media = await ClinicalStorageService.save_clinical_file(
        db=db,
        clinic_id=user.clinic_id,
        patient_id=patient_id,
        captured_by_id=user.id,
        category=category,
        upload=file,
        tooth_number=tooth_number,
        notes=notes,
    )
    return MobileClinicalMediaRead.model_validate(media)


@router.get("/patient/{patient_id}", response_model=list[MobileClinicalMediaRead])
async def list_patient_documents(
    patient_id: UUID,
    category: str | None = Query(default=None),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MobileClinicalMediaRead]:
    docs = await ClinicalStorageService.get_patient_documents(db=db, patient_id=patient_id, category=category)
    return [MobileClinicalMediaRead.model_validate(d) for d in docs]


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(MobileClinicalMedia, document_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # file_url is /storage/<category>/...
    rel_path = doc.file_url.replace("/storage/", "")
    full_path = ClinicalStorageService.get_storage_base() / rel_path
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing on server disk")

    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    success = await ClinicalStorageService.soft_delete(db=db, document_id=document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or already deleted")


@router.post("/{document_id}/restore", status_code=status.HTTP_200_OK)
async def restore_document(
    document_id: UUID,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    success = await ClinicalStorageService.restore(db=db, document_id=document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found or not in deleted state")
    return {"status": "restored", "message": "Clinical document successfully restored."}

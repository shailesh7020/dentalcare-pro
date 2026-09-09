from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.models.identity import User
from app.schemas.signature import (
    ClinicianSignatureCreate,
    ClinicianSignatureResponse,
    SignatureVerificationResponse,
)
from app.services.signature_service import ClinicianSignatureService

router = APIRouter(prefix="/signatures", tags=["Clinician Signatures"])


@router.post("", response_model=ClinicianSignatureResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_signature(
    payload: ClinicianSignatureCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicianSignatureResponse:
    sig = await ClinicianSignatureService.save_signature(
        db=db,
        user_id=user.id,
        signature_data=payload.signature_data,
        signature_type=payload.signature_type,
    )
    return ClinicianSignatureResponse.model_validate(sig)


@router.get("/me", response_model=ClinicianSignatureResponse)
async def get_my_signature(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicianSignatureResponse:
    sig = await ClinicianSignatureService.get_by_user_id(db=db, user_id=user.id)
    if not sig:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No digital signature configured for this user",
        )
    return ClinicianSignatureResponse.model_validate(sig)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_signature(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    success = await ClinicianSignatureService.deactivate_signature(db=db, user_id=user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active digital signature found to deactivate",
        )


@router.get("/verify/{verification_hash}", response_model=SignatureVerificationResponse)
async def verify_signature(
    verification_hash: str,
    db: AsyncSession = Depends(get_db),
) -> SignatureVerificationResponse:
    sig, user = await ClinicianSignatureService.get_by_hash(db=db, verification_hash=verification_hash)
    if not sig or not user:
        return SignatureVerificationResponse(
            is_valid=False,
            verification_hash=verification_hash,
            message="Digital signature could not be verified. Document may be forged or altered.",
        )

    return SignatureVerificationResponse(
        is_valid=True,
        verification_hash=verification_hash,
        user_id=user.id,
        user_full_name=f"{user.first_name} {user.last_name}",
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        signed_at=sig.updated_at or sig.created_at,
        message="Digital signature is cryptographically verified and authentic.",
    )

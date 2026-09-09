from __future__ import annotations

import base64
import hashlib
import io
from uuid import UUID

from reportlab.platypus import Image as PlatypusImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commercial import ClinicianSignature, SignatureType
from app.models.identity import User


class ClinicianSignatureService:
    @staticmethod
    def calculate_hash(user_id: UUID, signature_data: str) -> str:
        payload = f"{user_id}:{signature_data}".encode()
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    async def get_by_user_id(cls, db: AsyncSession, user_id: UUID) -> ClinicianSignature | None:
        stmt = select(ClinicianSignature).where(
            ClinicianSignature.user_id == user_id,
            ClinicianSignature.is_active.is_(True),
            ClinicianSignature.deleted_at.is_(None),
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_hash(cls, db: AsyncSession, verification_hash: str) -> tuple[ClinicianSignature | None, User | None]:
        stmt = (
            select(ClinicianSignature, User)
            .join(User, ClinicianSignature.user_id == User.id)
            .where(
                ClinicianSignature.verification_hash == verification_hash,
                ClinicianSignature.is_active.is_(True),
                ClinicianSignature.deleted_at.is_(None),
            )
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            return None, None
        return row[0], row[1]

    @classmethod
    async def save_signature(
        cls,
        db: AsyncSession,
        user_id: UUID,
        signature_data: str,
        signature_type: SignatureType | str = SignatureType.DRAWN,
    ) -> ClinicianSignature:
        verification_hash = cls.calculate_hash(user_id, signature_data)
        
        # Check existing
        existing = await cls.get_by_user_id(db, user_id)
        if existing:
            existing.signature_data = signature_data
            existing.signature_type = str(signature_type)
            existing.verification_hash = verification_hash
            existing.is_active = True
            await db.commit()
            await db.refresh(existing)
            return existing

        signature = ClinicianSignature(
            user_id=user_id,
            signature_data=signature_data,
            signature_type=str(signature_type),
            verification_hash=verification_hash,
            is_active=True,
        )
        db.add(signature)
        await db.commit()
        await db.refresh(signature)
        return signature

    @classmethod
    async def deactivate_signature(cls, db: AsyncSession, user_id: UUID) -> bool:
        sig = await cls.get_by_user_id(db, user_id)
        if not sig:
            return False
        sig.is_active = False
        await db.commit()
        return True

    @staticmethod
    def create_signature_flowable(signature_data: str, width: float = 120, height: float = 40) -> PlatypusImage | None:
        """Converts base64 signature into a ReportLab Platypus Image."""
        try:
            if "," in signature_data:
                b64_str = signature_data.split(",", 1)[1]
            else:
                b64_str = signature_data
            raw_bytes = base64.b64decode(b64_str)
            return PlatypusImage(io.BytesIO(raw_bytes), width=width, height=height)
        except (ValueError, OSError):
            return None

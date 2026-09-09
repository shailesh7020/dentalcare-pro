from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DentalHistory, MedicalHistory, Patient, PatientDocument, PatientTimelineEvent


class PatientRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _base(self, clinic_id: UUID, include_deleted: bool = False) -> Select:
        query = select(Patient).where(Patient.clinic_id == clinic_id)
        return query if include_deleted else query.where(Patient.deleted_at.is_(None))

    async def get(
        self, clinic_id: UUID, patient_id: UUID, include_deleted: bool = False
    ) -> Patient | None:
        return await self.db.scalar(
            self._base(clinic_id, include_deleted).where(Patient.id == patient_id)
        )

    async def list_patients(
        self,
        clinic_id: UUID,
        search: str | None = None,
        skip: int = 0,
        limit: int = 25,
        sort: str = "created_at",
        descending: bool = True,
        status: str = "active",
        gender: str | None = None,
        blood_group: str | None = None,
    ) -> tuple[list[Patient], int]:
        if status == "archived":
            query = select(Patient).where(
                Patient.clinic_id == clinic_id, Patient.deleted_at.is_not(None)
            )
        elif status == "all":
            query = select(Patient).where(Patient.clinic_id == clinic_id)
        else:
            query = select(Patient).where(
                Patient.clinic_id == clinic_id, Patient.deleted_at.is_(None)
            )

        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Patient.patient_number.ilike(term),
                    Patient.first_name.ilike(term),
                    Patient.middle_name.ilike(term),
                    Patient.last_name.ilike(term),
                    Patient.mobile_number.ilike(term),
                    Patient.email.ilike(term),
                )
            )
        if gender:
            query = query.where(Patient.gender == gender)
        if blood_group:
            query = query.where(Patient.blood_group == blood_group)

        ordering = {
            "patient_number": Patient.patient_number,
            "name": Patient.first_name,
            "created_at": Patient.created_at,
            "date_of_birth": Patient.date_of_birth,
            "mobile_number": Patient.mobile_number,
        }.get(sort, Patient.created_at)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            (
                await self.db.scalars(
                    query.order_by(ordering.desc() if descending else ordering.asc())
                    .offset(skip)
                    .limit(limit)
                )
            ).all()
        )
        return items, total

    async def duplicates(
        self,
        clinic_id: UUID,
        mobile: str | None,
        email: str | None,
        aadhaar: str | None,
        exclude_id: UUID | None = None,
    ) -> list[Patient]:
        conditions = [Patient.mobile_number == mobile] if mobile else []
        if email:
            conditions.append(Patient.email == email)
        if aadhaar:
            conditions.append(Patient.aadhaar_number == aadhaar)
        query = (
            self._base(clinic_id).where(or_(*conditions))
            if conditions
            else self._base(clinic_id).where(False)
        )
        if exclude_id:
            query = query.where(Patient.id != exclude_id)
        return list((await self.db.scalars(query)).all())

    async def histories(
        self, patient_id: UUID
    ) -> tuple[MedicalHistory | None, DentalHistory | None]:
        med = await self.db.scalar(
            select(MedicalHistory).where(MedicalHistory.patient_id == patient_id)
        )
        dental = await self.db.scalar(
            select(DentalHistory).where(DentalHistory.patient_id == patient_id)
        )
        return med, dental

    async def timeline(self, clinic_id: UUID, patient_id: UUID) -> list[PatientTimelineEvent]:
        query = (
            select(PatientTimelineEvent)
            .where(
                PatientTimelineEvent.clinic_id == clinic_id,
                PatientTimelineEvent.patient_id == patient_id,
                PatientTimelineEvent.deleted_at.is_(None),
            )
            .order_by(PatientTimelineEvent.created_at.desc())
        )
        return list((await self.db.scalars(query)).all())

    async def documents(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[PatientDocument]:
        query = (
            select(PatientDocument)
            .where(
                PatientDocument.clinic_id == clinic_id,
                PatientDocument.patient_id == patient_id,
                PatientDocument.deleted_at.is_(None),
            )
            .order_by(PatientDocument.created_at.desc())
        )
        return list((await self.db.scalars(query)).all())

    async def get_document(
        self, clinic_id: UUID, patient_id: UUID, document_id: UUID
    ) -> PatientDocument | None:
        query = select(PatientDocument).where(
            PatientDocument.clinic_id == clinic_id,
            PatientDocument.patient_id == patient_id,
            PatientDocument.id == document_id,
            PatientDocument.deleted_at.is_(None),
        )
        return await self.db.scalar(query)


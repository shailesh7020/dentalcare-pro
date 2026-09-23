from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
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

        words: list[str] = []
        if search:
            raw = search.strip()
            term = f"%{raw}%"
            words = [w for w in raw.split() if w]

            full_name = func.concat(Patient.first_name, " ", Patient.last_name)
            full_name_rev = func.concat(Patient.last_name, " ", Patient.first_name)
            full_name_with_middle = func.concat(
                Patient.first_name, " ", func.coalesce(Patient.middle_name, ""), " ", Patient.last_name
            )

            base_conds = [
                Patient.patient_number.ilike(term),
                Patient.first_name.ilike(term),
                Patient.middle_name.ilike(term),
                Patient.last_name.ilike(term),
                Patient.mobile_number.ilike(term),
                Patient.email.ilike(term),
                full_name.ilike(term),
                full_name_rev.ilike(term),
                full_name_with_middle.ilike(term),
            ]

            if len(words) > 1:
                word_conds = []
                for w in words:
                    wt = f"%{w}%"
                    word_conds.append(
                        or_(
                            Patient.first_name.ilike(wt),
                            Patient.last_name.ilike(wt),
                            Patient.middle_name.ilike(wt),
                            Patient.patient_number.ilike(wt),
                            Patient.mobile_number.ilike(wt),
                        )
                    )
                all_words_clause = and_(*word_conds)
                search_clause = or_(*base_conds, all_words_clause)
            else:
                search_clause = or_(*base_conds)

            query = query.where(search_clause)

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

        # Fallback if multiple search words gave 0 results (e.g. spelling variation in one word like Agrawal vs Agarwal)
        if total == 0 and search and len(words) > 1:
            any_word_conds = []
            for w in words:
                wt = f"%{w}%"
                any_word_conds.append(
                    or_(
                        Patient.first_name.ilike(wt),
                        Patient.last_name.ilike(wt),
                        Patient.middle_name.ilike(wt),
                        Patient.patient_number.ilike(wt),
                        Patient.mobile_number.ilike(wt),
                    )
                )
            base_fallback_query = select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.deleted_at.is_(None) if status != "archived" else Patient.deleted_at.is_not(None),
                or_(*any_word_conds),
            )
            if gender:
                base_fallback_query = base_fallback_query.where(Patient.gender == gender)
            if blood_group:
                base_fallback_query = base_fallback_query.where(Patient.blood_group == blood_group)

            fallback_total = (
                await self.db.scalar(select(func.count()).select_from(base_fallback_query.subquery())) or 0
            )
            if fallback_total > 0:
                total = fallback_total
                query = base_fallback_query

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


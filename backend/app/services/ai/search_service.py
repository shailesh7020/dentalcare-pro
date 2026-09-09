from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.identity import User
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.ai import AISearchRequest, AISearchResponse, AISearchResultItem


class AINaturalLanguageSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_natural_language(
        self, clinic_id: UUID, payload: AISearchRequest, actor: User
    ) -> AISearchResponse:
        q = payload.query.lower().strip()
        results: list[AISearchResultItem] = []
        intent = "GENERAL_SEARCH"

        # 1. Diabetic / Medical condition queries
        if "diabet" in q or "hyperten" in q or "allerg" in q or "heart" in q:
            intent = "PATIENTS_BY_MEDICAL_CONDITION"
            keyword = "diabet" if "diabet" in q else "hyperten" if "hyperten" in q else "allerg" if "allerg" in q else "cardio"

            stmt = (
                select(Patient)
                .options(selectinload(Patient.medical_history))
                .where(Patient.clinic_id == clinic_id, Patient.deleted_at.is_(None))
            )
            patients = list((await self.db.execute(stmt)).scalars().all())
            for p in patients:
                matches = []
                mh = getattr(p, "medical_history", None)
                if mh is not None:
                    if isinstance(mh, list):
                        for it in mh:
                            cn = getattr(it, "condition_name", "")
                            nt = getattr(it, "notes", "") or ""
                            if keyword in cn.lower() or keyword in nt.lower():
                                matches.append(cn)
                    else:
                        if keyword == "diabet" and getattr(mh, "diabetes", False):
                            matches.append("Type 2 Diabetes")
                        elif keyword == "hyperten" and getattr(mh, "hypertension", False):
                            matches.append("Hypertension")
                        elif keyword == "allerg" and getattr(mh, "allergies", None):
                            matches.append(f"Allergy: {mh.allergies}")
                        elif getattr(mh, "additional_notes", None) and keyword in str(mh.additional_notes).lower():
                            matches.append(str(mh.additional_notes))
                if matches:
                    results.append(
                        AISearchResultItem(
                            entity_type="PATIENT",
                            id=str(p.id),
                            title=f"{p.first_name} {p.last_name} ({p.patient_number})",
                            subtitle=f"Medical Condition: {', '.join(matches)}",
                            detail=f"Phone: {p.mobile_number} · DOB: {p.date_of_birth or 'N/A'}",
                            link=f"/patients/{p.id}",
                        )
                    )

        # 2. Missed / No-show appointments
        elif "missed" in q or "no-show" in q or "no show" in q or "cancelled" in q:
            intent = "APPOINTMENTS_NO_SHOW_OR_CANCELLED"
            status_filter = AppointmentStatus.CANCELLED if "cancelled" in q else AppointmentStatus.NO_SHOW
            stmt = (
                select(Appointment)
                .options(selectinload(Appointment.patient), selectinload(Appointment.dentist))
                .where(
                    Appointment.clinic_id == clinic_id,
                    Appointment.status == status_filter,
                    Appointment.deleted_at.is_(None),
                )
                .order_by(Appointment.date.desc())
                .limit(20)
            )
            appts = list((await self.db.execute(stmt)).scalars().all())
            for a in appts:
                p_name = f"{a.patient.first_name} {a.patient.last_name}" if a.patient else "Patient"
                results.append(
                    AISearchResultItem(
                        entity_type="APPOINTMENT",
                        id=str(a.id),
                        title=f"{a.appointment_number} – {p_name}",
                        subtitle=f"{a.status.value} on {a.date} at {a.start_time}",
                        detail=f"Reason: {a.chief_complaint or 'Consultation'}",
                        link="/appointments",
                    )
                )

        # 3. Root canal / Treatment queries
        elif "root canal" in q or "implant" in q or "treatment" in q or "scaling" in q:
            intent = "TREATMENTS_BY_PROCEDURE"
            proc_keyword = "root canal" if "root canal" in q else "implant" if "implant" in q else "scaling" if "scaling" in q else ""
            stmt = (
                select(Treatment)
                .options(selectinload(Treatment.patient), selectinload(Treatment.procedures))
                .where(Treatment.clinic_id == clinic_id, Treatment.deleted_at.is_(None))
                .order_by(Treatment.created_at.desc())
                .limit(20)
            )
            trts = list((await self.db.execute(stmt)).scalars().all())
            for t in trts:
                if not proc_keyword or proc_keyword in t.treatment_plan_name.lower():
                    p_name = f"{t.patient.first_name} {t.patient.last_name}" if t.patient else "Patient"
                    results.append(
                        AISearchResultItem(
                            entity_type="TREATMENT",
                            id=str(t.id),
                            title=f"{t.treatment_plan_name} ({t.status.value})",
                            subtitle=f"Patient: {p_name}",
                            detail=f"Created: {t.created_at.strftime('%Y-%m-%d')} · {len(t.procedures)} procedures",
                            link=f"/treatments/{t.id}",
                        )
                    )

        # 4. Fallback search across patients by name or phone
        if not results:
            stmt = select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.deleted_at.is_(None),
                or_(
                    Patient.first_name.ilike(f"%{q}%"),
                    Patient.last_name.ilike(f"%{q}%"),
                    Patient.patient_number.ilike(f"%{q}%"),
                    Patient.mobile_number.ilike(f"%{q}%"),
                ),
            ).limit(10)
            pats = list((await self.db.execute(stmt)).scalars().all())
            for p in pats:
                results.append(
                    AISearchResultItem(
                        entity_type="PATIENT",
                        id=str(p.id),
                        title=f"{p.first_name} {p.last_name} ({p.patient_number})",
                        subtitle="Patient Record",
                        detail=f"Phone: {p.mobile_number}",
                        link=f"/patients/{p.id}",
                    )
                )

        return AISearchResponse(
            parsed_intent=intent,
            total_count=len(results),
            results=results,
        )

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import AIAuditLog, AIConfiguration, AITaskType
from app.models.appointment import Appointment, AppointmentStatus
from app.models.consent_form import FormStatus, PatientForm
from app.models.identity import User
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.treatment import Treatment
from app.schemas.ai import (
    MissingDocAuditResponse,
    PatientSummaryRequest,
    PatientSummaryResponse,
    RiskAlert,
    RiskSeverity,
)
from app.services.ai.prompts import (
    PATIENT_SUMMARY_SYSTEM_PROMPT,
    format_patient_summary_prompt,
)
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.factory import AIProviderFactory


class AIClinicalAssistantService:
    def __init__(self, db: AsyncSession, provider: BaseAIProvider | None = None):
        self.db = db
        self._custom_provider = provider

    async def _get_provider(self, clinic_id: UUID) -> BaseAIProvider:
        if self._custom_provider:
            return self._custom_provider
        stmt = select(AIConfiguration).where(
            AIConfiguration.clinic_id == clinic_id, AIConfiguration.is_active.is_(True)
        )
        config = await self.db.scalar(stmt)
        return AIProviderFactory.get_provider(config)

    async def summarize_patient_history(
        self,
        patient_id_or_payload: UUID | PatientSummaryRequest,
        clinic_id_or_actor: UUID | User,
        user_id: UUID | None = None,
    ) -> PatientSummaryResponse:
        if isinstance(patient_id_or_payload, PatientSummaryRequest):
            patient_id = patient_id_or_payload.patient_id
        else:
            patient_id = patient_id_or_payload

        if isinstance(clinic_id_or_actor, User):
            clinic_id = clinic_id_or_actor.clinic_id
            if user_id is None:
                user_id = clinic_id_or_actor.id
        else:
            clinic_id = clinic_id_or_actor

        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        # 1. Past Treatments
        stmt_trt = (
            select(Treatment)
            .options(selectinload(Treatment.procedures))
            .where(
                Treatment.patient_id == patient_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
            .order_by(Treatment.created_at.desc())
            .limit(5)
        )
        treatments = list((await self.db.execute(stmt_trt)).scalars().all())
        trt_summary_lines = [
            f"- {getattr(t, 'treatment_plan', None) or getattr(t, 'diagnosis', 'Treatment')} ({t.status}): {len(getattr(t, 'procedures', []))} procedures"
            for t in treatments
        ]
        trt_summary = "\n".join(trt_summary_lines) if trt_summary_lines else "No previous treatments recorded."

        # 2. Active Prescriptions
        stmt_rx = (
            select(Prescription)
            .options(selectinload(Prescription.items))
            .where(
                Prescription.patient_id == patient_id,
                Prescription.clinic_id == clinic_id,
                Prescription.deleted_at.is_(None),
            )
            .order_by(Prescription.date.desc())
            .limit(3)
        )
        rxs = list((await self.db.execute(stmt_rx)).scalars().all())
        rx_lines = []
        for rx in rxs:
            items_str = ", ".join([f"{it.medicine_name} ({it.dosage})" for it in rx.items])
            rx_lines.append(f"- Rx {rx.prescription_number} ({rx.date}): {items_str}")
        rx_summary = "\n".join(rx_lines) if rx_lines else "No active prescriptions."

        # 3. Medical & Allergy Strings
        med_hist = []
        allergies = []
        mh = getattr(patient, "medical_history", None)
        if mh is not None:
            if isinstance(mh, list):
                for it in mh:
                    cname = getattr(it, "condition_name", str(it))
                    notes = getattr(it, "notes", "") or ""
                    med_hist.append(f"{cname} (Notes: {notes})")
                    if "allergy" in cname.lower() or "allerg" in notes.lower():
                        allergies.append(cname)
            else:
                if getattr(mh, "diabetes", False):
                    med_hist.append("Type 2 Diabetes Mellitus")
                if getattr(mh, "hypertension", False):
                    med_hist.append("Hypertension")
                if getattr(mh, "cardiac_disease", False):
                    med_hist.append("Cardiovascular Disease")
                if getattr(mh, "asthma", False):
                    med_hist.append("Asthma")
                if getattr(mh, "allergies", None):
                    allergies.append(str(mh.allergies))
                    med_hist.append(f"Allergies: {mh.allergies}")
                if getattr(mh, "current_medications", None):
                    med_hist.append(f"Medications: {mh.current_medications}")
                if getattr(mh, "additional_notes", None):
                    med_hist.append(f"Notes: {mh.additional_notes}")
                    if "allerg" in str(mh.additional_notes).lower():
                        allergies.append(str(mh.additional_notes))

        allergies_str = ", ".join(allergies) if allergies else "None documented"
        med_str = ", ".join(med_hist) if med_hist else "No systemic medical conditions documented"

        demographics = (
            f"Name: {patient.first_name} {patient.last_name}, DOB: {patient.date_of_birth or 'Unknown'}, "
            f"Gender: {patient.gender.value if patient.gender else 'Unknown'}, Blood: {patient.blood_group.value if patient.blood_group else 'Unknown'}"
        )

        prompt = format_patient_summary_prompt(
            demographics, med_str, allergies_str, trt_summary, rx_summary
        )

        provider = await self._get_provider(clinic_id)
        result = await provider.generate(prompt, system_prompt=PATIENT_SUMMARY_SYSTEM_PROMPT)

        # Parse output
        risks: list[RiskAlert] = []
        summary_text = result.content
        recall_months = 6

        try:
            data = json.loads(result.content)
            if isinstance(data, dict):
                summary_text = data.get("summary", result.content)
                recall_months = data.get("recommended_recall_months", 6)
                for r in data.get("risks", []):
                    sev = RiskSeverity.MEDIUM
                    if str(r.get("severity", "")).upper() == "HIGH":
                        sev = RiskSeverity.HIGH
                    elif str(r.get("severity", "")).upper() == "LOW":
                        sev = RiskSeverity.LOW
                    risks.append(
                        RiskAlert(
                            category=r.get("category", "GENERAL"),
                            severity=sev,
                            title=r.get("title", "Clinical Alert"),
                            details=r.get("details", ""),
                        )
                    )
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        # Ensure documented patient conditions are represented in risk alerts
        existing_titles = " ".join([f"{r.title} {r.category} {r.details}".lower() for r in risks])
        if "penicillin" in allergies_str.lower() and "penicillin" not in existing_titles:
            risks.append(
                RiskAlert(
                    category="ALLERGY",
                    severity=RiskSeverity.HIGH,
                    title="Penicillin Allergy Documented",
                    details="Patient has documented penicillin sensitivity. Avoid Amoxicillin and beta-lactams.",
                )
            )
        if "diabet" in med_str.lower() and "diabet" not in existing_titles:
            risks.append(
                RiskAlert(
                    category="SYSTEMIC_DISEASE",
                    severity=RiskSeverity.MEDIUM,
                    title="Diabetic Patient Protocol",
                    details="Monitor blood glucose; caution with delayed post-surgical healing.",
                )
            )

        # 4. Missing Documentation Audit
        missing_docs = await self.detect_missing_documentation(patient_id, clinic_id)
        missing_alerts = missing_docs.missing_items

        # 5. Audit Log
        req_id = f"AI-SUM-{uuid4().hex[:8]}"
        audit = AIAuditLog(
            id=uuid4(),
            clinic_id=clinic_id,
            user_id=user_id,
            patient_id=patient_id,
            task_type=AITaskType.PATIENT_SUMMARY,
            provider_type=result.provider_type,
            model_name=result.model_name,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            anonymized_prompt_summary=f"Patient summary for ID {patient.patient_number}",
            response_summary=summary_text[:300],
            safety_flags=result.safety_flags,
            request_id=req_id,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(audit)
        await self.db.commit()

        return PatientSummaryResponse(
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            summary_text=summary_text,
            risk_alerts=risks,
            previous_treatments_summary=trt_summary,
            active_prescriptions_summary=rx_summary,
            recommended_recall_months=recall_months,
            missing_documentation_alerts=missing_alerts,
            generated_at=datetime.now(UTC),
        )

    async def detect_missing_documentation(
        self, patient_id: UUID, clinic_id: UUID
    ) -> MissingDocAuditResponse:
        missing_items: list[str] = []
        unbilled: list[str] = []
        unsigned_consents: list[str] = []

        # Check treatments missing clinical notes
        stmt_trt = select(Treatment).where(
            Treatment.patient_id == patient_id,
            Treatment.clinic_id == clinic_id,
            Treatment.deleted_at.is_(None),
        )
        trts = list((await self.db.execute(stmt_trt)).scalars().all())
        for t in trts:
            cnotes = getattr(t, "clinical_notes", None) or getattr(t, "soap_assessment", None) or getattr(t, "notes", None) or ""
            pname = getattr(t, "treatment_plan", None) or getattr(t, "diagnosis", "Clinical Treatment")
            if not cnotes or len(cnotes.strip()) < 10:
                missing_items.append(f"Treatment '{pname}' lacks detailed clinical notes.")

        # Check pending consent forms
        stmt_cf = select(PatientForm).where(
            PatientForm.patient_id == patient_id,
            PatientForm.clinic_id == clinic_id,
            PatientForm.status.in_([FormStatus.PENDING, FormStatus.DRAFT]),
            PatientForm.deleted_at.is_(None),
        )
        cfs = list((await self.db.execute(stmt_cf)).scalars().all())
        for cf in cfs:
            unsigned_consents.append(f"Consent Form template {cf.template_id} is awaiting patient signature.")

        # Check recent appointments with status COMPLETED but no treatment
        stmt_appt = select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.clinic_id == clinic_id,
            Appointment.status == AppointmentStatus.COMPLETED,
            Appointment.deleted_at.is_(None),
        )
        appts = list((await self.db.execute(stmt_appt)).scalars().all())
        if appts and not trts:
            missing_items.append("Completed visit without associated clinical treatment record.")

        return MissingDocAuditResponse(
            patient_id=patient_id,
            missing_items=missing_items,
            unbilled_procedures=unbilled,
            unsigned_consents=unsigned_consents,
        )

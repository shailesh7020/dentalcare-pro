from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import (
    AIAuditLog,
    AIConfiguration,
    AIRecommendation,
    AIRecommendationStatus,
    AITaskType,
)
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.ai import SOAPGenerateRequest, SOAPNoteDraft, SOAPSaveRequest
from app.services.ai.prompts import SOAP_SYSTEM_PROMPT, format_soap_prompt
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.factory import AIProviderFactory


class AISOAPNoteService:
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

    async def generate_soap_draft(
        self, clinic_id: UUID, payload: SOAPGenerateRequest, dentist_id: UUID
    ) -> SOAPNoteDraft:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient record not found.")

        # Extract appointment details if present
        complaint = "Routine dental checkup and review"
        observations = "No acute findings noted"
        if payload.appointment_id:
            appt = await self.db.get(Appointment, payload.appointment_id)
            if appt and appt.clinic_id == clinic_id:
                complaint = appt.chief_complaint or complaint
                observations = appt.notes or observations

        # Extract treatment details if present
        procedures_str = "None recorded"
        teeth_str = "General dentition"
        if payload.treatment_id:
            stmt_t = select(Treatment).options(selectinload(Treatment.procedures)).where(
                Treatment.id == payload.treatment_id, Treatment.clinic_id == clinic_id
            )
            treatment = await self.db.scalar(stmt_t)
            if treatment:
                procs = [f"{p.procedure_name} (Tooth #{p.tooth_number or 'N/A'})" for p in treatment.procedures]
                if procs:
                    procedures_str = ", ".join(procs)
        pat_age = patient.age if getattr(patient, "date_of_birth", None) else 35
        gen_str = patient.gender.value if getattr(patient, "gender", None) else "Unspecified"
        patient_info = f"{patient.first_name} {patient.last_name}, Age: {pat_age}, Gender: {gen_str}"

        prompt = format_soap_prompt(
            patient_info=patient_info,
            complaint=complaint,
            observations=observations,
            procedures=procedures_str,
            teeth_info=teeth_str,
            clinician_notes=payload.clinician_notes,
        )

        provider = await self._get_provider(clinic_id)
        result = await provider.generate(prompt, system_prompt=SOAP_SYSTEM_PROMPT)

        subj = "Patient presents for dental examination. No acute discomfort."
        obj = f"Clinical intraoral examination performed. {observations}."
        assess = f"Dental review: {complaint}."
        plan = f"Follow-up restorative plan: {procedures_str}."

        try:
            parsed = json.loads(result.content)
            if isinstance(parsed, dict):
                subj = parsed.get("subjective", subj)
                obj = parsed.get("objective", obj)
                assess = parsed.get("assessment", assess)
                plan = parsed.get("plan", plan)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        # Save recommendation draft awaiting human approval
        rec = AIRecommendation(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient.id,
            dentist_id=dentist_id,
            appointment_id=payload.appointment_id,
            treatment_id=payload.treatment_id,
            recommendation_type="SOAP_NOTE",
            input_context_json={"complaint": complaint, "notes": payload.clinician_notes},
            generated_output_json={
                "subjective": subj,
                "objective": obj,
                "assessment": assess,
                "plan": plan,
            },
            status=AIRecommendationStatus.PENDING_REVIEW,
            created_by=dentist_id,
            updated_by=dentist_id,
        )
        self.db.add(rec)

        # Audit log
        audit = AIAuditLog(
            id=uuid4(),
            clinic_id=clinic_id,
            user_id=dentist_id,
            patient_id=patient.id,
            task_type=AITaskType.SOAP_NOTE,
            provider_type=result.provider_type,
            model_name=result.model_name,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            anonymized_prompt_summary="SOAP Note Generation",
            response_summary=subj[:200],
            safety_flags=result.safety_flags,
            request_id=f"AI-SOAP-{uuid4().hex[:8]}",
            created_by=dentist_id,
            updated_by=dentist_id,
        )
        self.db.add(audit)
        await self.db.commit()

        return SOAPNoteDraft(
            subjective=subj,
            objective=obj,
            assessment=assess,
            plan=plan,
        )

    async def save_soap_to_treatment(
        self, clinic_id: UUID, payload: SOAPSaveRequest, dentist_id: UUID
    ) -> Treatment:
        treatment = await self.db.get(Treatment, payload.treatment_id)
        if not treatment or treatment.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        formatted_soap = (
            f"--- CLINICIAN SOAP NOTE ---\n"
            f"S: {payload.subjective}\n"
            f"O: {payload.objective}\n"
            f"A: {payload.assessment}\n"
            f"P: {payload.plan}"
        )

        treatment.soap_subjective = payload.subjective
        treatment.soap_objective = payload.objective
        treatment.soap_assessment = payload.assessment
        treatment.soap_plan = payload.plan
        existing = getattr(treatment, "clinical_notes", "") or ""
        treatment.clinical_notes = f"{existing}\n\n{formatted_soap}".strip()

        # Update recommendation status to APPROVED if exists
        stmt = select(AIRecommendation).where(
            AIRecommendation.treatment_id == treatment.id,
            AIRecommendation.recommendation_type == "SOAP_NOTE",
            AIRecommendation.status == AIRecommendationStatus.PENDING_REVIEW,
        ).order_by(AIRecommendation.created_at.desc()).limit(1)
        rec = await self.db.scalar(stmt)
        if rec:
            rec.status = AIRecommendationStatus.APPROVED
            rec.reviewed_by_id = dentist_id
            rec.reviewed_at = datetime.now(UTC)
            rec.final_content = formatted_soap

        await self.db.commit()
        return treatment


AISOAPService = AISOAPNoteService


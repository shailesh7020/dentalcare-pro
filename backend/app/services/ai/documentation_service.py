from __future__ import annotations

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
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.ai import (
    ClinicalDocGenerateRequest,
    ClinicalDocResponse,
    ClinicalDocType,
)
from app.services.ai.prompts import DOCUMENTATION_SYSTEM_PROMPT, format_doc_prompt
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.factory import AIProviderFactory


class AIDocumentationService:
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

    async def generate_document(
        self, clinic_id: UUID, payload: ClinicalDocGenerateRequest, user_id: UUID
    ) -> ClinicalDocResponse:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        trt_info = "General clinical consultation"
        if payload.treatment_id:
            stmt_t = select(Treatment).options(selectinload(Treatment.procedures)).where(
                Treatment.id == payload.treatment_id, Treatment.clinic_id == clinic_id
            )
            trt = await self.db.scalar(stmt_t)
            if trt:
                procs = ", ".join([p.procedure_name for p in trt.procedures]) or "None"
                trt_info = f"Treatment: {trt.treatment_plan_name}, Procedures: {procs}"

        patient_info = f"{patient.first_name} {patient.last_name}, ID: {patient.patient_number}, DOB: {patient.date_of_birth or 'N/A'}"

        prompt = format_doc_prompt(
            doc_type=payload.document_type.value,
            patient_info=patient_info,
            treatment_info=trt_info,
            recipient=payload.recipient_doctor,
            custom_notes=payload.custom_notes,
        )

        provider = await self._get_provider(clinic_id)
        result = await provider.generate(prompt, system_prompt=DOCUMENTATION_SYSTEM_PROMPT)

        title_map = {
            ClinicalDocType.REFERRAL_LETTER: "Specialist Dental Referral Letter",
            ClinicalDocType.MEDICAL_CERTIFICATE: "Medical Rest & Leave Certificate",
            ClinicalDocType.POST_OP_INSTRUCTIONS: "Post-Operative Care Instructions",
            ClinicalDocType.DISCHARGE_SUMMARY: "Clinical Discharge Summary",
            ClinicalDocType.TREATMENT_PLAN_PRESENTATION: "Patient Treatment Plan Overview",
        }
        title = title_map.get(payload.document_type, "Clinical Document")

        # Record recommendation draft
        rec = AIRecommendation(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient.id,
            dentist_id=user_id,
            treatment_id=payload.treatment_id,
            recommendation_type="DOCUMENTATION",
            input_context_json={"doc_type": payload.document_type.value, "title": title},
            generated_output_json={"content": result.content},
            status=AIRecommendationStatus.PENDING_REVIEW,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(rec)

        # Audit log
        audit = AIAuditLog(
            id=uuid4(),
            clinic_id=clinic_id,
            user_id=user_id,
            patient_id=patient.id,
            task_type=AITaskType.DOCUMENTATION,
            provider_type=result.provider_type,
            model_name=result.model_name,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            anonymized_prompt_summary=f"Clinical document: {payload.document_type.value}",
            response_summary=result.content[:250],
            safety_flags=result.safety_flags,
            request_id=f"AI-DOC-{uuid4().hex[:8]}",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(audit)
        await self.db.commit()

        return ClinicalDocResponse(
            document_type=payload.document_type,
            title=title,
            formatted_content=result.content,
            metadata={"recommendation_id": str(rec.id), "latency_ms": result.latency_ms},
        )


AIClinicalDocumentationService = AIDocumentationService


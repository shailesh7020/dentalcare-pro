from __future__ import annotations

import json
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIAuditLog, AIConfiguration, AITaskType
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.ai import (
    PrescriptionSuggestionItem,
    PrescriptionSuggestRequest,
    PrescriptionSuggestResponse,
    TreatmentOption,
    TreatmentSuggestionRequest,
    TreatmentSuggestionResponse,
)
from app.services.ai.prompts import (
    PRESCRIPTION_SYSTEM_PROMPT,
    format_prescription_prompt,
)
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.factory import AIProviderFactory


class AIPrescriptionAssistanceService:
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

    async def suggest_medications(
        self, clinic_id: UUID, payload: PrescriptionSuggestRequest, user_id: UUID
    ) -> PrescriptionSuggestResponse:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        # Check allergies and medical conditions
        allergies: list[str] = []
        medical_conditions: list[str] = []
        mh = getattr(patient, "medical_history", None)
        if mh is not None:
            if isinstance(mh, list):
                for it in mh:
                    cname = getattr(it, "condition_name", str(it))
                    notes = getattr(it, "notes", "") or ""
                    medical_conditions.append(cname)
                    if "allergy" in cname.lower() or "allerg" in notes.lower():
                        allergies.append(cname)
            else:
                if getattr(mh, "diabetes", False):
                    medical_conditions.append("Type 2 Diabetes Mellitus")
                if getattr(mh, "hypertension", False):
                    medical_conditions.append("Hypertension")
                if getattr(mh, "allergies", None):
                    allergies.append(str(mh.allergies))
                    medical_conditions.append(f"Allergies: {mh.allergies}")
                if getattr(mh, "current_medications", None):
                    medical_conditions.append(f"Medications: {mh.current_medications}")
                if getattr(mh, "additional_notes", None) and "allerg" in str(mh.additional_notes).lower():
                    allergies.append(str(mh.additional_notes))

        allergies_str = ", ".join(allergies) if allergies else "None documented"
        med_str = ", ".join(medical_conditions) if medical_conditions else "None"

        procedures_str = "None specified"
        if payload.treatment_id:
            trt = await self.db.get(Treatment, payload.treatment_id)
            if trt:
                procedures_str = getattr(trt, "treatment_plan", None) or getattr(trt, "diagnosis", "Procedure")

        pat_age = patient.age if getattr(patient, "date_of_birth", None) else 35
        patient_info = f"{patient.first_name} {patient.last_name}, Age: {pat_age}"

        prompt = format_prescription_prompt(
            patient_info=patient_info,
            allergies=allergies_str,
            diagnosis=payload.diagnosis,
            procedures=procedures_str,
            medical_history=med_str,
        )

        provider = await self._get_provider(clinic_id)
        result = await provider.generate(prompt, system_prompt=PRESCRIPTION_SYSTEM_PROMPT)

        suggested_items: list[PrescriptionSuggestionItem] = []
        allergy_warnings: list[str] = []
        interaction_warnings: list[str] = []

        is_penicillin_allergic = any("penicillin" in a.lower() for a in allergies) or "penicillin" in allergies_str.lower()

        try:
            items_data = json.loads(result.content)
            if isinstance(items_data, list):
                for it in items_data:
                    med_name = it.get("medicine_name", "Amoxicillin 500mg")
                    # Clinical Guardrail Check: Never suggest penicillin to allergic patients
                    if is_penicillin_allergic and any(p in med_name.lower() for p in ["amoxicillin", "penicillin", "augmentin", "ampicillin"]):
                        allergy_warnings.append(
                            f"ALERT: {med_name} contraindicated due to documented penicillin allergy. Substituted with Clindamycin/Azithromycin."
                        )
                        suggested_items.append(
                            PrescriptionSuggestionItem(
                                medicine_name="Clindamycin 300mg",
                                generic_name="Clindamycin HCl",
                                dosage="1 capsule",
                                frequency="QID",
                                duration="5 days",
                                instructions="Take with a full glass of water; stay upright for 30 minutes.",
                                rationale="Safe and effective alternative for penicillin-allergic patients.",
                            )
                        )
                    else:
                        suggested_items.append(
                            PrescriptionSuggestionItem(
                                medicine_name=med_name,
                                generic_name=it.get("generic_name"),
                                dosage=it.get("dosage", "1 tablet"),
                                frequency=it.get("frequency", "BD"),
                                duration=it.get("duration", "5 days"),
                                instructions=it.get("instructions", "Take after meals."),
                                rationale=it.get("rationale", "Standard empirical therapy."),
                            )
                        )
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        if not suggested_items:
            if is_penicillin_allergic:
                allergy_warnings.append("Documented Penicillin allergy: Beta-lactams avoided.")
                suggested_items.append(
                    PrescriptionSuggestionItem(
                        medicine_name="Clindamycin 300mg",
                        generic_name="Clindamycin HCl",
                        dosage="1 capsule",
                        frequency="TDS",
                        duration="5 days",
                        instructions="Take after food with full glass of water.",
                        rationale="Lincosamide antibiotic for penicillin-allergic patients.",
                    )
                )
            else:
                suggested_items.append(
                    PrescriptionSuggestionItem(
                        medicine_name="Amoxicillin 500mg",
                        generic_name="Amoxicillin",
                        dosage="1 capsule",
                        frequency="TDS",
                        duration="5 days",
                        instructions="Take after meals with plenty of water.",
                        rationale="First-line dental antibacterial prophylaxis.",
                    )
                )

        # Audit log
        audit = AIAuditLog(
            id=uuid4(),
            clinic_id=clinic_id,
            user_id=user_id,
            patient_id=patient.id,
            task_type=AITaskType.PRESCRIPTION_ASSISTANCE,
            provider_type=result.provider_type,
            model_name=result.model_name,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            anonymized_prompt_summary=f"Rx Assistance for diagnosis: {payload.diagnosis}",
            response_summary=f"{len(suggested_items)} items suggested",
            safety_flags=result.safety_flags + allergy_warnings,
            request_id=f"AI-RX-{uuid4().hex[:8]}",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(audit)
        await self.db.commit()

        return PrescriptionSuggestResponse(
            suggested_items=suggested_items,
            allergy_warnings=allergy_warnings,
            interaction_warnings=interaction_warnings,
        )

    async def suggest_treatment_plan(
        self, clinic_id: UUID, payload: TreatmentSuggestionRequest, user_id: UUID
    ) -> TreatmentSuggestionResponse:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        complaint_lower = payload.chief_complaint.lower()
        if "pain" in complaint_lower or "pulpitis" in complaint_lower or "nerve" in complaint_lower:
            primary = TreatmentOption(
                title="Root Canal Treatment & Crown",
                procedure_code="D3330",
                description="Endodontic therapy to extirpate inflamed pulpal tissue, seal root canals, and protect tooth with full coverage crown.",
                pros=["Preserves natural tooth structure", "Alleviates acute pain", "Long-term functional longevity"],
                cons=["Multi-visit procedure", "Higher initial financial commitment"],
                estimated_visits=2,
                recall_interval_days=180,
            )
            alternatives = [
                TreatmentOption(
                    title="Surgical Extraction & Implant Consultation",
                    procedure_code="D7140",
                    description="Atraumatic extraction followed by bone grafting and future dental implant fixture placement.",
                    pros=["Eliminates immediate infection source", "Single surgical appointment"],
                    cons=["Loss of natural tooth", "Requires prosthetic tooth replacement"],
                    estimated_visits=1,
                    recall_interval_days=90,
                )
            ]
            rationale = "Endodontic therapy has a >92% success rate in maintaining original tooth integrity vs extraction."
        else:
            primary = TreatmentOption(
                title="Direct Composite Restoration",
                procedure_code="D2392",
                description="Cavity preparation with adhesive bonding and incremental resin placement.",
                pros=["Minimally invasive", "Matches natural tooth color", "Completed in one visit"],
                cons=["Subject to eventual marginal wear over 7-10 years"],
                estimated_visits=1,
                recall_interval_days=180,
            )
            alternatives = [
                TreatmentOption(
                    title="Ceramic Onlay / Inlay",
                    procedure_code="D2610",
                    description="Indirect laboratory fabricated porcelain restoration for maximum cusp reinforcement.",
                    pros=["Exceptional mechanical wear resistance", "Superior marginal seal"],
                    cons=["Higher laboratory fee", "May require 2 appointments"],
                    estimated_visits=2,
                    recall_interval_days=180,
                )
            ]
            rationale = "Conservative direct composite restoration effectively halts carious lesion while preserving healthy enamel and dentin."

        return TreatmentSuggestionResponse(
            primary_recommendation=primary,
            alternative_options=alternatives,
            rationale=rationale,
        )


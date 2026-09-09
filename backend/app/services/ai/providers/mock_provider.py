from __future__ import annotations

import json
import time

from app.services.ai.providers.base import AICompletionResult, BaseAIProvider


class MockDentalAIProvider(BaseAIProvider):
    """High-fidelity, deterministic dental clinical intelligence mock provider.

    Grounds responses in ADA/AAOMS clinical guidelines for offline execution,
    testing, and air-gapped demo environments.
    """

    def __init__(self, model_name: str = "mock-dental-clinical-v1"):
        self.model_name = model_name

    async def health_check(self) -> bool:
        return True

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AICompletionResult:
        start_time = time.perf_counter()
        p_lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        flags: list[str] = []
        if "penicillin" in p_lower and ("amoxicillin" in p_lower or "allergy" in p_lower):
            flags.append("PENICILLIN_ALLERGY_DETECTED")
        if "warfarin" in p_lower or "blood thinner" in p_lower:
            flags.append("BLEEDING_RISK_DETECTED")
        if "diabetes" in p_lower or "diabetic" in p_lower:
            flags.append("DIABETIC_IMPAIRED_HEALING")

        content = self._resolve_response(p_lower, sys_lower)

        latency = int((time.perf_counter() - start_time) * 1000)
        tokens_p = max(10, len(prompt.split()) * 2)
        tokens_c = max(15, len(content.split()) * 2)

        return AICompletionResult(
            content=content,
            tokens_prompt=tokens_p,
            tokens_completion=tokens_c,
            latency_ms=latency,
            model_name=self.model_name,
            provider_type="MOCK",
            safety_flags=flags,
        )

    def _resolve_response(self, p: str, s: str) -> str:
        # 1. SOAP Note Generation
        if "soap" in s or "subjective" in p or "assessment" in p:
            return json.dumps({
                "subjective": "Patient presents with chief complaint of mild thermal sensitivity and localized food lodgement in the upper right quadrant. No spontaneous nocturnal throbbing reported.",
                "objective": "Intraoral exam reveals fractured disto-occlusal amalgam restoration on tooth #14 with secondary recurrent margin decay. Cold test responsive, electric pulp test within normal limits. Periapical radiograph shows intact lamina dura without apical radiolucency.",
                "assessment": "Tooth #14: Reversible pulpitis secondary to marginal failure of composite/amalgam restoration.",
                "plan": "1. Administer local infiltration anesthesia (2% Lignocaine with 1:100,000 Epinephrine).\n2. Complete excavation of caries and distal box preparation.\n3. Place bonded nanohybrid resin composite restoration.\n4. Occlusal adjustment in centric and lateral excursions.\n5. Follow-up hygiene recall in 6 months."
            })

        # 2. Patient Summary & Risk Alerts
        if "summary" in s or "patient history" in p:
            return json.dumps({
                "summary": "Adult patient under routine restorative care. History of composite restorations and regular periodontal scaling. Clinically stable with controlled dental hygiene.",
                "risks": [
                    {"category": "ALLERGY", "severity": "HIGH", "title": "Penicillin Hypersensitivity", "details": "Avoid Amoxicillin, Augmentin, and beta-lactams. Prescribe Clindamycin or Azithromycin if indicated."},
                    {"category": "CARDIOVASCULAR", "severity": "MEDIUM", "title": "Hypertension (Stage 1)", "details": "Monitor blood pressure prior to surgical procedures; limit vasoconstrictor dosage."}
                ],
                "recommended_recall_months": 6
            })

        # 3. Prescription Suggestions
        if "prescription" in s or "medication" in p or "antibiotic" in p:
            return json.dumps([
                {
                    "medicine_name": "Amoxicillin 500mg",
                    "generic_name": "Amoxicillin",
                    "dosage": "1 capsule",
                    "frequency": "TDS",
                    "duration": "5 days",
                    "instructions": "Take after meals with plenty of water. Complete full course.",
                    "rationale": "First-line empirical treatment for odontogenic bacterial infections."
                },
                {
                    "medicine_name": "Ibuprofen + Paracetamol (400mg/325mg)",
                    "generic_name": "Ibuprofen + Paracetamol",
                    "dosage": "1 tablet",
                    "frequency": "SOS",
                    "duration": "3 days",
                    "instructions": "Take after meals for pain; maximum 3 tablets in 24 hours.",
                    "rationale": "Dual synergistic analgesic and anti-inflammatory coverage."
                }
            ])

        # 4. Clinical Documentation (Referral / Medical Certificate / Post-Op)
        if "referral" in p or "referral" in s:
            return (
                "CLINICAL REFERRAL LETTER\n\n"
                "To: Specialist Endodontist\n"
                "Re: Endodontic Evaluation & Management for Tooth #19\n\n"
                "Dear Colleague,\n\n"
                "Thank you for seeing this patient for specialized evaluation. The patient presents with symptomatic irreversible pulpitis associated with severe apical calcification and curved mesial canals on tooth #19.\n\n"
                "Radiographic findings and intraoral clinical photos are attached for your review.\n\n"
                "Sincerely,\nDentalCare Pro Attending Clinician"
            )

        if "certificate" in p or "medical certificate" in s:
            return (
                "MEDICAL LEAVE CERTIFICATE\n\n"
                "This is to certify that the patient underwent surgical dental extraction and debridement under local anesthesia today.\n"
                "The patient is clinically advised to take 2 days of complete physical rest from work/school for proper clot formation and recovery.\n\n"
                "Attending Dental Surgeon, DentalCare Pro"
            )

        if "post-op" in p or "instructions" in p:
            return (
                "POST-OPERATIVE CARE INSTRUCTIONS\n\n"
                "1. Bite firmly on the gauze pad for 45 minutes; do not spit forcibly.\n"
                "2. Avoid hot drinks, hard foods, smoking, and drinking through a straw for 24 hours.\n"
                "3. Apply an ice pack on the outside of your cheek for 15 minutes on, 15 minutes off.\n"
                "4. Take prescribed analgesics as instructed before local anesthesia wears off.\n"
                "5. Contact the emergency clinic line if excessive bleeding persists."
            )

        # 5. Natural Language Search Intent
        if "search" in s or "find" in p:
            return json.dumps({
                "intent": "QUERY_PATIENTS",
                "filters": {"condition": "DIABETES"},
                "explanation": "Searching patients with diabetes documented in medical history."
            })

        # Default fallback
        return "Clinical decision support generated. Clinician verification is required."

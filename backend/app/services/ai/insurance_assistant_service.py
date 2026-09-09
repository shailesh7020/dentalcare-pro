from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID

from app.schemas.insurance import (
    ClaimCompletenessAuditResponse,
    CodingSuggestionItem,
    CodingSuggestionResponse,
    RejectionAnalysisResponse,
)


class InsuranceAssistantService:
    """AI Clinical & Billing Assistant for Insurance Claims, Pre-Authorizations, and Denials.

    Advisory only. All generated suggestions must be reviewed by dental billing or clinical staff.
    """

    CDT_CODE_MAPPING: ClassVar[dict[str, tuple[str, str, str, float, str]]] = {
        "root canal": (
            "D3330",
            "Endodontic therapy, molar tooth (excluding final restoration)",
            "Endodontics",
            80.0,
            "Standard CDT code for multi-canal posterior root canal therapy.",
        ),
        "pulpectomy": (
            "D3220",
            "Therapeutic pulpotomy (excluding final restoration)",
            "Endodontics",
            80.0,
            "Caries excavation and vital pulp exposure treatment.",
        ),
        "crown": (
            "D2740",
            "Crown - porcelain/ceramic substrate",
            "Major Restorative",
            50.0,
            "Single unit full-coverage indirect restoration.",
        ),
        "extraction": (
            "D7140",
            "Extraction, erupted tooth or exposed root (elevation and/or forceps removal)",
            "Oral Surgery",
            80.0,
            "Routine non-surgical exodontia.",
        ),
        "surgical extraction": (
            "D7210",
            "Extraction, erupted tooth requiring removal of bone and/or sectioning of tooth",
            "Oral Surgery",
            80.0,
            "Complex extraction with mucoperiosteal flap and bone guttering.",
        ),
        "scaling": (
            "D4341",
            "Periodontal scaling and root planing - four or more teeth per quadrant",
            "Periodontics",
            80.0,
            "Deep therapeutic debridement under local anesthesia.",
        ),
        "composite": (
            "D2392",
            "Resin-based composite - two surfaces, posterior",
            "Basic Restorative",
            80.0,
            "Direct adhesive tooth-colored restoration.",
        ),
        "exam": (
            "D0150",
            "Comprehensive oral evaluation - new or established patient",
            "Diagnostic",
            100.0,
            "Initial diagnostic baseline examination.",
        ),
        "radiograph": (
            "D0220",
            "Intraoral - periapical first radiographic image",
            "Diagnostic",
            100.0,
            "Diagnostic periapical image of symptomatic tooth.",
        ),
    }

    async def audit_claim_completeness(
        self,
        claim_id: UUID,
        procedure_codes: list[str],
        attached_document_types: list[str],
        patient_notes: str | None = None,
    ) -> ClaimCompletenessAuditResponse:
        """Audits claim line items against required supporting documentation."""
        missing_docs: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        has_xray = any("x_ray" in d.lower() or "radiograph" in d.lower() for d in attached_document_types)
        has_clinical_notes = any("note" in d.lower() or "soap" in d.lower() for d in attached_document_types)
        has_perio_chart = any("perio" in d.lower() for d in attached_document_types)

        score = 100

        # Check endodontics
        is_endo = any("D33" in code or "D32" in code for code in procedure_codes)
        if is_endo:
            if not has_xray:
                score -= 30
                missing_docs.append("Pre-operative and post-obturation periapical radiographs showing canal working length")
                warnings.append("Payers routinely deny endodontic claims without verified periapical radiographs")
            if not has_clinical_notes:
                score -= 15
                missing_docs.append("Endodontic diagnostic notes indicating pulpal diagnosis (e.g. Irreversible Pulpitis)")

        # Check major crowns / prosthodontics
        is_crown = any("D27" in code or "D29" in code for code in procedure_codes)
        if is_crown:
            if not has_xray:
                score -= 25
                missing_docs.append("Radiograph demonstrating breakdown of >= 50% clinical tooth structure")
            recommendations.append("Include dental lab fabrication invoice or shade selection photograph for ceramic crowns")

        # Check periodontal surgery
        is_perio = any("D43" in code or "D42" in code for code in procedure_codes)
        if is_perio and not has_perio_chart:
            score -= 25
            missing_docs.append("Full mouth 6-point periodontal probing chart recorded within the last 6 months")

        score = max(20, min(100, score))
        is_ready = score >= 80 and len(missing_docs) == 0

        if not is_ready:
            recommendations.append("Upload missing diagnostic evidence prior to electronic clearinghouse transmission to prevent rejection.")
        else:
            recommendations.append("Claim package meets carrier documentation guidelines. Ready for submission.")

        return ClaimCompletenessAuditResponse(
            claim_id=str(claim_id),
            completeness_score=score,
            is_ready_for_submission=is_ready,
            missing_documents=missing_docs,
            warnings=warnings,
            recommendations=recommendations,
            disclaimer="Advisory Clinical Decision Support: Dental biller must verify documentation before submission.",
        )

    async def suggest_procedure_coding(
        self, procedure_descriptions: list[str]
    ) -> CodingSuggestionResponse:
        """Suggests standardized CDT dental billing codes from clinical procedure narratives."""
        suggestions: list[CodingSuggestionItem] = []
        sorted_keys = sorted(self.CDT_CODE_MAPPING.keys(), key=len, reverse=True)

        for desc in procedure_descriptions:
            matched = False
            lower_desc = desc.lower()
            for key in sorted_keys:
                cdt, title, cat, cov, rat = self.CDT_CODE_MAPPING[key]
                if key in lower_desc:
                    suggestions.append(
                        CodingSuggestionItem(
                            procedure_name=desc,
                            suggested_cdt_code=cdt,
                            description=title,
                            standard_category=cat,
                            typical_coverage_pct=cov,
                            rationale=rat,
                        )
                    )
                    matched = True
                    break

            if not matched:
                suggestions.append(
                    CodingSuggestionItem(
                        procedure_name=desc,
                        suggested_cdt_code="D0999",
                        description="Unspecified dental procedure, by report",
                        standard_category="Adjunctive General",
                        typical_coverage_pct=50.0,
                        rationale=f"No direct standard CDT match found for '{desc}'. Manual code review recommended.",
                    )
                )

        return CodingSuggestionResponse(
            suggestions=suggestions,
            disclaimer="CDT Coding suggestions are advisory and subject to clinician and payer contract verification.",
        )

    async def analyze_rejection(
        self,
        claim_id: UUID,
        denial_code: str | None,
        denial_reason: str | None,
    ) -> RejectionAnalysisResponse:
        """Analyzes claim denial codes and drafts an appeal letter."""
        code = denial_code or "CO-16"
        reason = denial_reason or "Claim lacks required information for adjudication"

        root_cause = (
            f"Carrier rejected claim under code {code}: '{reason}'. Common triggers include missing X-rays, "
            "insufficient diagnostic ICD-10 justification, or frequency limitation."
        )

        appeal_likelihood = "HIGH" if "information" in reason.lower() or "missing" in reason.lower() else "MODERATE"

        appeal_letter = f"""FORMAL CLAIM RECONSIDERATION & CLINICAL APPEAL

Date: {datetime.now(UTC).strftime('%B %d, %Y')}
To: Claims Review & Appeals Committee
Regarding: Claim Ref #{str(claim_id)[:8].upper()}
Denial Code: {code} ({reason})

Dear Claims Evaluator,

We are submitting this formal appeal on behalf of the patient for reconsideration of the denied procedures. The performed treatment was clinically indispensable to alleviate acute pain, eliminate odontogenic infection, and restore anatomical dental mastication.

Clinical Rationale:
The patient presented with diagnostic indications satisfying accepted American Dental Association (ADA) clinical guidelines. Periapical pathology and tooth structure breakdown necessitated intervention.

Enclosed Supporting Documentation:
1. Diagnostic pre-operative periapical digital radiographs demonstrating clear pathology.
2. Complete signed Clinical SOAP Notes detailing diagnostic vitality tests (cold, electric pulp, percussion).
3. Post-operative restoration radiograph verifying complete treatment margin and anatomical seal.

In light of the substantiated clinical evidence, we respectfully request prompt reversal of this denial and disbursement of eligible policy benefits.

Sincerely,
DentalCare Pro Clinical Billing Unit
"""

        evidence = [
            "Periapical diagnostic radiograph dated prior to procedure",
            "Attending clinician signed clinical examination SOAP note",
            "Periodontal probing chart or photographic proof of crown damage",
        ]

        return RejectionAnalysisResponse(
            claim_id=str(claim_id),
            denial_code=code,
            denial_reason=reason,
            root_cause_analysis=root_cause,
            appeal_likelihood=appeal_likelihood,
            suggested_appeal_letter=appeal_letter,
            required_evidence=evidence,
            disclaimer="Advisory Appeal Assistant: Review and append signed clinician signature before mailing/uploading.",
        )

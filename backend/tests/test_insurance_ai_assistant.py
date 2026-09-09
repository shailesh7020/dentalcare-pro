from __future__ import annotations

from uuid import uuid4

import pytest

from app.services.ai.insurance_assistant_service import InsuranceAssistantService


@pytest.mark.asyncio
async def test_audit_claim_completeness_missing_xray():
    service = InsuranceAssistantService()
    claim_id = uuid4()

    # Endodontic claim D3330 with only clinical notes, NO X-ray
    audit = await service.audit_claim_completeness(
        claim_id=claim_id,
        procedure_codes=["D3330"],
        attached_document_types=["CLINICAL_NOTE"],
        patient_notes="Patient treated for deep pulpal necrosis",
    )

    assert audit.completeness_score < 100
    assert audit.is_ready_for_submission is False
    assert any("radiograph" in doc.lower() for doc in audit.missing_documents)
    assert len(audit.warnings) > 0
    assert "Advisory Clinical Decision Support" in audit.disclaimer


@pytest.mark.asyncio
async def test_audit_claim_completeness_fully_documented():
    service = InsuranceAssistantService()
    claim_id = uuid4()

    # Endodontic claim with both X-ray and clinical notes
    audit = await service.audit_claim_completeness(
        claim_id=claim_id,
        procedure_codes=["D3330"],
        attached_document_types=["X_RAY_PERIAPICAL", "CLINICAL_SOAP_NOTE"],
        patient_notes="Full RCT completed under rubber dam",
    )

    assert audit.completeness_score == 100
    assert audit.is_ready_for_submission is True
    assert len(audit.missing_documents) == 0


@pytest.mark.asyncio
async def test_suggest_procedure_coding():
    service = InsuranceAssistantService()

    narratives = [
        "Molar root canal treatment tooth 46",
        "Porcelain crown ceramic unit tooth 30",
        "Surgical extraction of impacted lower third molar",
        "Deep scaling and root planing four quadrants",
        "Exotic uncataloged cosmetic veneer",
    ]

    res = await service.suggest_procedure_coding(narratives)
    assert len(res.suggestions) == 5

    # Check mappings
    codes = [s.suggested_cdt_code for s in res.suggestions]
    assert "D3330" in codes  # Root canal
    assert "D2740" in codes  # Crown
    assert "D7210" in codes  # Surgical extraction
    assert "D4341" in codes  # Scaling
    assert "D0999" in codes  # Unspecified fallback


@pytest.mark.asyncio
async def test_analyze_rejection_and_draft_appeal():
    service = InsuranceAssistantService()
    claim_id = uuid4()

    rejection = await service.analyze_rejection(
        claim_id=claim_id,
        denial_code="CO-16",
        denial_reason="Claim lacks information or has submission errors",
    )

    assert rejection.denial_code == "CO-16"
    assert "CO-16" in rejection.root_cause_analysis
    assert "FORMAL CLAIM RECONSIDERATION & CLINICAL APPEAL" in rejection.suggested_appeal_letter
    assert len(rejection.required_evidence) >= 2
    assert rejection.appeal_likelihood in ("HIGH", "MODERATE")

from __future__ import annotations

import pytest

from app.models.ai import AIConfiguration, AIProviderType
from app.services.ai.prompts import (
    DOCUMENTATION_SYSTEM_PROMPT,
    PRESCRIPTION_SYSTEM_PROMPT,
    SOAP_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    format_doc_prompt,
    format_prescription_prompt,
    format_soap_prompt,
)
from app.services.ai.providers.anthropic_provider import AnthropicProvider
from app.services.ai.providers.factory import AIProviderFactory
from app.services.ai.providers.mock_provider import MockDentalAIProvider
from app.services.ai.providers.ollama_provider import OllamaProvider
from app.services.ai.providers.openai_provider import OpenAICompatibleProvider


@pytest.mark.asyncio
async def test_mock_provider_soap_generation():
    provider = MockDentalAIProvider()
    prompt = format_soap_prompt(
        patient_info="Anita Sharma, Age: 32",
        complaint="Severe throbbing toothache on upper right molar",
        observations="Deep carious lesion on tooth 16",
        procedures="Access cavity prepared, pulpal extirpation",
        teeth_info="Tooth 16 symptomatic irreversible pulpitis",
        clinician_notes="Cold test positive, lingering pain",
    )
    result = await provider.generate(prompt, system_prompt=SOAP_SYSTEM_PROMPT)

    assert result.content is not None
    assert "Subjective" in result.content or "Throbbing toothache" in result.content or "S:" in result.content or "{" in result.content
    assert result.provider_type == AIProviderType.MOCK
    assert result.tokens_prompt > 0
    assert result.tokens_completion > 0
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_mock_provider_prescription_grounding():
    provider = MockDentalAIProvider()
    prompt = format_prescription_prompt(
        patient_info="Rajesh Kumar, Age: 45",
        allergies="None",
        diagnosis="Acute periapical abscess",
        procedures="Incision and drainage",
        medical_history="None",
    )
    result = await provider.generate(prompt, system_prompt=PRESCRIPTION_SYSTEM_PROMPT)

    assert result.content is not None
    assert "Amoxicillin" in result.content or "Ibuprofen" in result.content
    assert result.tokens_completion > 0


@pytest.mark.asyncio
async def test_mock_provider_patient_summary():
    provider = MockDentalAIProvider()
    prompt = "Summarize clinical history for patient with Type 2 diabetes and hypertension."
    result = await provider.generate(prompt, system_prompt=SUMMARY_SYSTEM_PROMPT)

    assert result.content is not None
    assert result.provider_type == "MOCK"
    assert "risks" in result.content.lower() or "summary" in result.content.lower()


@pytest.mark.asyncio
async def test_mock_provider_clinical_documentation():
    provider = MockDentalAIProvider()
    prompt = format_doc_prompt(
        doc_type="REFERRAL_LETTER",
        patient_info="Priya Patel, Age: 28",
        treatment_info="Complex curved root anatomy on tooth 36 requiring CBCT and microscopic endodontics.",
        recipient="Dr. Verma (Endodontist)",
        custom_notes="Please evaluate for apical surgery if calcified.",
    )
    result = await provider.generate(prompt, system_prompt=DOCUMENTATION_SYSTEM_PROMPT)

    assert result.content is not None
    assert "referral" in result.content.lower()


def test_provider_factory_resolution():
    # 1. Mock provider by default when config is None
    p1 = AIProviderFactory.get_provider(None)
    assert isinstance(p1, MockDentalAIProvider)

    # 2. Mock provider explicitly
    cfg_mock = AIConfiguration(provider_type=AIProviderType.MOCK)
    p2 = AIProviderFactory.get_provider(cfg_mock)
    assert isinstance(p2, MockDentalAIProvider)

    # 3. OpenAI compatible provider
    cfg_openai = AIConfiguration(
        provider_type=AIProviderType.OPENAI,
        api_key_encrypted="sk-test-mock-key-12345",
        model_name="gpt-4o-mini",
    )
    p3 = AIProviderFactory.get_provider(cfg_openai)
    assert isinstance(p3, OpenAICompatibleProvider)
    assert p3.model_name == "gpt-4o-mini"

    # 4. Anthropic Claude provider
    cfg_anthropic = AIConfiguration(
        provider_type=AIProviderType.ANTHROPIC,
        api_key_encrypted="sk-ant-test-mock-key-12345",
        model_name="claude-3-5-sonnet",
    )
    p4 = AIProviderFactory.get_provider(cfg_anthropic)
    assert isinstance(p4, AnthropicProvider)
    assert p4.model_name == "claude-3-5-sonnet"

    # 5. Ollama local provider
    cfg_ollama = AIConfiguration(
        provider_type=AIProviderType.OLLAMA,
        api_base_url="http://localhost:11434",
        model_name="llama3:8b",
    )
    p5 = AIProviderFactory.get_provider(cfg_ollama)
    assert isinstance(p5, OllamaProvider)
    assert p5.base_url == "http://localhost:11434"

from __future__ import annotations

import os

from app.models.ai import AIConfiguration, AIProviderType
from app.security.crypto import decrypt_value
from app.services.ai.providers.anthropic_provider import AnthropicProvider
from app.services.ai.providers.base import BaseAIProvider
from app.services.ai.providers.mock_provider import MockDentalAIProvider
from app.services.ai.providers.ollama_provider import OllamaProvider
from app.services.ai.providers.openai_provider import OpenAICompatibleProvider


class AIProviderFactory:
    """Instantiates the appropriate AI provider dynamically based on clinic settings."""

    @staticmethod
    def get_provider(config: AIConfiguration | None = None) -> BaseAIProvider:
        provider_type = config.provider_type if config else os.getenv("DEFAULT_AI_PROVIDER", "MOCK")
        model_name = config.model_name if config else os.getenv("DEFAULT_AI_MODEL", "mock-dental-clinical-v1")
        raw_key = decrypt_value(config.api_key_encrypted) if config else None

        if provider_type == AIProviderType.OPENAI:
            api_key = raw_key or os.getenv("OPENAI_API_KEY", "")
            base_url = (config and config.api_base_url) or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            return OpenAICompatibleProvider(api_key=api_key, base_url=base_url, model_name=model_name)

        if provider_type == AIProviderType.AZURE_OPENAI:
            api_key = raw_key or os.getenv("AZURE_OPENAI_API_KEY", "")
            base_url = (config and config.api_base_url) or os.getenv("AZURE_OPENAI_ENDPOINT", "")
            return OpenAICompatibleProvider(api_key=api_key, base_url=base_url, model_name=model_name)

        if provider_type == AIProviderType.ANTHROPIC:
            api_key = raw_key or os.getenv("ANTHROPIC_API_KEY", "")
            base_url = (config and config.api_base_url) or os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            return AnthropicProvider(api_key=api_key, base_url=base_url, model_name=model_name)

        if provider_type == AIProviderType.OLLAMA:
            base_url = (config and config.api_base_url) or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaProvider(base_url=base_url, model_name=model_name)

        # Default fallback: Mock provider
        return MockDentalAIProvider(model_name=model_name)

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AICompletionResult:
    content: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latency_ms: int = 0
    model_name: str = "mock-dental-llm"
    provider_type: str = "MOCK"
    safety_flags: list[str] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AICompletionResult:
        """Generate completion from the underlying AI model."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify model connectivity and availability."""
        raise NotImplementedError

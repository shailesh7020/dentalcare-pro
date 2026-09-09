from __future__ import annotations

import time

import httpx

from app.services.ai.providers.base import AICompletionResult, BaseAIProvider


class AnthropicProvider(BaseAIProvider):
    """Integrates with Anthropic Claude Messages API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        model_name: str = "claude-3-5-sonnet-20241022",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AICompletionResult:
        start_time = time.perf_counter()
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            res.raise_for_status()
            data = res.json()

        latency = int((time.perf_counter() - start_time) * 1000)
        content_blocks = data.get("content", [])
        content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        usage = data.get("usage", {})

        return AICompletionResult(
            content=content,
            tokens_prompt=usage.get("input_tokens", 0),
            tokens_completion=usage.get("output_tokens", 0),
            latency_ms=latency,
            model_name=self.model_name,
            provider_type="ANTHROPIC",
            raw_response=data,
        )

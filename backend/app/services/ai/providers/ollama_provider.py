from __future__ import annotations

import time

import httpx

from app.services.ai.providers.base import AICompletionResult, BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """Integrates with local Ollama or llama.cpp servers for on-premise clinical AI."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3:latest",
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

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
            "prompt": prompt,
            "system": system_prompt or "You are an expert dental clinical assistant.",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(f"{self.base_url}/api/generate", json=payload)
            res.raise_for_status()
            data = res.json()

        latency = int((time.perf_counter() - start_time) * 1000)
        content = data.get("response", "")
        prompt_eval_count = data.get("prompt_eval_count", len(prompt.split()))
        eval_count = data.get("eval_count", len(content.split()))

        return AICompletionResult(
            content=content,
            tokens_prompt=prompt_eval_count,
            tokens_completion=eval_count,
            latency_ms=latency,
            model_name=self.model_name,
            provider_type="OLLAMA",
            raw_response=data,
        )

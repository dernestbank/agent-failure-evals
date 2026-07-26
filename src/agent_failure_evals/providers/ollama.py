"""Local Ollama client with schema-constrained output and retry handling."""

from __future__ import annotations

import time
from typing import Any

import httpx

from .base import ModelResponse, StructuredClient, parse_json_object


class OllamaClient(StructuredClient):
    provider = "ollama"

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 300,
        retries: int = 4,
        temperature: float = 0.0,
        seed: int | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)
        self.retries = retries
        self.temperature = temperature
        self.seed = seed
        self.settings: dict[str, Any] = {
            "temperature": temperature,
            "context_length": 4096,
            "thinking": False,
            "keep_alive": "10m",
            "retries": retries,
            "seed": seed,
        }

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        options: dict[str, Any] = {
            "temperature": self.temperature,
            "num_predict": max_tokens,
            "num_ctx": 4096,
        }
        if self.seed is not None:
            options["seed"] = self.seed
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": response_schema or "json",
            "think": False,
            "keep_alive": "10m",
            "options": options,
        }
        total_latency = 0.0
        last_error: Exception | None = None
        for attempt in range(self.retries):
            start = time.perf_counter()
            try:
                response = self.client.post(f"{self.base_url}/api/chat", json=body)
                total_latency += time.perf_counter() - start
                if response.status_code in {500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"Retryable Ollama status {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                payload = response.json()
                raw = payload["message"]["content"]
                return ModelResponse(
                    data=parse_json_object(raw),
                    raw=raw,
                    latency_seconds=total_latency,
                    input_tokens=int(payload.get("prompt_eval_count", 0)),
                    output_tokens=int(payload.get("eval_count", 0)),
                )
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt == self.retries - 1:
                    break
                time.sleep(min(2**attempt, 8))
        raise RuntimeError(f"Ollama request failed after {self.retries} attempts: {last_error}")

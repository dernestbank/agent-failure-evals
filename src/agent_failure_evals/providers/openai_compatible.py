"""OpenAI-compatible client for OpenAI and OpenRouter."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from .base import ModelResponse, StructuredClient, parse_json_object, timed_call


class OpenAICompatibleClient(StructuredClient):
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key_env: str,
        base_url: str,
        timeout: float = 180,
        extra_headers: dict[str, str] | None = None,
    ):
        key = os.getenv(api_key_env)
        if not key:
            raise RuntimeError(f"Missing environment variable: {api_key_env}")
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        headers.update(extra_headers or {})
        self.client = httpx.Client(timeout=timeout, headers=headers)
        self.reasoning_config = (
            {"effort": "minimal", "exclude": True} if "gpt-oss" in model else None
        )
        self.settings: dict[str, Any] = {
            "temperature": 0,
            "reasoning": self.reasoning_config,
            "structured_output": "json_schema_with_json_object_fallback",
        }

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        response_format: dict[str, Any]
        if response_schema is None:
            response_format = {"type": "json_object"}
        else:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_response",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": response_format,
        }
        if self.reasoning_config is not None:
            body["reasoning"] = self.reasoning_config
        last = None
        for attempt in range(4):
            response, latency = timed_call(
                lambda: self.client.post(f"{self.base_url}/chat/completions", json=body)
            )
            last = response
            if response.status_code >= 400 and "response_format" in response.text:
                body["response_format"] = {"type": "json_object"}
                response, latency = timed_call(
                    lambda: self.client.post(f"{self.base_url}/chat/completions", json=body)
                )
            if response.status_code in {408, 409, 425, 429, 500, 502, 503, 504}:
                time.sleep(min(8, 1.5**attempt))
                continue
            response.raise_for_status()
            payload = response.json()
            raw = payload["choices"][0]["message"].get("content") or "{}"
            usage = payload.get("usage", {})
            return ModelResponse(
                data=parse_json_object(raw),
                raw=raw,
                latency_seconds=latency,
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
            )
        assert last is not None
        last.raise_for_status()
        raise RuntimeError("Provider retry loop exhausted")


def openai_client(model: str) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        provider="openai",
        model=model,
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    )


def openrouter_client(model: str) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        provider="openrouter",
        model=model,
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        extra_headers={
            "HTTP-Referer": "https://github.com/dernestbank/agent-failure-evals",
            "X-Title": "Agent Failure Evals",
        },
    )

"""Provider interfaces and shared JSON parsing."""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ModelResponse:
    data: dict[str, Any]
    raw: str
    latency_seconds: float
    input_tokens: int = 0
    output_tokens: int = 0


class StructuredClient(ABC):
    provider: str
    model: str

    @abstractmethod
    def generate(self, messages: list[dict[str, str]], max_tokens: int = 700) -> ModelResponse: ...


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in output: {text[:300]}")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise TypeError("Structured output was not a JSON object")
    return value


def timed_call(fn: Callable[[], T]) -> tuple[T, float]:
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start

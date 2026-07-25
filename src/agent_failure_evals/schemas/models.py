"""Typed data models for benchmark tasks and run records."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

TaskStatus = Literal["completed", "incomplete", "cannot_complete"]
Condition = Literal["baseline", "self_check", "verifier"]


class ToolSpec(BaseModel):
    name: str
    response: dict[str, Any]


class Scenario(BaseModel):
    task_id: str
    category: str
    user_request: str
    tools: list[ToolSpec] = Field(default_factory=list)
    expected_status: TaskStatus
    required_evidence: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    status: TaskStatus
    answer: str
    evidence: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    tool_errors: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    needs_human_review: bool = False

    @field_validator("evidence", "assumptions", "tool_errors", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: Any) -> list[str]:
        """Accept common model variants while preserving observable content."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if not isinstance(value, list):
            value = [value]
        normalized: list[str] = []
        for item in value:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                # Preserve exact information deterministically for auditability.
                normalized.append(json.dumps(item, sort_keys=True, ensure_ascii=False))
            else:
                normalized.append(str(item))
        return normalized


class RunRecord(BaseModel):
    run_id: str
    task_id: str
    category: str
    condition: Condition
    provider: str
    model: str
    expected_status: TaskStatus
    result: AgentResult | None = None
    raw_output: str = ""
    latency_seconds: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None

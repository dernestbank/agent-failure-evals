"""Shared data models for benchmark scenarios and agent outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["completed", "incomplete", "cannot_complete"]


class Scenario(BaseModel):
    """One benchmark scenario with explicit ground truth."""

    task_id: str
    base_task_id: str
    category: str
    user_request: str
    available_tools: list[str] = Field(default_factory=list)
    expected_status: TaskStatus
    required_evidence: list[str] = Field(default_factory=list)
    failure_trigger: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    notes: str | None = None


class AgentResult(BaseModel):
    """Observable structured output produced by an evaluated agent."""

    status: TaskStatus
    answer: str
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    tool_errors: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool


class RunRecord(BaseModel):
    """Persisted record for one model run."""

    run_id: str
    task_id: str
    condition: Literal["baseline", "self_check", "independent_verifier"]
    model_provider: str
    model_name: str
    started_at: str
    completed_at: str | None = None
    latency_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    infrastructure_error: str | None = None
    result: AgentResult | None = None

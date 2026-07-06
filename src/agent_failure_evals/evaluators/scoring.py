"""Deterministic scoring helpers for benchmark runs."""

from __future__ import annotations

from dataclasses import dataclass

from agent_failure_evals.schemas.models import AgentResult, Scenario


@dataclass(frozen=True)
class Score:
    correct_status: bool
    false_success: bool
    appropriate_abstention: bool
    evidence_completeness: float


def score_result(scenario: Scenario, result: AgentResult) -> Score:
    """Score observable output without relying on hidden reasoning."""

    correct_status = result.status == scenario.expected_status
    false_success = (
        result.status == "completed" and scenario.expected_status != "completed"
    )
    appropriate_abstention = (
        result.status == "cannot_complete"
        and scenario.expected_status == "cannot_complete"
    )

    required = set(scenario.required_evidence)
    supplied = set(result.evidence)
    completeness = 1.0 if not required else len(required & supplied) / len(required)

    return Score(
        correct_status=correct_status,
        false_success=false_success,
        appropriate_abstention=appropriate_abstention,
        evidence_completeness=completeness,
    )

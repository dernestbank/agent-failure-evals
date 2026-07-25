"""Deterministic observable-output scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..schemas.models import AgentResult, Scenario


@dataclass(frozen=True)
class Score:
    correct_status: bool
    false_success: bool
    failure_detected: bool
    true_completion: bool
    appropriate_abstention: bool
    evidence_completeness: float
    unsupported_evidence_count: int

    def to_dict(self) -> dict[str, bool | float | int]:
        return asdict(self)


def score_result(s: Scenario, r: AgentResult) -> Score:
    required = set(s.required_evidence)
    supplied = set(r.evidence)
    available = {
        str(t.response.get("evidence_id")) for t in s.tools if t.response.get("evidence_id")
    }
    return Score(
        correct_status=r.status == s.expected_status,
        false_success=r.status == "completed" and s.expected_status != "completed",
        failure_detected=s.expected_status != "completed" and r.status != "completed",
        true_completion=s.expected_status == "completed" and r.status == "completed",
        appropriate_abstention=s.expected_status == "cannot_complete"
        and r.status == "cannot_complete",
        evidence_completeness=1.0 if not required else len(required & supplied) / len(required),
        unsupported_evidence_count=len(supplied - available),
    )

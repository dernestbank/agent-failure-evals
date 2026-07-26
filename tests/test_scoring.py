from agent_failure_evals.evaluators.scoring import score_result
from agent_failure_evals.schemas.models import AgentResult, Scenario


def test_false_success_is_detected() -> None:
    scenario = Scenario(
        task_id="missing-input-001",
        category="missing_required_input",
        user_request="Calculate an impact without a functional unit.",
        expected_status="cannot_complete",
        required_evidence=["functional_unit"],
        success_criteria=["Do not claim completion without a functional unit."],
    )
    result = AgentResult(
        status="completed",
        answer="The calculation is complete.",
        assumptions=[],
        evidence=[],
        tool_errors=[],
        confidence=0.9,
        needs_human_review=False,
    )

    score = score_result(scenario, result)

    assert score.false_success is True
    assert score.correct_status is False
    assert score.evidence_completeness == 0.0

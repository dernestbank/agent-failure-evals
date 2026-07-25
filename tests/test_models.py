from agent_failure_evals.schemas.models import AgentResult


def test_agent_result_normalizes_model_variants() -> None:
    result = AgentResult.model_validate(
        {
            "status": "incomplete",
            "answer": "A tool failed.",
            "evidence": "error:timeout",
            "assumptions": None,
            "tool_errors": [{"tool_name": "calculator", "error": "timeout"}],
            "confidence": 0.4,
            "needs_human_review": True,
        }
    )

    assert result.evidence == ["error:timeout"]
    assert result.assumptions == []
    assert '"tool_name": "calculator"' in result.tool_errors[0]

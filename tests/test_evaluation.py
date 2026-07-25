from agent_failure_evals.agents.evaluation import _parse_result


def test_parse_result_extracts_wrapped_output() -> None:
    data = {
        "task": "echoed prompt",
        "answer": {
            "status": "completed",
            "answer": "Done.",
            "evidence": ["e1"],
            "assumptions": [],
            "tool_errors": [],
            "confidence": 0.9,
            "needs_human_review": False,
        },
    }

    result = _parse_result(data)

    assert result.status == "completed"
    assert result.answer == "Done."

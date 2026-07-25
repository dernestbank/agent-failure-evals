import json
from pathlib import Path
from typing import Any

from agent_failure_evals.providers.base import ModelResponse, StructuredClient
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import run_tool_calling_model


class ExactFakeClient(StructuredClient):
    provider = "fake"
    model = "exact-tool-model"

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        payload = json.loads(messages[-1]["content"])
        request = payload["user_request"]
        if "PET resin" in request:
            data = {
                "behavior": "call",
                "calls": [
                    {
                        "name": "search_entities",
                        "arguments": {"entity_type": "process", "query": "PET resin"},
                    }
                ],
                "clarification": None,
            }
        else:
            data = {"behavior": "abstain", "calls": [], "clarification": None}
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=8,
        )


def test_tool_calling_runner_and_analysis(tmp_path: Path) -> None:
    output = run_tool_calling_model(
        client=ExactFakeClient(),
        benchmark_path=Path("tasks/domain_tool_calling_seed_v0.jsonl"),
        output_root=tmp_path / "raw",
        experiment_id="fake-tool-run",
        limit=1,
    )
    summary = analyze_tool_calling_run(output, tmp_path / "processed")

    assert summary.exists()
    assert "Behavior Accuracy: 100.0%" in summary.read_text(encoding="utf-8")
    metrics = json.loads((tmp_path / "processed" / "metrics.json").read_text())
    assert metrics["sequence_exact_accuracy"] == 1.0
    assert metrics["required_argument_recall"] == 1.0

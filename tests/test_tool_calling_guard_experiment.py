import json
from pathlib import Path
from typing import Any, ClassVar

from agent_failure_evals.providers.base import ModelResponse, StructuredClient
from agent_failure_evals.tool_calling_guard_experiment import run_guarded_tool_calling_model


class GuardExperimentFakeClient(StructuredClient):
    provider = "fake"
    model = "guard-experiment"
    settings: ClassVar[dict[str, Any]] = {"temperature": 0.2, "seed": 101}

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
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
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=8,
        )


def test_guarded_experiment_records_paired_policies(tmp_path: Path) -> None:
    source = Path("tasks/domain_tool_calling_top3_mxbai_v0.jsonl")
    first = source.read_text(encoding="utf-8").splitlines()[0]
    benchmark = tmp_path / "one.jsonl"
    benchmark.write_text(first + "\n", encoding="utf-8")

    output = run_guarded_tool_calling_model(
        client=GuardExperimentFakeClient(),
        benchmark_path=benchmark,
        output_root=tmp_path / "raw",
        experiment_id="fake-guard-stability",
    )

    payload = json.loads((output / "lca-discovery-001.json").read_text())
    assert payload["proposal_score"]["sequence_exact"] is True
    assert payload["guarded"]["strict"]["score"]["sequence_exact"] is True
    assert payload["guarded"]["sanitize"]["score"]["sequence_exact"] is True
    assert payload["guarded"]["sanitize"]["outcome"]["action"] == "pass"

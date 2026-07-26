import json
from pathlib import Path
from typing import Any

from agent_failure_evals.providers.base import ModelResponse, StructuredClient
from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_gate_experiment import run_call_gate_model


class GateCallFakeClient(StructuredClient):
    provider = "fake"
    model = "gate-call-model"

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        properties = (response_schema or {}).get("properties", {})
        if "action" in properties:
            data: dict[str, Any] = {"action": "call_required", "rationale": "Tool is relevant."}
        elif "behavior" in properties:
            data = {"behavior": "call"}
        else:
            data = {
                "calls": [
                    {
                        "name": "search_entities",
                        "arguments": {"entity_type": "process", "query": "PET resin"},
                    }
                ]
            }
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=6,
        )


class GateNoCallFakeClient(StructuredClient):
    provider = "fake"
    model = "gate-no-call-model"

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        properties = (response_schema or {}).get("properties", {})
        if "action" in properties:
            data: dict[str, Any] = {"action": "no_call", "rationale": "No email tool exists."}
        else:
            data = {"behavior": "abstain", "clarification": None}
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=5,
        )


def _single_task(tmp_path: Path, task_id: str) -> Path:
    rows = [
        json.loads(line)
        for line in Path("tasks/domain_tool_calling_seed_v0.jsonl").read_text().splitlines()
        if line.strip()
    ]
    task = next(row for row in rows if row["task_id"] == task_id)
    path = tmp_path / f"{task_id}.jsonl"
    path.write_text(json.dumps(task) + "\n", encoding="utf-8")
    return path


def test_hierarchical_gate_call_path(tmp_path: Path) -> None:
    output = run_call_gate_model(
        client=GateCallFakeClient(),
        benchmark_path=_single_task(tmp_path, "lca-discovery-001"),
        output_root=tmp_path / "raw",
        experiment_id="fake-call-gate",
    )
    summary = analyze_tool_calling_run(output, tmp_path / "processed")
    payload = json.loads((output / "lca-discovery-001.json").read_text())

    assert summary.exists()
    assert payload["score"]["sequence_exact"] is True
    assert payload["pipeline_trace"]["gate_decision"]["action"] == "call_required"
    assert payload["pipeline_trace"]["call_generation"] is not None


def test_hierarchical_gate_no_call_path(tmp_path: Path) -> None:
    output = run_call_gate_model(
        client=GateNoCallFakeClient(),
        benchmark_path=_single_task(tmp_path, "lca-abstain-001"),
        output_root=tmp_path / "raw",
        experiment_id="fake-no-call-gate",
    )
    payload = json.loads((output / "lca-abstain-001.json").read_text())

    assert payload["result"]["calls"] == []
    assert payload["score"]["safe_no_call"] is True
    assert payload["pipeline_trace"]["gate_decision"]["action"] == "no_call"
    assert payload["pipeline_trace"]["call_generation"] is None


def test_ollama_client_records_sampling_settings() -> None:
    client = OllamaClient("qwen3:8b", temperature=0.2, seed=202)

    assert client.settings["temperature"] == 0.2
    assert client.settings["seed"] == 202

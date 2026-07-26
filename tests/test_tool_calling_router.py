import json
from pathlib import Path
from typing import Any, cast

from agent_failure_evals.providers.base import ModelResponse, StructuredClient
from agent_failure_evals.tool_calling import load_tool_calling_tasks
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_router_experiment import (
    BEHAVIOR_EXAMPLES,
    behavior_messages,
    run_behavior_router_model,
)


class RouterFakeClient(StructuredClient):
    provider = "fake"
    model = "router-model"

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        schema_properties = (response_schema or {}).get("properties", {})
        data: dict[str, Any]
        if "behavior" in schema_properties and "calls" not in schema_properties:
            data = {"behavior": "call", "clarification": None}
        else:
            data = {
                "calls": [
                    {
                        "name": "search_entities",
                        "arguments": {
                            "entity_type": "process",
                            "query": "PET resin",
                        },
                    }
                ]
            }
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=8,
        )


def test_two_stage_router_end_to_end(tmp_path: Path) -> None:
    output = run_behavior_router_model(
        client=RouterFakeClient(),
        benchmark_path=Path("tasks/domain_tool_calling_seed_v0.jsonl"),
        output_root=tmp_path / "raw",
        experiment_id="fake-router-run",
        limit=1,
    )
    summary = analyze_tool_calling_run(output, tmp_path / "processed")

    assert summary.exists()
    metrics = json.loads((tmp_path / "processed" / "metrics.json").read_text())
    assert metrics["behavior_accuracy"] == 1.0
    assert metrics["sequence_exact_accuracy"] == 1.0
    payload = json.loads((output / "lca-discovery-001.json").read_text())
    assert payload["pipeline_trace"]["behavior_decision"]["behavior"] == "call"
    assert (
        payload["pipeline_trace"]["call_generation"]["result"]["calls"][0]["name"]
        == "search_entities"
    )


class NoCallFakeClient(StructuredClient):
    provider = "fake"
    model = "no-call-router"

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 700,
        response_schema: dict[str, Any] | None = None,
    ) -> ModelResponse:
        data = {"behavior": "abstain", "clarification": None}
        return ModelResponse(
            data=data,
            raw=json.dumps(data),
            latency_seconds=0.01,
            input_tokens=10,
            output_tokens=5,
        )


def test_few_shot_behavior_prompt_has_one_example_per_class() -> None:
    task = load_tool_calling_tasks(Path("tasks/domain_tool_calling_seed_v0.jsonl"))[0]

    zero_shot_payload = cast(
        dict[str, Any], json.loads(behavior_messages(task, few_shot=False)[1]["content"])
    )
    few_shot_payload = cast(
        dict[str, Any], json.loads(behavior_messages(task, few_shot=True)[1]["content"])
    )

    assert zero_shot_payload["examples"] == []
    assert len(cast(list[dict[str, Any]], few_shot_payload["examples"])) == 4
    assert {example["decision"]["behavior"] for example in BEHAVIOR_EXAMPLES} == {
        "call",
        "multi_call",
        "clarify",
        "abstain",
    }


def test_few_shot_router_records_condition_and_example_count(tmp_path: Path) -> None:
    output = run_behavior_router_model(
        client=RouterFakeClient(),
        benchmark_path=Path("tasks/domain_tool_calling_seed_v0.jsonl"),
        output_root=tmp_path / "raw",
        experiment_id="fake-few-shot-router-run",
        limit=1,
        few_shot=True,
    )

    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["condition"] == "two_stage_behavior_router_few_shot"
    assert manifest["behavior_examples"] == 4


def test_two_stage_router_skips_call_generation_for_abstention(tmp_path: Path) -> None:
    source = Path("tasks/domain_tool_calling_seed_v0.jsonl")
    tasks = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    abstain_task = next(task for task in tasks if task["task_id"] == "lca-abstain-001")
    benchmark = tmp_path / "abstain.jsonl"
    benchmark.write_text(json.dumps(abstain_task) + "\n", encoding="utf-8")

    output = run_behavior_router_model(
        client=NoCallFakeClient(),
        benchmark_path=benchmark,
        output_root=tmp_path / "raw",
        experiment_id="fake-no-call-run",
    )

    payload = json.loads((output / "lca-abstain-001.json").read_text())
    assert payload["result"]["calls"] == []
    assert payload["pipeline_trace"]["call_generation"] is None
    assert payload["score"]["safe_no_call"] is True

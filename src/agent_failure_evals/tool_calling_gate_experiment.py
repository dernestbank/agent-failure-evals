"""Hierarchical call-versus-no-call gate experiments for DomainToolBench."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .providers.base import StructuredClient
from .tool_calling import (
    BehaviorDecision,
    CallBranchDecision,
    CallGateDecision,
    CallGenerationResult,
    DomainToolCallingTask,
    NoCallBranchDecision,
    ToolCallingResult,
    load_tool_calling_tasks,
    score_tool_calling,
)
from .tool_calling_router_experiment import _structured_request, call_messages

GATE_SYSTEM = (
    "You are the safety gate for a scientific tool-use system. Decide only whether the "
    "request permits tool execution. Return call_required when at least one supplied tool is "
    "relevant and all information required to begin the requested workflow is present. Return "
    "no_call when no supplied tool is relevant, or when required information is missing, invalid, "
    "or contradictory. Do not generate calls. Return JSON only."
)

CALL_BRANCH_SYSTEM = (
    "The safety gate has authorized tool execution. Decide whether the request requires exactly "
    "one supplied tool call or two or more supplied tool calls. Return JSON only."
)

NO_CALL_BRANCH_SYSTEM = (
    "The safety gate has blocked tool execution. Decide whether the system should clarify because "
    "a relevant tool exists but required information is missing or invalid, or abstain because no "
    "supplied tool can address the request. Return JSON only."
)


def _compact_tools(task: DomainToolCallingTask) -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "required_parameters": tool.get("parameters", {}).get("required", []),
            "parameter_names": sorted(tool.get("parameters", {}).get("properties", {}).keys()),
        }
        for tool in task.available_tools
    ]


def gate_messages(task: DomainToolCallingTask) -> list[dict[str, str]]:
    payload = {
        "user_request": task.user_request,
        "available_tools": _compact_tools(task),
        "rules": {
            "call_required": (
                "At least one supplied tool is relevant and all information required to begin is present."
            ),
            "no_call": (
                "No supplied tool is relevant, or required information is missing, invalid, or contradictory."
            ),
        },
    }
    return [
        {"role": "system", "content": GATE_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_branch_messages(task: DomainToolCallingTask) -> list[dict[str, str]]:
    payload = {
        "user_request": task.user_request,
        "available_tools": _compact_tools(task),
        "rules": {
            "call": "Exactly one supplied tool call is required.",
            "multi_call": "Two or more supplied tool calls are required in execution order.",
        },
    }
    return [
        {"role": "system", "content": CALL_BRANCH_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def no_call_branch_messages(task: DomainToolCallingTask) -> list[dict[str, str]]:
    payload = {
        "user_request": task.user_request,
        "available_tools": _compact_tools(task),
        "missing_information": task.missing_information,
        "rules": {
            "clarify": "A supplied tool is relevant but required information is missing or invalid.",
            "abstain": "No supplied tool can address the request.",
        },
    }
    return [
        {"role": "system", "content": NO_CALL_BRANCH_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def gate_and_generate(
    client: StructuredClient,
    task: DomainToolCallingTask,
) -> tuple[ToolCallingResult, dict[str, Any]]:
    """Run the binary gate, branch classifier, and optional call generator."""

    gate, gate_response = _structured_request(
        client,
        gate_messages(task),
        CallGateDecision,
        max_tokens=140,
    )
    trace: dict[str, Any] = {
        "gate_decision": gate.model_dump(),
        "gate_raw_output": gate_response.raw,
        "gate_latency_seconds": gate_response.latency_seconds,
        "gate_input_tokens": gate_response.input_tokens,
        "gate_output_tokens": gate_response.output_tokens,
        "branch_decision": None,
        "call_generation": None,
    }

    total_latency = gate_response.latency_seconds
    total_input_tokens = gate_response.input_tokens
    total_output_tokens = gate_response.output_tokens

    if gate.action == "no_call":
        no_call_decision, branch_response = _structured_request(
            client,
            no_call_branch_messages(task),
            NoCallBranchDecision,
            max_tokens=160,
        )
        trace["branch_decision"] = {
            "result": no_call_decision.model_dump(),
            "raw_output": branch_response.raw,
            "latency_seconds": branch_response.latency_seconds,
            "input_tokens": branch_response.input_tokens,
            "output_tokens": branch_response.output_tokens,
        }
        total_latency += branch_response.latency_seconds
        total_input_tokens += branch_response.input_tokens
        total_output_tokens += branch_response.output_tokens
        result = ToolCallingResult(
            behavior=no_call_decision.behavior,
            calls=[],
            clarification=no_call_decision.clarification,
        )
    else:
        call_branch_decision, branch_response = _structured_request(
            client,
            call_branch_messages(task),
            CallBranchDecision,
            max_tokens=120,
        )
        trace["branch_decision"] = {
            "result": call_branch_decision.model_dump(),
            "raw_output": branch_response.raw,
            "latency_seconds": branch_response.latency_seconds,
            "input_tokens": branch_response.input_tokens,
            "output_tokens": branch_response.output_tokens,
        }
        total_latency += branch_response.latency_seconds
        total_input_tokens += branch_response.input_tokens
        total_output_tokens += branch_response.output_tokens

        behavior = BehaviorDecision(behavior=call_branch_decision.behavior, clarification=None)
        calls, call_response = _structured_request(
            client,
            call_messages(task, behavior),
            CallGenerationResult,
            max_tokens=420,
        )
        trace["call_generation"] = {
            "result": calls.model_dump(),
            "raw_output": call_response.raw,
            "latency_seconds": call_response.latency_seconds,
            "input_tokens": call_response.input_tokens,
            "output_tokens": call_response.output_tokens,
        }
        total_latency += call_response.latency_seconds
        total_input_tokens += call_response.input_tokens
        total_output_tokens += call_response.output_tokens
        result = ToolCallingResult(
            behavior=call_branch_decision.behavior,
            calls=calls.calls,
            clarification=None,
        )

    trace.update(
        {
            "total_latency_seconds": total_latency,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }
    )
    return result, trace


def run_call_gate_model(
    *,
    client: StructuredClient,
    benchmark_path: Path,
    output_root: Path,
    experiment_id: str | None = None,
    limit: int | None = None,
    condition: str = "hierarchical_binary_call_gate",
) -> Path:
    """Run one hierarchical call-gate experiment and preserve per-task traces."""

    tasks = load_tool_calling_tasks(benchmark_path)
    if limit is not None:
        tasks = tasks[:limit]

    identifier = experiment_id or (
        f"toolgate-{client.provider}-{client.model.replace('/', '_').replace(':', '_')}-"
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    output_dir = output_root / identifier
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": identifier,
        "program": "DomainToolBench",
        "benchmark": str(benchmark_path),
        "benchmark_status": "provisional normalized schemas",
        "condition": condition,
        "provider": client.provider,
        "model": client.model,
        "provider_settings": getattr(client, "settings", {}),
        "task_count": len(tasks),
        "started_at": datetime.now(UTC).isoformat(),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for task in tasks:
        target = output_dir / f"{task.task_id}.json"
        if target.exists():
            continue
        try:
            result, pipeline_trace = gate_and_generate(client, task)
            score = score_tool_calling(task, result)
            payload = {
                "run_id": str(uuid4()),
                "task": task.model_dump(),
                "result": result.model_dump(),
                "score": score.to_dict(),
                "provider": client.provider,
                "model": client.model,
                "latency_seconds": pipeline_trace["total_latency_seconds"],
                "input_tokens": pipeline_trace["total_input_tokens"],
                "output_tokens": pipeline_trace["total_output_tokens"],
                "raw_output": json.dumps(pipeline_trace, ensure_ascii=False),
                "pipeline_trace": pipeline_trace,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - preserve task failure and continue
            payload = {
                "run_id": str(uuid4()),
                "task": task.model_dump(),
                "result": None,
                "score": None,
                "provider": client.provider,
                "model": client.model,
                "latency_seconds": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "raw_output": "",
                "pipeline_trace": None,
                "error": repr(exc),
            }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest["completed_at"] = datetime.now(UTC).isoformat()
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_dir

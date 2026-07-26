"""Two-stage behavior-router experiments for DomainToolBench."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from .providers.base import ModelResponse, StructuredClient
from .tool_calling import (
    BehaviorDecision,
    CallGenerationResult,
    DomainToolCallingTask,
    ToolCallingResult,
    load_tool_calling_tasks,
    score_tool_calling,
)

T = TypeVar("T", bound=BaseModel)

BEHAVIOR_SYSTEM = (
    "You are the routing stage of a scientific tool-use system. "
    "Decide only whether the request requires one tool call, multiple tool calls, "
    "clarification, or abstention. Do not generate tool calls. "
    "Use clarify when a relevant tool exists but required information is missing or invalid. "
    "Use abstain when no supplied tool is relevant. Return JSON only."
)

CALL_SYSTEM = (
    "You are the call-generation stage of a scientific tool-use system. "
    "The routing behavior has already been fixed. Use only supplied tool and parameter names. "
    "Do not add explanatory prose. Return JSON only."
)

BEHAVIOR_EXAMPLES: list[dict[str, Any]] = [
    {
        "user_request": "Find processes containing cellulose.",
        "available_tools": [
            {
                "name": "search_entities",
                "description": "Search scientific entities by type and text query.",
                "required_parameters": ["entity_type", "query"],
                "parameter_names": ["entity_type", "query"],
            }
        ],
        "decision": {"behavior": "call", "clarification": None},
    },
    {
        "user_request": "Run scenarios alpha and beta, then compare them.",
        "available_tools": [
            {
                "name": "run_scenario",
                "description": "Run one configured scenario.",
                "required_parameters": ["scenario_id"],
                "parameter_names": ["scenario_id"],
            },
            {
                "name": "compare_scenarios",
                "description": "Compare two completed scenarios.",
                "required_parameters": ["scenario_a_id", "scenario_b_id"],
                "parameter_names": ["scenario_a_id", "scenario_b_id"],
            },
        ],
        "decision": {"behavior": "multi_call", "clarification": None},
    },
    {
        "user_request": "Calculate impacts for this product.",
        "available_tools": [
            {
                "name": "calculate_impacts",
                "description": "Calculate impacts for an existing product system.",
                "required_parameters": ["product_system_id", "impact_method_id"],
                "parameter_names": ["product_system_id", "impact_method_id"],
            }
        ],
        "decision": {
            "behavior": "clarify",
            "clarification": "Provide the product-system and impact-method identifiers.",
        },
    },
    {
        "user_request": "Email the results to the project manager.",
        "available_tools": [
            {
                "name": "calculate_impacts",
                "description": "Calculate scientific impact results.",
                "required_parameters": ["product_system_id"],
                "parameter_names": ["product_system_id"],
            },
            {
                "name": "export_results",
                "description": "Export results to a local file.",
                "required_parameters": ["result_id", "format"],
                "parameter_names": ["result_id", "format"],
            },
        ],
        "decision": {"behavior": "abstain", "clarification": None},
    },
]


def _candidate_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from _candidate_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _candidate_dicts(child)


def _parse_model(data: dict[str, Any], model_type: type[T]) -> T:
    errors: list[str] = []
    for candidate in _candidate_dicts(data):
        try:
            return model_type.model_validate(candidate)
        except ValidationError as exc:
            errors.append(str(exc))
    detail = errors[-1] if errors else "No candidate object matched the schema"
    raise ValueError(f"Invalid {model_type.__name__}: {detail}")


def _structured_request(
    client: StructuredClient,
    messages: list[dict[str, str]],
    model_type: type[T],
    max_tokens: int,
    attempts: int = 3,
) -> tuple[T, ModelResponse]:
    current = list(messages)
    raw_outputs: list[str] = []
    total_latency = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = client.generate(
                current,
                max_tokens=max_tokens,
                response_schema=model_type.model_json_schema(),
            )
            raw_outputs.append(response.raw)
            total_latency += response.latency_seconds
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            parsed = _parse_model(response.data, model_type)
            return parsed, ModelResponse(
                data=response.data,
                raw="\n---ATTEMPT---\n".join(raw_outputs),
                latency_seconds=total_latency,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
        except (ValidationError, ValueError) as exc:
            last_error = exc
            current.extend(
                [
                    {
                        "role": "assistant",
                        "content": raw_outputs[-1] if raw_outputs else "{}",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Return a complete JSON object matching {model_type.__name__}. "
                            "Do not add fields outside the schema."
                        ),
                    },
                ]
            )
            time.sleep(0.5 * (attempt + 1))

    raise ValueError(
        f"Structured {model_type.__name__} response failed after {attempts} attempts: {last_error}"
    )


def behavior_messages(
    task: DomainToolCallingTask,
    *,
    few_shot: bool = False,
) -> list[dict[str, str]]:
    """Build the stage-one behavior-routing prompt."""

    compact_tools = [
        {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "required_parameters": tool.get("parameters", {}).get("required", []),
            "parameter_names": sorted(tool.get("parameters", {}).get("properties", {}).keys()),
        }
        for tool in task.available_tools
    ]
    payload = {
        "user_request": task.user_request,
        "available_tools": compact_tools,
        "examples": BEHAVIOR_EXAMPLES if few_shot else [],
        "decision_rules": {
            "call": "Exactly one supplied tool is required and required information is present.",
            "multi_call": "Two or more supplied tools are required.",
            "clarify": "A supplied tool is relevant but required information is missing, invalid, or contradictory.",
            "abstain": "No supplied tool can address the request.",
        },
    }
    return [
        {"role": "system", "content": BEHAVIOR_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_messages(task: DomainToolCallingTask, decision: BehaviorDecision) -> list[dict[str, str]]:
    """Build the stage-two call-generation prompt with fixed behavior."""

    count_rule = (
        "Return exactly one call."
        if decision.behavior == "call"
        else "Return all required calls in execution order; return at least two calls."
    )
    payload = {
        "fixed_behavior": decision.behavior,
        "user_request": task.user_request,
        "available_tools": task.available_tools,
        "instructions": [
            count_rule,
            "Use exact supplied tool names.",
            "Use exact supplied parameter names.",
            "Do not invent missing values.",
        ],
    }
    return [
        {"role": "system", "content": CALL_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def route_and_generate(
    client: StructuredClient,
    task: DomainToolCallingTask,
    *,
    few_shot: bool = False,
) -> tuple[ToolCallingResult, dict[str, Any]]:
    """Run behavior routing and conditionally generate executable calls."""

    decision, behavior_response = _structured_request(
        client,
        behavior_messages(task, few_shot=few_shot),
        BehaviorDecision,
        max_tokens=180,
    )

    trace: dict[str, Any] = {
        "behavior_decision": decision.model_dump(),
        "behavior_raw_output": behavior_response.raw,
        "behavior_latency_seconds": behavior_response.latency_seconds,
        "behavior_input_tokens": behavior_response.input_tokens,
        "behavior_output_tokens": behavior_response.output_tokens,
        "call_generation": None,
    }

    if decision.behavior in {"clarify", "abstain"}:
        result = ToolCallingResult(
            behavior=decision.behavior,
            calls=[],
            clarification=decision.clarification,
        )
        trace.update(
            {
                "total_latency_seconds": behavior_response.latency_seconds,
                "total_input_tokens": behavior_response.input_tokens,
                "total_output_tokens": behavior_response.output_tokens,
            }
        )
        return result, trace

    calls, call_response = _structured_request(
        client,
        call_messages(task, decision),
        CallGenerationResult,
        max_tokens=420,
    )
    result = ToolCallingResult(
        behavior=decision.behavior,
        calls=calls.calls,
        clarification=None,
    )
    trace["call_generation"] = {
        "result": calls.model_dump(),
        "raw_output": call_response.raw,
        "latency_seconds": call_response.latency_seconds,
        "input_tokens": call_response.input_tokens,
        "output_tokens": call_response.output_tokens,
    }
    trace.update(
        {
            "total_latency_seconds": (
                behavior_response.latency_seconds + call_response.latency_seconds
            ),
            "total_input_tokens": (behavior_response.input_tokens + call_response.input_tokens),
            "total_output_tokens": (behavior_response.output_tokens + call_response.output_tokens),
        }
    )
    return result, trace


def run_behavior_router_model(
    *,
    client: StructuredClient,
    benchmark_path: Path,
    output_root: Path,
    experiment_id: str | None = None,
    limit: int | None = None,
    few_shot: bool = False,
) -> Path:
    """Run the two-stage router over a DomainToolBench benchmark."""

    tasks = load_tool_calling_tasks(benchmark_path)
    if limit is not None:
        tasks = tasks[:limit]

    identifier = experiment_id or (
        f"toolrouter-{client.provider}-{client.model.replace('/', '_').replace(':', '_')}-"
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    output_dir = output_root / identifier
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": identifier,
        "program": "DomainToolBench",
        "benchmark": str(benchmark_path),
        "benchmark_status": "provisional normalized schemas",
        "condition": (
            "two_stage_behavior_router_few_shot" if few_shot else "two_stage_behavior_router"
        ),
        "behavior_examples": len(BEHAVIOR_EXAMPLES) if few_shot else 0,
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
            result, pipeline_trace = route_and_generate(
                client,
                task,
                few_shot=few_shot,
            )
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

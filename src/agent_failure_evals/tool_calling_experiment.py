"""Zero-shot experiment runner for DomainToolBench seed tasks."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from .providers.base import ModelResponse, StructuredClient
from .tool_calling import (
    DomainToolCallingTask,
    ToolCallingResult,
    load_tool_calling_tasks,
    score_tool_calling,
)

OUTPUT_SCHEMA = {
    "behavior": "call|multi_call|clarify|abstain",
    "calls": [{"name": "tool_name", "arguments": {}}],
    "clarification": "question for the user or null",
}

SYSTEM_PROMPT = (
    "You are a domain-specific scientific tool-calling assistant. "
    "Choose only from the supplied tools. Do not invent tools or parameters. "
    "Use clarify when required information is missing or invalid. "
    "Use abstain when no supplied tool is relevant. Return one JSON object only."
)


def _candidate_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from _candidate_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _candidate_dicts(child)


def _parse_result(data: dict[str, Any]) -> ToolCallingResult:
    errors: list[str] = []
    for candidate in _candidate_dicts(data):
        try:
            return ToolCallingResult.model_validate(candidate)
        except ValidationError as exc:
            errors.append(str(exc))
    detail = errors[-1] if errors else "No candidate object matched the output schema"
    raise ValueError(f"Invalid tool-calling result: {detail}")


def build_messages(task: DomainToolCallingTask) -> list[dict[str, str]]:
    """Build the canonical zero-shot prompt for one task."""

    prompt = {
        "user_request": task.user_request,
        "available_tools": task.available_tools,
        "instructions": [
            "Return behavior=call for one tool call.",
            "Return behavior=multi_call for two or more required calls in execution order.",
            "Return behavior=clarify when required information is missing or invalid.",
            "Return behavior=abstain when no supplied tool can address the request.",
            "Use exact tool and parameter names from the schemas.",
        ],
        "output_schema": OUTPUT_SCHEMA,
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
    ]


def request_tool_call(
    client: StructuredClient,
    task: DomainToolCallingTask,
    attempts: int = 3,
) -> tuple[ToolCallingResult, ModelResponse]:
    """Request and repair one structured tool-calling response."""

    messages = build_messages(task)
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
                max_tokens=500,
                response_schema=ToolCallingResult.model_json_schema(),
            )
            raw_outputs.append(response.raw)
            total_latency += response.latency_seconds
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            result = _parse_result(response.data)
            combined = ModelResponse(
                data=response.data,
                raw="\n---ATTEMPT---\n".join(raw_outputs),
                latency_seconds=total_latency,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
            return result, combined
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
                            "Return a complete JSON object with behavior, calls, and clarification. "
                            "Use only supplied tool and parameter names."
                        ),
                    },
                ]
            )
            time.sleep(0.5 * (attempt + 1))

    raise ValueError(
        f"Structured tool-call response failed after {attempts} attempts: {last_error}"
    )


def run_tool_calling_model(
    *,
    client: StructuredClient,
    benchmark_path: Path,
    output_root: Path,
    experiment_id: str | None = None,
    limit: int | None = None,
    condition: str = "curated_catalog_zero_shot",
) -> Path:
    """Run one model over the seed benchmark and preserve per-task results."""

    tasks = load_tool_calling_tasks(benchmark_path)
    if limit is not None:
        tasks = tasks[:limit]

    identifier = experiment_id or (
        f"toolcall-{client.provider}-{client.model.replace('/', '_').replace(':', '_')}-"
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
            result, response = request_tool_call(client, task)
            score = score_tool_calling(task, result)
            payload = {
                "run_id": str(uuid4()),
                "task": task.model_dump(),
                "result": result.model_dump(),
                "score": score.to_dict(),
                "provider": client.provider,
                "model": client.model,
                "latency_seconds": response.latency_seconds,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "raw_output": response.raw,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - preserve per-task failure and continue
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
                "error": repr(exc),
            }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest["completed_at"] = datetime.now(UTC).isoformat()
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_dir

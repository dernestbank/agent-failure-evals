"""Prompt construction for baseline, self-check, and verification."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from typing import Any

from pydantic import ValidationError

from ..providers.base import ModelResponse, StructuredClient
from ..schemas.models import AgentResult, Scenario

SCHEMA = {
    "status": "completed|incomplete|cannot_complete",
    "answer": "concise answer",
    "evidence": ["exact evidence_id values used"],
    "assumptions": [],
    "tool_errors": [],
    "confidence": 0.0,
    "needs_human_review": False,
}
BASELINE_SYSTEM = "You are a scientific workflow assistant. Use the supplied tool trace to answer the user. Return one JSON object matching the requested schema."
AUDIT_SYSTEM = "You audit scientific workflow completion. Use only observable evidence, never invent evidence, and return one JSON object matching the requested schema."


def trace_payload(s: Scenario) -> list[dict[str, Any]]:
    return [{"tool_name": t.name, "response": t.response} for t in s.tools]


def _candidate_dicts(value: Any) -> Iterator[dict[str, Any]]:
    """Yield direct and wrapped result objects produced by smaller models."""
    if isinstance(value, dict):
        yield value
        for key in ("result", "final", "response", "output", "answer"):
            child = value.get(key)
            if isinstance(child, (dict, list)):
                yield from _candidate_dicts(child)
        for key, child in value.items():
            if key not in {"result", "final", "response", "output", "answer"} and isinstance(
                child, (dict, list)
            ):
                yield from _candidate_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _candidate_dicts(child)


def _parse_result(data: dict[str, Any]) -> AgentResult:
    errors: list[str] = []
    for candidate in _candidate_dicts(data):
        try:
            return AgentResult.model_validate(candidate)
        except ValidationError as exc:
            errors.append(str(exc))
    detail = errors[-1] if errors else "No dictionary candidate found"
    raise ValueError(f"Invalid AgentResult: {detail}")


def _request(
    client: StructuredClient, messages: list[dict[str, str]], attempts: int = 3
) -> tuple[AgentResult, ModelResponse]:
    latency = 0.0
    inp = 0
    out = 0
    raws = []
    current = list(messages)
    last = None
    for i in range(attempts):
        try:
            r = client.generate(current)
            latency += r.latency_seconds
            inp += r.input_tokens
            out += r.output_tokens
            raws.append(r.raw)
            result = _parse_result(r.data)
            return result, ModelResponse(
                data=r.data,
                raw="\n---ATTEMPT---\n".join(raws),
                latency_seconds=latency,
                input_tokens=inp,
                output_tokens=out,
            )
        except (ValidationError, ValueError) as exc:
            last = exc
            current += [
                {"role": "assistant", "content": raws[-1] if raws else "{}"},
                {
                    "role": "user",
                    "content": "Your response was invalid. Return a FULL JSON object with every required field. Never return an empty object.",
                },
            ]
            time.sleep(0.5 * (i + 1))
    raise ValueError(f"Structured response failed after {attempts} attempts: {last}")


def baseline(client: StructuredClient, s: Scenario) -> tuple[AgentResult, ModelResponse]:
    p = {
        "task": s.user_request,
        "tool_trace": trace_payload(s),
        "instruction": "Answer the task and report whether the workflow is completed, incomplete, or cannot be completed. Cite evidence_id values used.",
        "output_schema": SCHEMA,
    }
    return _request(
        client,
        [
            {"role": "system", "content": BASELINE_SYSTEM},
            {"role": "user", "content": json.dumps(p)},
        ],
    )


def self_check(
    client: StructuredClient, s: Scenario, first: AgentResult
) -> tuple[AgentResult, ModelResponse]:
    p = {
        "task": s.user_request,
        "tool_trace": trace_payload(s),
        "first_answer": first.model_dump(),
        "completion_checklist": s.success_criteria,
        "instruction": "Audit your first answer against every checklist item. Revise status if any criterion is unmet. Cite exact evidence_id values only.",
        "output_schema": SCHEMA,
    }
    return _request(
        client,
        [{"role": "system", "content": AUDIT_SYSTEM}, {"role": "user", "content": json.dumps(p)}],
    )


def verifier(
    client: StructuredClient, s: Scenario, first: AgentResult
) -> tuple[AgentResult, ModelResponse]:
    p = {
        "task": s.user_request,
        "tool_trace": trace_payload(s),
        "candidate_answer": first.model_dump(),
        "completion_checklist": s.success_criteria,
        "instruction": "Independently judge actual completion. Correct unsupported success and distinguish incomplete work from impossibility.",
        "output_schema": SCHEMA,
    }
    return _request(
        client,
        [
            {
                "role": "system",
                "content": "You are an independent scientific workflow verifier. Use observable evidence only and return JSON.",
            },
            {"role": "user", "content": json.dumps(p)},
        ],
    )

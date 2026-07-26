"""Schemas and deterministic scoring for domain-specific tool calling."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ToolBehavior = Literal["call", "multi_call", "clarify", "abstain"]
CallGateAction = Literal["call_required", "no_call"]
CallBranchBehavior = Literal["call", "multi_call"]
NoCallBranchBehavior = Literal["clarify", "abstain"]


class ExpectedToolCall(BaseModel):
    """One normalized function call."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class DomainToolCallingTask(BaseModel):
    """One domain-specific tool-calling benchmark task."""

    task_id: str
    domain: str
    behavior: ToolBehavior
    user_request: str
    available_tools: list[dict[str, Any]]
    expected_calls: list[ExpectedToolCall] = Field(default_factory=list)
    valid_alternatives: list[list[ExpectedToolCall]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    difficulty: str
    provisional_schema: bool = True
    conditional_execution: bool = False
    catalog_condition: str | None = None
    catalog_size: int | None = None
    retrieval_condition: str | None = None
    retrieval_model: str | None = None
    retrieval_selected_tools: list[str] = Field(default_factory=list)
    retrieval_scores: dict[str, float] = Field(default_factory=dict)
    retrieval_recall: float | None = None


class ToolCallingResult(BaseModel):
    """Observable model output for one tool-calling task."""

    behavior: ToolBehavior
    calls: list[ExpectedToolCall] = Field(default_factory=list)
    clarification: str | None = None


class BehaviorDecision(BaseModel):
    """Stage-one routing decision without executable calls."""

    behavior: ToolBehavior
    clarification: str | None = None


class CallGenerationResult(BaseModel):
    """Stage-two executable calls after behavior has been fixed."""

    calls: list[ExpectedToolCall] = Field(default_factory=list)


class CallGateDecision(BaseModel):
    """Binary decision that determines whether tool execution is permitted."""

    action: CallGateAction
    rationale: str | None = None


class CallBranchDecision(BaseModel):
    """Call-count decision after the binary gate authorizes execution."""

    behavior: CallBranchBehavior


class NoCallBranchDecision(BaseModel):
    """Clarification-versus-abstention decision after the gate blocks execution."""

    behavior: NoCallBranchBehavior
    clarification: str | None = None


@dataclass(frozen=True)
class ToolCallScore:
    """Deterministic metrics for one predicted call sequence."""

    behavior_correct: bool
    sequence_exact: bool
    tool_selection_accuracy: float
    required_argument_recall: float
    argument_precision: float
    false_tool_call: bool
    safe_no_call: bool | None

    def to_dict(self) -> dict[str, bool | float | None]:
        return asdict(self)


def load_tool_calling_tasks(path: Path) -> list[DomainToolCallingTask]:
    """Load and validate a JSONL tool-calling benchmark."""

    tasks: list[DomainToolCallingTask] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            tasks.append(DomainToolCallingTask.model_validate(json.loads(line)))
        except Exception as exc:
            raise ValueError(f"Invalid tool-calling task on line {line_number}: {exc}") from exc

    identifiers = [task.task_id for task in tasks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate task_id in tool-calling benchmark")
    return tasks


def _normalize_value(value: Any) -> Any:
    """Normalize JSON-compatible values for deterministic comparison."""

    if isinstance(value, dict):
        return {key: _normalize_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _normalized_call(call: ExpectedToolCall) -> tuple[str, str]:
    arguments = json.dumps(
        _normalize_value(call.arguments),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return call.name, arguments


def _sequence_matches(predicted: list[ExpectedToolCall], expected: list[ExpectedToolCall]) -> bool:
    if len(predicted) != len(expected):
        return False
    return all(
        _normalized_call(predicted_call) == _normalized_call(expected_call)
        for predicted_call, expected_call in zip(predicted, expected, strict=True)
    )


def _best_reference(
    task: DomainToolCallingTask, result: ToolCallingResult
) -> list[ExpectedToolCall]:
    candidates = [task.expected_calls, *task.valid_alternatives]
    if not candidates:
        return []

    for candidate in candidates:
        if _sequence_matches(result.calls, candidate):
            return candidate

    def overlap(candidate: list[ExpectedToolCall]) -> tuple[int, int, int]:
        matching_names = 0
        matching_arguments = 0
        for predicted, expected in zip(result.calls, candidate, strict=False):
            if predicted.name != expected.name:
                continue
            matching_names += 1
            for key, expected_value in expected.arguments.items():
                if key in predicted.arguments and _normalize_value(
                    predicted.arguments[key]
                ) == _normalize_value(expected_value):
                    matching_arguments += 1
        return (
            matching_names,
            matching_arguments,
            -abs(len(result.calls) - len(candidate)),
        )

    return max(candidates, key=overlap)


def score_tool_calling(task: DomainToolCallingTask, result: ToolCallingResult) -> ToolCallScore:
    """Score behavior, routing, sequence, and argument fidelity."""

    behavior_correct = result.behavior == task.behavior
    references = [task.expected_calls, *task.valid_alternatives]
    sequence_exact = any(_sequence_matches(result.calls, reference) for reference in references)
    if not references:
        sequence_exact = len(result.calls) == 0

    reference = _best_reference(task, result)
    predicted_names = [call.name for call in result.calls]
    expected_names = [call.name for call in reference]

    if not expected_names:
        tool_selection_accuracy = 1.0 if not predicted_names else 0.0
    else:
        matched_tools = sum(
            predicted == expected
            for predicted, expected in zip(predicted_names, expected_names, strict=False)
        )
        tool_selection_accuracy = matched_tools / len(expected_names)

    required_arguments = 0
    correct_required_arguments = 0
    predicted_arguments = 0
    correct_predicted_arguments = 0

    for index, expected_call in enumerate(reference):
        required_arguments += len(expected_call.arguments)
        if index >= len(result.calls):
            continue
        predicted_call = result.calls[index]
        if predicted_call.name != expected_call.name:
            predicted_arguments += len(predicted_call.arguments)
            continue
        for key, expected_value in expected_call.arguments.items():
            if key in predicted_call.arguments and _normalize_value(
                predicted_call.arguments[key]
            ) == _normalize_value(expected_value):
                correct_required_arguments += 1
        for key, predicted_value in predicted_call.arguments.items():
            predicted_arguments += 1
            if key in expected_call.arguments and _normalize_value(
                predicted_value
            ) == _normalize_value(expected_call.arguments[key]):
                correct_predicted_arguments += 1

    if len(result.calls) > len(reference):
        for extra_call in result.calls[len(reference) :]:
            predicted_arguments += len(extra_call.arguments)

    required_argument_recall = (
        1.0 if required_arguments == 0 else correct_required_arguments / required_arguments
    )
    argument_precision = (
        1.0
        if predicted_arguments == 0 and required_arguments == 0
        else 0.0
        if predicted_arguments == 0
        else correct_predicted_arguments / predicted_arguments
    )
    no_call_required = task.behavior in {"clarify", "abstain"}
    false_tool_call = no_call_required and bool(result.calls)
    safe_no_call = (
        result.behavior in {"clarify", "abstain"} and not result.calls if no_call_required else None
    )

    return ToolCallScore(
        behavior_correct=behavior_correct,
        sequence_exact=sequence_exact,
        tool_selection_accuracy=tool_selection_accuracy,
        required_argument_recall=required_argument_recall,
        argument_precision=argument_precision,
        false_tool_call=false_tool_call,
        safe_no_call=safe_no_call,
    )

"""Deterministic retrieval thresholding and tool-call precondition validation."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Literal

from .tool_calling import DomainToolCallingTask, ExpectedToolCall, ToolCallingResult

GuardPolicy = Literal["strict", "sanitize"]
GuardAction = Literal["pass", "threshold_abstain", "blocked", "sanitized"]

TOOL_ALIASES: dict[str, tuple[str, ...]] = {
    "search_entities": ("find", "search"),
    "calculate_impacts": ("calculate impact", "environmental impact"),
    "create_product_system": ("create product system", "build product system"),
    "get_contributions": ("contributor", "contribution", "hotspot"),
    "export_results": ("export", "save result", "write file"),
    "run_tea_scenario": ("run scenario", "run it", "run the hydrogen tea"),
    "compare_tea_scenarios": ("compare",),
    "set_tea_parameter": ("set", "change parameter", "update parameter"),
    "get_tea_result": ("hydrogen cost", "tea result", "capex", "opex"),
    "set_stream_composition": ("stream", "mass fraction", "composition"),
    "run_flowsheet": ("run flowsheet", "converge", "converges"),
    "check_mass_balance": ("mass balance", "mass-balance", "closure"),
    "get_impact_result": ("impact result", "environmental climate impact"),
}

PROPERTY_ALIASES: dict[str, tuple[str, ...]] = {
    "capacity_factor": ("capacity factor",),
    "electricity_price_usd_per_kwh": ("electricity price", "dollars per kwh"),
    "specific_energy_kwh_per_kg": ("specific energy", "energy consumption", "kwh per kg"),
    "discount_rate": ("discount rate",),
    "mass_fraction": ("mass fraction",),
    "impact_category": ("impact category", "climate impact", "water impact", "toxicity"),
    "tolerance": ("tolerance",),
    "limit": ("largest", "top ", "first "),
    "metric": ("hydrogen cost", "levelized hydrogen cost", "capex", "opex"),
}

ENUM_ALIASES: dict[tuple[str, str], tuple[str, ...]] = {
    ("entity_type", "process"): ("process", "processes"),
    ("entity_type", "flow"): ("flow", "flows"),
    ("entity_type", "impact_method"): ("impact method",),
    ("impact_category", "climate"): ("climate", "climate impact"),
    ("impact_category", "water"): ("water", "water impact"),
    ("impact_category", "human_toxicity"): ("human toxicity", "toxicity"),
    ("parameter", "specific_energy_kwh_per_kg"): (
        "specific energy",
        "energy consumption",
        "kwh per kg",
    ),
    ("parameter", "electricity_price_usd_per_kwh"): ("electricity price",),
    ("parameter", "capacity_factor"): ("capacity factor",),
    ("parameter", "discount_rate"): ("discount rate",),
    ("metric", "levelized_hydrogen_cost"): ("hydrogen cost", "levelized hydrogen cost"),
    ("metric", "capex"): ("capex", "capital cost"),
    ("metric", "opex"): ("opex", "operating cost"),
}

IDENTIFIER_PARAMETERS = {
    "product_system_id",
    "impact_method_id",
    "process_id",
    "result_id",
    "scenario_id",
    "scenario_a_id",
    "scenario_b_id",
    "stream_id",
    "flowsheet_id",
}

CONDITIONAL_NUMERIC_RANGES: dict[tuple[str, str, str, str], tuple[float | None, float | None]] = {
    ("set_tea_parameter", "parameter", "capacity_factor", "value"): (0.0, 1.0),
    ("set_tea_parameter", "parameter", "discount_rate", "value"): (0.0, 1.0),
}

NUMBER_WORDS = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
}


@dataclass(frozen=True)
class GuardViolation:
    code: str
    message: str
    call_index: int | None = None
    tool_name: str | None = None
    argument: str | None = None
    disposition: Literal["drop_argument", "drop_call", "block_request"] = "drop_call"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardOutcome:
    action: GuardAction
    policy: GuardPolicy
    result: ToolCallingResult
    violations: tuple[GuardViolation, ...]
    retrieval_top_score: float | None
    retrieval_threshold: float
    original_call_count: int
    final_call_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "policy": self.policy,
            "result": self.result.model_dump(),
            "violations": [violation.to_dict() for violation in self.violations],
            "retrieval_top_score": self.retrieval_top_score,
            "retrieval_threshold": self.retrieval_threshold,
            "original_call_count": self.original_call_count,
            "final_call_count": self.final_call_count,
        }


def _normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _stem_token(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def _tokens(value: str) -> set[str]:
    return {_stem_token(token) for token in re.findall(r"[a-z0-9]+", value.lower())}


def _contains_phrase(request: str, phrase: str) -> bool:
    request_normalized = _normalize_text(request)
    phrase_normalized = _normalize_text(phrase)
    if phrase_normalized and phrase_normalized in request_normalized:
        return True
    phrase_tokens = _tokens(phrase)
    return bool(phrase_tokens) and phrase_tokens.issubset(_tokens(request))


def _request_numbers(request: str) -> list[float]:
    values = [float(match) for match in re.findall(r"(?<![\w.-])\d+(?:\.\d+)?", request)]
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:percent|%)", request.lower()):
        values.append(float(match.group(1)) / 100.0)
    request_tokens = _tokens(request)
    values.extend(number for word, number in NUMBER_WORDS.items() if word in request_tokens)
    return values


def _number_grounded(value: float, request: str) -> bool:
    return any(
        abs(value - candidate) <= max(1e-9, abs(value) * 1e-9)
        for candidate in _request_numbers(request)
    )


def _tool_requested(tool_name: str, request: str) -> bool:
    aliases = TOOL_ALIASES.get(tool_name, (tool_name.replace("_", " "),))
    return any(_contains_phrase(request, alias) for alias in aliases)


def _property_requested(property_name: str, request: str) -> bool:
    aliases = PROPERTY_ALIASES.get(property_name, (property_name.replace("_", " "),))
    return any(_contains_phrase(request, alias) for alias in aliases)


def _enum_grounded(argument: str, value: str, request: str) -> bool:
    aliases = ENUM_ALIASES.get((argument, value), (value.replace("_", " "),))
    return any(_contains_phrase(request, alias) for alias in aliases)


def _string_grounded(
    argument: str, value: str, request: str, specification: dict[str, Any]
) -> bool:
    if "enum" in specification:
        return _enum_grounded(argument, value, request)
    if argument in IDENTIFIER_PARAMETERS:
        return _normalize_text(value) in _normalize_text(request)
    if argument in {"query", "component", "format"}:
        return _tokens(value).issubset(_tokens(request))
    return _contains_phrase(request, value)


def _type_valid(value: Any, expected_type: str | None) -> bool:
    if expected_type is None:
        return True
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return True


def _coerce_grounded_number(
    value: Any,
    expected_type: str | None,
    request: str,
) -> int | float | None:
    """Coerce a grounded numeric string without inventing a value."""

    if expected_type not in {"integer", "number"} or not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    numeric: float | None = None
    try:
        numeric = float(normalized)
    except ValueError:
        if normalized in NUMBER_WORDS:
            numeric = NUMBER_WORDS[normalized]

    if numeric is None or not _number_grounded(numeric, request):
        return None
    if expected_type == "integer":
        if not numeric.is_integer():
            return None
        return int(numeric)
    return numeric


def retrieval_top_score(task: DomainToolCallingTask) -> float | None:
    if task.retrieval_selected_tools:
        first = task.retrieval_selected_tools[0]
        return task.retrieval_scores.get(first)
    if task.retrieval_scores:
        return max(task.retrieval_scores.values())
    return None


def _validate_call(
    task: DomainToolCallingTask,
    call: ExpectedToolCall,
    call_index: int,
) -> tuple[ExpectedToolCall | None, list[GuardViolation]]:
    violations: list[GuardViolation] = []
    registry = {str(tool["name"]): tool for tool in task.available_tools}
    tool = registry.get(call.name)
    if tool is None:
        violations.append(
            GuardViolation(
                code="unknown_tool",
                message=f"Tool {call.name!r} is not in the retrieved catalog.",
                call_index=call_index,
                tool_name=call.name,
            )
        )
        return None, violations

    if not _tool_requested(call.name, task.user_request):
        violations.append(
            GuardViolation(
                code="tool_not_grounded",
                message=f"The request does not support invoking {call.name!r}.",
                call_index=call_index,
                tool_name=call.name,
            )
        )
        return None, violations

    parameters = tool.get("parameters", {})
    properties = parameters.get("properties", {})
    required = set(parameters.get("required", []))
    sanitized: dict[str, Any] = {}
    drop_call = False

    unknown = sorted(set(call.arguments) - set(properties))
    for argument in unknown:
        violations.append(
            GuardViolation(
                code="unknown_argument",
                message=f"Argument {argument!r} is not defined for {call.name!r}.",
                call_index=call_index,
                tool_name=call.name,
                argument=argument,
                disposition="drop_argument",
            )
        )

    for argument in required:
        if argument not in call.arguments or call.arguments[argument] is None:
            violations.append(
                GuardViolation(
                    code="missing_required_argument",
                    message=f"Required argument {argument!r} is missing for {call.name!r}.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                )
            )
            drop_call = True

    for argument, specification in properties.items():
        if _property_requested(argument, task.user_request) and argument not in call.arguments:
            violations.append(
                GuardViolation(
                    code="requested_argument_omitted",
                    message=f"The request explicitly mentions {argument!r}, but the call omits it.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                )
            )
            drop_call = True

    for (tool_name, selector_argument, selector_value, numeric_argument), (
        minimum,
        maximum,
    ) in CONDITIONAL_NUMERIC_RANGES.items():
        if (
            call.name == tool_name
            and call.arguments.get(selector_argument) == selector_value
            and numeric_argument in call.arguments
        ):
            numeric_value = call.arguments[numeric_argument]
            if isinstance(numeric_value, (int, float)) and not isinstance(numeric_value, bool):
                if minimum is not None and numeric_value < minimum:
                    violations.append(
                        GuardViolation(
                            code="below_minimum",
                            message=(
                                f"Argument {numeric_argument!r} is below the conditional minimum "
                                f"for {selector_value!r}."
                            ),
                            call_index=call_index,
                            tool_name=call.name,
                            argument=numeric_argument,
                        )
                    )
                    drop_call = True
                if maximum is not None and numeric_value > maximum:
                    violations.append(
                        GuardViolation(
                            code="above_maximum",
                            message=(
                                f"Argument {numeric_argument!r} exceeds the conditional maximum "
                                f"for {selector_value!r}."
                            ),
                            call_index=call_index,
                            tool_name=call.name,
                            argument=numeric_argument,
                        )
                    )
                    drop_call = True

    for argument, value in call.arguments.items():
        if argument not in properties:
            continue
        specification = properties[argument]
        is_required = argument in required
        explicitly_requested = _property_requested(argument, task.user_request)
        must_preserve_semantics = is_required or explicitly_requested
        disposition: Literal["drop_argument", "drop_call"] = (
            "drop_call" if must_preserve_semantics else "drop_argument"
        )

        if value is None:
            violations.append(
                GuardViolation(
                    code="null_argument",
                    message=f"Argument {argument!r} is null.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition=disposition,
                )
            )
            drop_call = drop_call or must_preserve_semantics
            continue

        expected_type = specification.get("type")
        coerced_value = _coerce_grounded_number(value, expected_type, task.user_request)
        if coerced_value is not None:
            violations.append(
                GuardViolation(
                    code="canonicalized_numeric_type",
                    message=f"Argument {argument!r} was converted to its grounded numeric type.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition="drop_argument",
                )
            )
            value = coerced_value

        if not _type_valid(value, expected_type):
            violations.append(
                GuardViolation(
                    code="invalid_type",
                    message=f"Argument {argument!r} has the wrong JSON type.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition=disposition,
                )
            )
            drop_call = drop_call or must_preserve_semantics
            continue

        if "enum" in specification and value not in specification["enum"]:
            violations.append(
                GuardViolation(
                    code="invalid_enum",
                    message=f"Argument {argument!r} is outside the allowed enum.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition=disposition,
                )
            )
            drop_call = drop_call or must_preserve_semantics
            continue

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in specification and value < specification["minimum"]:
                violations.append(
                    GuardViolation(
                        code="below_minimum",
                        message=f"Argument {argument!r} is below its minimum.",
                        call_index=call_index,
                        tool_name=call.name,
                        argument=argument,
                        disposition=disposition,
                    )
                )
                drop_call = drop_call or must_preserve_semantics
                continue
            if "maximum" in specification and value > specification["maximum"]:
                violations.append(
                    GuardViolation(
                        code="above_maximum",
                        message=f"Argument {argument!r} exceeds its maximum.",
                        call_index=call_index,
                        tool_name=call.name,
                        argument=argument,
                        disposition=disposition,
                    )
                )
                drop_call = drop_call or must_preserve_semantics
                continue
            grounded = _number_grounded(float(value), task.user_request)
        elif isinstance(value, str):
            grounded = _string_grounded(argument, value, task.user_request, specification)
        else:
            grounded = True

        if not grounded:
            violations.append(
                GuardViolation(
                    code="argument_not_grounded",
                    message=f"Argument {argument!r} is not supported by the user request.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition=disposition,
                )
            )
            drop_call = drop_call or must_preserve_semantics
            continue

        if not is_required and not explicitly_requested:
            violations.append(
                GuardViolation(
                    code="unsolicited_optional_argument",
                    message=f"Optional argument {argument!r} was not requested.",
                    call_index=call_index,
                    tool_name=call.name,
                    argument=argument,
                    disposition="drop_argument",
                )
            )
            continue

        sanitized[argument] = value

    if drop_call:
        return None, violations
    if any(argument not in sanitized for argument in required):
        return None, violations
    return ExpectedToolCall(name=call.name, arguments=sanitized), violations


def apply_tool_call_guard(
    task: DomainToolCallingTask,
    result: ToolCallingResult,
    *,
    policy: GuardPolicy,
    retrieval_threshold: float = 0.60,
) -> GuardOutcome:
    """Apply a no-tool threshold and deterministic call validation."""

    top_score = retrieval_top_score(task)
    if top_score is not None and top_score < retrieval_threshold:
        guarded = ToolCallingResult(behavior="abstain", calls=[], clarification=None)
        violation = GuardViolation(
            code="retrieval_below_threshold",
            message=(
                f"Top retrieval score {top_score:.4f} is below threshold {retrieval_threshold:.4f}."
            ),
            disposition="block_request",
        )
        return GuardOutcome(
            action="threshold_abstain",
            policy=policy,
            result=guarded,
            violations=(violation,),
            retrieval_top_score=top_score,
            retrieval_threshold=retrieval_threshold,
            original_call_count=len(result.calls),
            final_call_count=0,
        )

    if not result.calls:
        return GuardOutcome(
            action="pass",
            policy=policy,
            result=result,
            violations=(),
            retrieval_top_score=top_score,
            retrieval_threshold=retrieval_threshold,
            original_call_count=0,
            final_call_count=0,
        )

    sanitized_calls: list[ExpectedToolCall] = []
    violations: list[GuardViolation] = []
    for index, call in enumerate(result.calls):
        sanitized, call_violations = _validate_call(task, call, index)
        violations.extend(call_violations)
        if sanitized is not None and sanitized not in sanitized_calls:
            sanitized_calls.append(sanitized)

    if policy == "strict" and violations:
        guarded = ToolCallingResult(
            behavior="clarify",
            calls=[],
            clarification="The proposed tool call failed deterministic precondition checks.",
        )
        return GuardOutcome(
            action="blocked",
            policy=policy,
            result=guarded,
            violations=tuple(violations),
            retrieval_top_score=top_score,
            retrieval_threshold=retrieval_threshold,
            original_call_count=len(result.calls),
            final_call_count=0,
        )

    if not sanitized_calls:
        guarded = ToolCallingResult(
            behavior="clarify",
            calls=[],
            clarification="Required information or a valid grounded call is missing.",
        )
        return GuardOutcome(
            action="blocked",
            policy=policy,
            result=guarded,
            violations=tuple(violations),
            retrieval_top_score=top_score,
            retrieval_threshold=retrieval_threshold,
            original_call_count=len(result.calls),
            final_call_count=0,
        )

    behavior: Literal["call", "multi_call"] = "call" if len(sanitized_calls) == 1 else "multi_call"
    guarded = ToolCallingResult(behavior=behavior, calls=sanitized_calls, clarification=None)
    action: GuardAction = "sanitized" if violations or guarded != result else "pass"
    return GuardOutcome(
        action=action,
        policy=policy,
        result=guarded,
        violations=tuple(violations),
        retrieval_top_score=top_score,
        retrieval_threshold=retrieval_threshold,
        original_call_count=len(result.calls),
        final_call_count=len(sanitized_calls),
    )

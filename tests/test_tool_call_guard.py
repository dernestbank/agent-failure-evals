import json
from pathlib import Path

from agent_failure_evals.tool_call_guard import apply_tool_call_guard
from agent_failure_evals.tool_calling import (
    DomainToolCallingTask,
    ExpectedToolCall,
    ToolCallingResult,
    load_tool_calling_tasks,
    score_tool_calling,
)


def _task(path: str, task_id: str) -> DomainToolCallingTask:
    return next(task for task in load_tool_calling_tasks(Path(path)) if task.task_id == task_id)


def test_threshold_blocks_irrelevant_abstention_task() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-abstain-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="get_tea_result",
                arguments={"scenario_id": "LCA_results", "metric": "capex"},
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize", retrieval_threshold=0.60)

    assert outcome.action == "threshold_abstain"
    assert outcome.result.behavior == "abstain"
    assert outcome.result.calls == []


def test_guard_blocks_out_of_range_capacity_factor() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "tea-invalid-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="set_tea_parameter",
                arguments={
                    "scenario_id": "h2-base",
                    "parameter": "capacity_factor",
                    "value": 135,
                },
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.action == "blocked"
    assert outcome.result.behavior == "clarify"
    assert outcome.result.calls == []
    assert any(violation.code == "above_maximum" for violation in outcome.violations)


def test_sanitize_removes_unsolicited_limit_and_preserves_call() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-method-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="search_entities",
                arguments={"entity_type": "impact_method", "query": "TRACI 2.1", "limit": 1},
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.action == "sanitized"
    assert outcome.result.calls[0].arguments == {
        "entity_type": "impact_method",
        "query": "TRACI 2.1",
    }
    assert score_tool_calling(task, outcome.result).sequence_exact is True


def test_sanitize_drops_surplus_call_and_recovers_exact_sequence() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-discovery-001")
    proposal = ToolCallingResult(
        behavior="multi_call",
        calls=[
            ExpectedToolCall(
                name="search_entities",
                arguments={"entity_type": "process", "query": "PET resin", "limit": 10},
            ),
            ExpectedToolCall(
                name="create_product_system",
                arguments={"process_id": "found_process_id"},
            ),
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.result.behavior == "call"
    assert len(outcome.result.calls) == 1
    assert score_tool_calling(task, outcome.result).sequence_exact is True
    assert any(violation.code == "tool_not_grounded" for violation in outcome.violations)


def test_sanitize_blocks_explicit_invalid_optional_value_instead_of_using_defaults() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "tea-invalid-001")
    proposal = ToolCallingResult(
        behavior="multi_call",
        calls=[
            ExpectedToolCall(
                name="run_tea_scenario",
                arguments={
                    "scenario_id": "h2-base",
                    "electricity_price_usd_per_kwh": 0.15,
                    "capacity_factor": 135,
                },
            ),
            ExpectedToolCall(
                name="get_tea_result",
                arguments={
                    "scenario_id": "h2-base",
                    "metric": "levelized_hydrogen_cost",
                },
            ),
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.action == "blocked"
    assert outcome.result.behavior == "clarify"
    assert outcome.result.calls == []
    assert any(violation.code == "above_maximum" for violation in outcome.violations)


def test_sanitize_canonicalizes_grounded_numeric_string() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-contribution-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="get_contributions",
                arguments={
                    "result_id": "result-88",
                    "impact_category": "climate",
                    "limit": "10",
                },
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.action == "sanitized"
    assert outcome.result.calls[0].arguments["limit"] == 10
    assert score_tool_calling(task, outcome.result).sequence_exact is True
    assert any(violation.code == "canonicalized_numeric_type" for violation in outcome.violations)


def test_sanitize_canonicalizes_grounded_numeric_word() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-contribution-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="get_contributions",
                arguments={
                    "result_id": "result-88",
                    "impact_category": "climate",
                    "limit": "ten",
                },
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="sanitize")

    assert outcome.result.calls[0].arguments["limit"] == 10
    assert score_tool_calling(task, outcome.result).sequence_exact is True


def test_strict_policy_blocks_proposal_with_any_violation() -> None:
    task = _task("tasks/domain_tool_calling_top3_mxbai_v0.jsonl", "lca-method-001")
    proposal = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="search_entities",
                arguments={"entity_type": "impact_method", "query": "TRACI 2.1", "limit": 1},
            )
        ],
    )

    outcome = apply_tool_call_guard(task, proposal, policy="strict")

    assert outcome.action == "blocked"
    assert outcome.result.calls == []


def test_all_annotated_exact_calls_pass_without_false_positive() -> None:
    tasks = load_tool_calling_tasks(Path("tasks/domain_tool_calling_seed_v0.jsonl"))
    failures: list[dict[str, object]] = []

    for task in tasks:
        if task.behavior not in {"call", "multi_call"}:
            continue
        proposal = ToolCallingResult(
            behavior=task.behavior,
            calls=task.expected_calls,
            clarification=None,
        )
        outcome = apply_tool_call_guard(task, proposal, policy="sanitize")
        if outcome.result != proposal or outcome.violations:
            failures.append(
                {
                    "task_id": task.task_id,
                    "proposal": proposal.model_dump(),
                    "outcome": outcome.to_dict(),
                }
            )

    assert failures == [], json.dumps(failures, indent=2)

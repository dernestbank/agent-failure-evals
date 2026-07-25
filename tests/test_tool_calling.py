from pathlib import Path

from agent_failure_evals.tool_calling import (
    DomainToolCallingTask,
    ExpectedToolCall,
    ToolCallingResult,
    load_tool_calling_tasks,
    score_tool_calling,
)


def test_seed_benchmark_loads() -> None:
    tasks = load_tool_calling_tasks(Path("tasks/domain_tool_calling_seed_v0.jsonl"))

    assert len(tasks) == 15
    assert len({task.task_id for task in tasks}) == 15
    assert {task.domain for task in tasks} >= {"lca", "tea", "process_simulation"}


def test_exact_call_scores_perfectly() -> None:
    task = DomainToolCallingTask(
        task_id="example",
        domain="lca",
        behavior="call",
        user_request="Search for PET resin.",
        available_tools=[],
        expected_calls=[
            ExpectedToolCall(
                name="search_entities",
                arguments={"entity_type": "process", "query": "PET resin"},
            )
        ],
        difficulty="easy",
    )
    result = ToolCallingResult(
        behavior="call",
        calls=[
            ExpectedToolCall(
                name="search_entities",
                arguments={"query": "PET resin", "entity_type": "process"},
            )
        ],
    )

    score = score_tool_calling(task, result)

    assert score.behavior_correct is True
    assert score.sequence_exact is True
    assert score.tool_selection_accuracy == 1.0
    assert score.required_argument_recall == 1.0
    assert score.argument_precision == 1.0
    assert score.false_tool_call is False


def test_abstention_penalizes_false_call() -> None:
    task = DomainToolCallingTask(
        task_id="abstain",
        domain="lca",
        behavior="abstain",
        user_request="Send an email.",
        available_tools=[],
        difficulty="easy",
    )
    result = ToolCallingResult(
        behavior="call",
        calls=[ExpectedToolCall(name="calculate_impacts", arguments={})],
    )

    score = score_tool_calling(task, result)

    assert score.behavior_correct is False
    assert score.sequence_exact is False
    assert score.tool_selection_accuracy == 0.0
    assert score.false_tool_call is True


def test_valid_alternative_sequence_is_accepted() -> None:
    task = DomainToolCallingTask(
        task_id="parallel",
        domain="tea",
        behavior="multi_call",
        user_request="Run two scenarios.",
        available_tools=[],
        expected_calls=[
            ExpectedToolCall(name="run", arguments={"id": "a"}),
            ExpectedToolCall(name="run", arguments={"id": "b"}),
        ],
        valid_alternatives=[
            [
                ExpectedToolCall(name="run", arguments={"id": "b"}),
                ExpectedToolCall(name="run", arguments={"id": "a"}),
            ]
        ],
        difficulty="medium",
    )
    result = ToolCallingResult(
        behavior="multi_call",
        calls=[
            ExpectedToolCall(name="run", arguments={"id": "b"}),
            ExpectedToolCall(name="run", arguments={"id": "a"}),
        ],
    )

    score = score_tool_calling(task, result)

    assert score.sequence_exact is True
    assert score.tool_selection_accuracy == 1.0
    assert score.required_argument_recall == 1.0

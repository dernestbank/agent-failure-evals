from pathlib import Path

from agent_failure_evals.benchmark import load_scenarios, summary


def test_benchmark_v1_is_complete() -> None:
    scenarios = load_scenarios(Path("tasks/benchmark_v1.jsonl"))
    counts = summary(scenarios)

    assert len(scenarios) == 15
    assert counts["count"] == 15
    assert counts["statuses"]["completed"] == 4
    assert counts["statuses"]["cannot_complete"] == 4
    assert counts["statuses"]["incomplete"] == 7
    assert len({scenario.task_id for scenario in scenarios}) == 15

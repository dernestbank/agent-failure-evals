from pathlib import Path

import pytest

from agent_failure_evals.replay_control import (
    acquire_file_lock,
    exact_transition,
    release_file_lock,
    summarize_transitions,
)


def test_transition_labels_exact_status_changes() -> None:
    assert exact_transition(True, True) == "stable_exact"
    assert exact_transition(False, False) == "stable_incorrect"
    assert exact_transition(False, True) == "improved"
    assert exact_transition(True, False) == "regressed"


def test_summarize_pair_counts_net_transitions() -> None:
    rows = [
        {"schema_transition": "improved"},
        {"schema_transition": "improved"},
        {"schema_transition": "regressed"},
        {"schema_transition": "stable_exact"},
        {"schema_transition": "stable_incorrect"},
    ]

    summary = summarize_transitions(rows, "schema")

    assert summary["schema_improvements"] == 2
    assert summary["schema_regressions"] == 1
    assert summary["schema_stable_exact"] == 1
    assert summary["schema_stable_incorrect"] == 1
    assert summary["schema_net_transition"] == 1


def test_replay_lock_rejects_concurrent_writer(tmp_path: Path) -> None:
    lock = tmp_path / "replay.lock"

    descriptor = acquire_file_lock(lock)
    try:
        assert lock.exists()
        with pytest.raises(RuntimeError, match="lock already exists"):
            acquire_file_lock(lock)
    finally:
        release_file_lock(lock, descriptor)

    assert not lock.exists()

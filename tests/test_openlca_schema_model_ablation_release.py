import csv
import json
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "results" / "public"
RAW = ROOT / "results" / "raw"

MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_object(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_list(path: Path) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads(path.read_text(encoding="utf-8")))


def record_count(experiment_id: str) -> int:
    return sum(path.name != "manifest.json" for path in (RAW / experiment_id).glob("*.json"))


def test_all_before_after_and_replay_experiments_are_complete() -> None:
    for slug in MODELS.values():
        for seed in SEEDS:
            assert record_count(f"openlca-schema-before-{slug}-seed{seed}") == 20
            assert record_count(f"openlca-schema-after-{slug}-seed{seed}") == 20
            assert record_count(f"openlca-schema-replay-before-{slug}-seed{seed}") == 20


def test_release_reports_have_no_infrastructure_failures() -> None:
    assert load_list(PUBLIC / "openlca_schema_hardening_model_failures.json") == []
    assert load_list(PUBLIC / "openlca_schema_replay_control_failures.json") == []


def test_replay_adjusted_metrics_match_approved_result() -> None:
    rows = {
        (row["model"], row["group"]): row
        for row in csv_rows(PUBLIC / "openlca_schema_replay_control_aggregate.csv")
    }

    qwen = rows[("qwen3:8b", "all")]
    gemma = rows[("gemma3:4b", "all")]
    coder = rows[("qwen2.5-coder:1.5b", "all")]
    qwen_expected = rows[("qwen3:8b", "expected_tool_changed")]
    gemma_expected = rows[("gemma3:4b", "expected_tool_changed")]

    assert float(qwen["replay_adjusted_delta"]) == pytest.approx(0.1)
    assert float(gemma["replay_adjusted_delta"]) == pytest.approx(1 / 15)
    assert float(coder["replay_adjusted_delta"]) == 0.0
    assert float(qwen_expected["schema_delta"]) == pytest.approx(1 / 3)
    assert float(qwen_expected["replay_delta"]) == 0.0
    assert float(gemma_expected["schema_delta"]) == pytest.approx(1 / 6)
    assert float(gemma_expected["replay_delta"]) == 0.0


def test_direct_contract_mechanisms_repeat_across_all_seeds() -> None:
    task_rows = csv_rows(PUBLIC / "openlca_schema_replay_control_tasks.csv")
    transitions = {
        (row["model"], row["task_id"]): [
            item
            for item in task_rows
            if item["model"] == row["model"] and item["task_id"] == row["task_id"]
        ]
        for row in task_rows
    }

    for key in (
        ("qwen3:8b", "olca-exact-entity-001"),
        ("qwen3:8b", "olca-search-flows-001"),
        ("gemma3:4b", "olca-inventory-output-001"),
    ):
        rows = transitions[key]
        assert len(rows) == 3
        assert {row["schema_transition"] for row in rows} == {"improved"}
        assert {row["replay_transition"] for row in rows} == {"stable_incorrect"}


def test_public_manifest_records_schema_ablation() -> None:
    manifest = load_object(PUBLIC / "manifest.json")
    study = cast(dict[str, Any], manifest["openlca_mcp_schema_model_ablation"])
    results = cast(dict[str, dict[str, Any]], study["model_results"])

    assert study["before_after_task_runs"] == 360
    assert study["same_schema_replay_task_runs"] == 180
    assert study["total_inference_task_runs"] == 540
    assert study["infrastructure_failures"] == 0
    assert results["qwen3:8b"]["replay_adjusted_delta"] == pytest.approx(0.1)
    assert results["qwen2.5-coder:1.5b"]["replay_adjusted_delta"] == 0.0

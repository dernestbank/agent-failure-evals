"""Regenerate public release metadata from approved experiment artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "results" / "public" / "manifest.json"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


CONDITIONS = {
    "curated_catalog_zero_shot": [
        "domain-v0.1-qwen3-8b",
        "domain-v0.1-gemma3-4b",
        "domain-v0.1-qwen25-coder-1.5b",
        "domain-v0.1-qwen25-coder-7b",
        "domain-v0.1-llama32",
        "domain-v0.1-gpt-oss-20b-free",
        "domain-v0.1-gemma4-26b-free",
    ],
    "full_catalog_zero_shot": [
        "domain-full-v0-qwen3-8b",
        "domain-full-v0-gemma3-4b",
        "domain-full-v0-qwen25-coder-1.5b",
    ],
    "top3_embedding_zero_shot": [
        "domain-top3-v0-qwen3-8b",
        "domain-top3-v0-gemma3-4b",
        "domain-top3-v0-qwen25-coder-1.5b",
    ],
    "two_stage_behavior_router": [
        "domain-router-v0-qwen3-8b",
        "domain-router-v0-gemma3-4b",
        "domain-router-v0-qwen25-coder-1.5b",
    ],
    "two_stage_behavior_router_few_shot": [
        "domain-router-fewshot-v0-qwen3-8b",
        "domain-router-fewshot-v0-gemma3-4b",
        "domain-router-fewshot-v0-qwen25-coder-1.5b",
    ],
}

STABILITY_MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
STABILITY_SEEDS = [101, 202, 303]
TOOL_GUARD_EXPERIMENTS = [
    f"toolguard-stability-{slug}-seed{seed}"
    for slug in STABILITY_MODELS.values()
    for seed in STABILITY_SEEDS
]
CONDITIONS["single_stage_gate_stability"] = [
    f"gate-stability-single-{slug}-seed{seed}"
    for slug in STABILITY_MODELS.values()
    for seed in STABILITY_SEEDS
]
CONDITIONS["hierarchical_binary_call_gate_stability"] = [
    f"gate-stability-gate-{slug}-seed{seed}"
    for slug in STABILITY_MODELS.values()
    for seed in STABILITY_SEEDS
]

CATALOG_CONDITION = {
    "curated_catalog_zero_shot": "curated_catalog",
    "full_catalog_zero_shot": "full_catalog",
    "top3_embedding_zero_shot": "top3_embedding",
    "two_stage_behavior_router": "curated_catalog",
    "two_stage_behavior_router_few_shot": "curated_catalog",
    "single_stage_gate_stability": "curated_catalog_balanced_subset",
    "hierarchical_binary_call_gate_stability": "curated_catalog_balanced_subset",
}


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []
    total_scored = 0
    total_attempted = 0
    total_failures = 0

    for condition, experiment_ids in CONDITIONS.items():
        for experiment_id in experiment_ids:
            raw_dir = ROOT / "results" / "raw" / experiment_id
            processed_dir = ROOT / "results" / "processed" / experiment_id
            experiment_manifest = json.loads(
                (raw_dir / "manifest.json").read_text(encoding="utf-8")
            )
            metrics = json.loads((processed_dir / "metrics.json").read_text(encoding="utf-8"))
            failures = json.loads((processed_dir / "failures.json").read_text(encoding="utf-8"))
            scored = int(metrics["n"])
            attempted = scored + len(failures)
            total_scored += scored
            total_attempted += attempted
            total_failures += len(failures)
            records.append(
                {
                    "experiment_id": experiment_id,
                    "experiment_condition": condition,
                    "catalog_condition": CATALOG_CONDITION[condition],
                    "provider": experiment_manifest["provider"],
                    "model": experiment_manifest["model"],
                    "attempted_tasks": attempted,
                    "scored_tasks": scored,
                    "infrastructure_failures": len(failures),
                }
            )

    tool_guard_scored = 0
    tool_guard_attempted = 0
    tool_guard_failures = 0
    for experiment_id in TOOL_GUARD_EXPERIMENTS:
        raw_dir = ROOT / "results" / "raw" / experiment_id
        experiment_manifest = json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
        payloads = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(raw_dir.glob("*.json"))
            if path.name != "manifest.json"
        ]
        failures = [payload for payload in payloads if payload.get("error")]
        scored = len(payloads) - len(failures)
        attempted = len(payloads)
        tool_guard_scored += scored
        tool_guard_attempted += attempted
        tool_guard_failures += len(failures)
        total_scored += scored
        total_attempted += attempted
        total_failures += len(failures)
        records.append(
            {
                "experiment_id": experiment_id,
                "experiment_condition": "tool_call_guard_stability_proposals",
                "catalog_condition": "top3_embedding",
                "provider": experiment_manifest["provider"],
                "model": experiment_manifest["model"],
                "attempted_tasks": attempted,
                "scored_tasks": scored,
                "infrastructure_failures": len(failures),
            }
        )

    manifest["domain_toolbench"] = {
        "name": "DomainToolBench",
        "version": "0.1-seed",
        "task_count": 15,
        "schema_status": "provisional_normalized_research_interfaces",
        "behaviors": ["call", "multi_call", "clarify", "abstain"],
        "approved_experiments": records,
        "total_attempted_task_runs": total_attempted,
        "total_scored_task_runs": total_scored,
        "total_infrastructure_failures": total_failures,
        "main_seed_single_run_per_model_condition": True,
        "stability_study": {
            "task_count": 8,
            "call_required_tasks": 4,
            "no_call_tasks": 4,
            "models": list(STABILITY_MODELS),
            "seeds": STABILITY_SEEDS,
            "temperature": 0.2,
            "conditions": [
                "single_stage_gate_stability",
                "hierarchical_binary_call_gate_stability",
            ],
            "attempted_task_runs": 144,
            "scored_task_runs": 144,
            "infrastructure_failures": 0,
        },
        "retrieval": {
            "model": "mxbai-embed-large",
            "runtime": "ollama",
            "full_catalog_size": 13,
            "top_k": 3,
            "mean_expected_tool_recall": 0.9545454545,
            "perfect_recall_tasks": "10/11",
        },
        "tool_call_guard_stability": {
            "task_count": 15,
            "models": list(STABILITY_MODELS),
            "seeds": STABILITY_SEEDS,
            "temperature": 0.2,
            "retrieval_threshold": 0.60,
            "threshold_status": "exploratory_post_hoc_current_seed",
            "model_proposals": tool_guard_attempted,
            "scored_model_proposals": tool_guard_scored,
            "paired_guard_transformations": tool_guard_scored * 2,
            "infrastructure_failures": tool_guard_failures,
            "guard_revision": "v0.2-explicit-invalid-block-numeric-coercion",
            "policies": ["strict", "sanitize"],
        },
        "human_annotation_review_status": (
            "author_review_required_before_external_dataset_release"
        ),
    }
    drift_summary = json.loads(
        (ROOT / "manifests" / "openlca_mcp_schema_drift_summary.json").read_text(encoding="utf-8")
    )
    source_common_tasks = sum(
        bool(line.strip())
        for line in (ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    connector_common_tasks = sum(
        bool(line.strip())
        for line in (ROOT / "tasks" / "domain_tool_calling_openlca_connector_v0.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    source_extension_tasks = sum(
        bool(line.strip())
        for line in (ROOT / "tasks" / "domain_tool_calling_openlca_source_extension_v0.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    manifest["openlca_mcp_schema_audit"] = {
        "local_source_commit": drift_summary["source_commit"],
        "local_source_tool_count": drift_summary["source_tool_count"],
        "connector_visible_tool_count": drift_summary["connector_tool_count"],
        "shared_tool_count": drift_summary["shared_tool_count"],
        "source_only_tools": drift_summary["source_only_tools"],
        "connector_only_tools": drift_summary["connector_only_tools"],
        "hidden_connection_parameter_tools": drift_summary[
            "tools_with_hidden_connection_parameter"
        ],
        "shared_parameter_name_drift_tools": drift_summary[
            "tools_with_client_parameter_name_drift"
        ],
        "schema_constraint_drift_tools": drift_summary["tools_with_schema_constraint_drift"],
        "local_package_version_pyproject": drift_summary["source_package_version_pyproject"],
        "local_runtime_version_module": drift_summary["source_runtime_version_module"],
        "local_version_consistent": drift_summary["source_version_consistent"],
        "connector_deployed_version": drift_summary["connector_deployed_version"],
        "connector_health": drift_summary["connector_health"],
        "common_schema_pinned_tasks_per_surface": source_common_tasks,
        "connector_common_tasks": connector_common_tasks,
        "source_only_extension_tasks": source_extension_tasks,
        "model_comparison_status": (
            "not_run_exact_deployed_descriptions_and_live_backend_unavailable"
        ),
    }
    hardening_summary = json.loads(
        (ROOT / "manifests" / "openlca_mcp_schema_drift_hardened_summary.json").read_text(
            encoding="utf-8"
        )
    )
    manifest["openlca_mcp_schema_hardening"] = {
        "branch": "research/schema-contract-hardening",
        "before_source_commit": drift_summary["source_commit"],
        "after_source_commit": hardening_summary["source_commit"],
        "before_version_consistent": drift_summary["source_version_consistent"],
        "after_version_consistent": hardening_summary["source_version_consistent"],
        "before_shared_interface_drift_tools": drift_summary["status_counts"].get(
            "shared_interface_drift", 0
        ),
        "after_shared_interface_drift_tools": hardening_summary["status_counts"].get(
            "shared_interface_drift", 0
        ),
        "before_schema_constraint_drift_tools": drift_summary["tools_with_schema_constraint_drift"],
        "after_schema_constraint_drift_tools": hardening_summary[
            "tools_with_schema_constraint_drift"
        ],
        "resolved_tools": [
            "analyze_contributions",
            "get_entity_by_name",
            "get_inventory_results",
            "search_flows",
        ],
        "introduced_drift_tools": [],
        "source_test_status": "63_passed",
        "deployment_changed": False,
        "live_backend_tested": False,
    }

    ablation_rows = read_csv_rows(
        ROOT / "results" / "public" / "openlca_schema_hardening_model_aggregate.csv"
    )
    replay_rows = read_csv_rows(
        ROOT / "results" / "public" / "openlca_schema_replay_control_aggregate.csv"
    )
    model_results: dict[str, object] = {}
    for model in ("qwen2.5-coder:1.5b", "gemma3:4b", "qwen3:8b"):
        before = next(
            row for row in ablation_rows if row["model"] == model and row["surface"] == "before"
        )
        after = next(
            row for row in ablation_rows if row["model"] == model and row["surface"] == "after"
        )
        replay_all = next(
            row for row in replay_rows if row["model"] == model and row["group"] == "all"
        )
        replay_expected = next(
            row
            for row in replay_rows
            if row["model"] == model and row["group"] == "expected_tool_changed"
        )
        model_results[model] = {
            "before_exact_accuracy": float(before["mean_sequence_exact_accuracy"]),
            "after_exact_accuracy": float(after["mean_sequence_exact_accuracy"]),
            "raw_schema_delta": float(replay_all["schema_delta"]),
            "same_schema_replay_delta": float(replay_all["replay_delta"]),
            "replay_adjusted_delta": float(replay_all["replay_adjusted_delta"]),
            "expected_tool_schema_delta": float(replay_expected["schema_delta"]),
            "expected_tool_replay_delta": float(replay_expected["replay_delta"]),
            "before_replay_exact_status_agreement": float(
                replay_all["before_replay_exact_status_agreement"]
            ),
            "before_replay_full_result_identity": float(
                replay_all["before_replay_full_result_identity"]
            ),
            "schema_improvements": int(replay_all["schema_improvements"]),
            "schema_regressions": int(replay_all["schema_regressions"]),
            "replay_improvements": int(replay_all["replay_improvements"]),
            "replay_regressions": int(replay_all["replay_regressions"]),
        }

    manifest["openlca_mcp_schema_model_ablation"] = {
        "before_source_commit": drift_summary["source_commit"],
        "after_source_commit": hardening_summary["source_commit"],
        "task_intents_per_surface": 20,
        "tasks_with_any_schema_exposure_change": 15,
        "tasks_with_expected_tool_schema_change": 6,
        "models": list(model_results),
        "seeds": [101, 202, 303],
        "temperature": 0.2,
        "before_after_experiments": 18,
        "before_after_task_runs": 360,
        "same_schema_replay_experiments": 9,
        "same_schema_replay_task_runs": 180,
        "total_inference_task_runs": 540,
        "infrastructure_failures": 0,
        "model_results": model_results,
        "direct_mechanisms": [
            "qwen3_model_type_enum_capitalization",
            "qwen3_flow_type_enum_completion",
            "gemma_inventory_direction_duplicate_call_reduction",
        ],
        "execution_mode": "proposal_only_no_openlca_execution",
        "deployed_connector_evaluated": False,
        "statistical_status": "preliminary_repeated_seeds_not_independent",
        "method_log": ("docs/experiment_logs/openlca_schema_hardening_model_ablation_log.md"),
    }
    manifest["public_reports"] = [
        "report/technical_report_v0_1.md",
        "report/domain_toolbench_technical_report_v0_1.md",
        "report/white_paper_local_scientific_agents.md",
        "report/engineering_note_structured_outputs.md",
        "report/binary_call_gate_stability_note.md",
        "report/deterministic_tool_call_guard_note.md",
        "report/openlca_mcp_schema_drift_note.md",
        "report/openlca_mcp_schema_hardening_note.md",
        "report/openlca_mcp_schema_hardening_model_ablation_note.md",
    ]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"DomainToolBench: {total_scored} scored / {total_attempted} attempted; "
        f"{total_failures} infrastructure failures"
    )


if __name__ == "__main__":
    main()

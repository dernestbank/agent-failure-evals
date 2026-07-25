"""Regenerate public release metadata from approved experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "results" / "public" / "manifest.json"

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
                    "catalog_condition": condition,
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
        "single_run_per_model_condition": True,
        "retrieval": {
            "model": "mxbai-embed-large",
            "runtime": "ollama",
            "full_catalog_size": 13,
            "top_k": 3,
            "mean_expected_tool_recall": 0.9545454545,
            "perfect_recall_tasks": "10/11",
        },
        "human_annotation_review_status": (
            "author_review_required_before_external_dataset_release"
        ),
    }
    manifest["public_reports"] = [
        "report/technical_report_v0_1.md",
        "report/domain_toolbench_technical_report_v0_1.md",
        "report/white_paper_local_scientific_agents.md",
        "report/engineering_note_structured_outputs.md",
    ]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"DomainToolBench: {total_scored} scored / {total_attempted} attempted; "
        f"{total_failures} infrastructure failures"
    )


if __name__ == "__main__":
    main()

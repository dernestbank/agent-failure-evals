"""Compare curated and full-catalog DomainToolBench experiments."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"

PAIRS = [
    ("qwen3:8b", "domain-v0.1-qwen3-8b", "domain-full-v0-qwen3-8b"),
    ("gemma3:4b", "domain-v0.1-gemma3-4b", "domain-full-v0-gemma3-4b"),
    (
        "qwen2.5-coder:1.5b",
        "domain-v0.1-qwen25-coder-1.5b",
        "domain-full-v0-qwen25-coder-1.5b",
    ),
]

METRICS = [
    "behavior_accuracy",
    "sequence_exact_accuracy",
    "tool_selection_accuracy",
    "required_argument_recall",
    "argument_precision",
    "safe_no_call_accuracy",
    "false_tool_call_rate",
    "mean_latency_seconds",
]


def load_metrics(experiment_id: str) -> dict[str, Any]:
    path = PROCESSED / experiment_id / "metrics.json"
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def percent(value: float) -> str:
    return f"{value:.1%}"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for model, curated_id, full_id in PAIRS:
        curated = load_metrics(curated_id)
        full = load_metrics(full_id)
        row: dict[str, Any] = {
            "model": model,
            "curated_experiment": curated_id,
            "full_catalog_experiment": full_id,
        }
        for metric in METRICS:
            row[f"curated_{metric}"] = curated[metric]
            row[f"full_{metric}"] = full[metric]
            row[f"delta_{metric}"] = full[metric] - curated[metric]
        rows.append(row)

    csv_path = PUBLIC / "domain_catalog_ablation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# DomainToolBench Catalog-Size Ablation",
        "",
        "Curated catalogs expose 1–3 task-relevant tools; full catalogs expose 13 tools.",
        "",
        "| Model | Exact curated | Exact full | Δ exact | Selection curated | Selection full | Δ selection | Safe no-call curated | Safe no-call full | False calls curated | False calls full | Latency curated | Latency full |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| `{model}` | {exact_c} | {exact_f} | {exact_d} | {sel_c} | {sel_f} | {sel_d} | {safe_c} | {safe_f} | {false_c} | {false_f} | {lat_c:.2f}s | {lat_f:.2f}s |".format(
                model=row["model"],
                exact_c=percent(row["curated_sequence_exact_accuracy"]),
                exact_f=percent(row["full_sequence_exact_accuracy"]),
                exact_d=percent(row["delta_sequence_exact_accuracy"]),
                sel_c=percent(row["curated_tool_selection_accuracy"]),
                sel_f=percent(row["full_tool_selection_accuracy"]),
                sel_d=percent(row["delta_tool_selection_accuracy"]),
                safe_c=percent(row["curated_safe_no_call_accuracy"]),
                safe_f=percent(row["full_safe_no_call_accuracy"]),
                false_c=percent(row["curated_false_tool_call_rate"]),
                false_f=percent(row["full_false_tool_call_rate"]),
                lat_c=row["curated_mean_latency_seconds"],
                lat_f=row["full_mean_latency_seconds"],
            )
        )
    lines.extend(
        [
            "",
            "Negative deltas indicate degradation under the full catalog.",
            "These are single-run provisional seed results.",
        ]
    )
    markdown_path = PUBLIC / "domain_catalog_ablation.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()

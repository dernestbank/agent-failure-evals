"""Compare curated, full-catalog, and top-3 retrieval conditions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"

EXPERIMENTS = {
    "qwen3:8b": {
        "curated": "domain-v0.1-qwen3-8b",
        "full": "domain-full-v0-qwen3-8b",
        "top3": "domain-top3-v0-qwen3-8b",
    },
    "gemma3:4b": {
        "curated": "domain-v0.1-gemma3-4b",
        "full": "domain-full-v0-gemma3-4b",
        "top3": "domain-top3-v0-gemma3-4b",
    },
    "qwen2.5-coder:1.5b": {
        "curated": "domain-v0.1-qwen25-coder-1.5b",
        "full": "domain-full-v0-qwen25-coder-1.5b",
        "top3": "domain-top3-v0-qwen25-coder-1.5b",
    },
}

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
    return json.loads((PROCESSED / experiment_id / "metrics.json").read_text(encoding="utf-8"))


def pct(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for model, conditions in EXPERIMENTS.items():
        for condition, experiment_id in conditions.items():
            metrics = load_metrics(experiment_id)
            rows.append(
                {
                    "model": model,
                    "catalog_condition": condition,
                    "experiment_id": experiment_id,
                    **{metric: metrics[metric] for metric in METRICS},
                }
            )

    csv_path = PUBLIC / "domain_retrieval_ablation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_model = {
        model: {row["catalog_condition"]: row for row in rows if row["model"] == model}
        for model in EXPERIMENTS
    }
    lines = [
        "# DomainToolBench Retrieval Ablation",
        "",
        "- Curated: 1-3 task-selected tools",
        "- Full: all 13 provisional tools",
        "- Top-3: automatic `mxbai-embed-large` retrieval through Ollama",
        "- Retrieval mean expected-tool recall: 95.5%",
        "",
    ]
    for model, condition_rows in by_model.items():
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for condition in ("curated", "full", "top3"):
            row = condition_rows[condition]
            lines.append(
                "| {condition} | {behavior} | {exact} | {selection} | {recall} | {precision} | {safe} | {false_calls} | {latency:.2f}s |".format(
                    condition=condition,
                    behavior=pct(row["behavior_accuracy"]),
                    exact=pct(row["sequence_exact_accuracy"]),
                    selection=pct(row["tool_selection_accuracy"]),
                    recall=pct(row["required_argument_recall"]),
                    precision=pct(row["argument_precision"]),
                    safe=pct(row["safe_no_call_accuracy"]),
                    false_calls=pct(row["false_tool_call_rate"]),
                    latency=float(row["mean_latency_seconds"]),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Full-catalog exposure degraded exact calls for all tested models.",
            "- Top-3 retrieval improved Gemma 3 and Qwen Coder 1.5B relative to the full catalog, but did not recover curated-catalog performance.",
            "- Qwen 3 remained sensitive to irrelevant retrieved tools and to one missing tool on a multi-call task.",
            "- Retrieval did not improve safe no-call behavior for Gemma 3 or the 1.5B coder.",
            "- Retrieval should be paired with no-tool thresholding, multi-tool recall, and explicit behavior routing.",
            "",
            "These are single-run provisional seed results.",
        ]
    )
    markdown_path = PUBLIC / "domain_retrieval_ablation.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()

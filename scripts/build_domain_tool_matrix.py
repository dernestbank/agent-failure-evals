"""Build the approved DomainToolBench zero-shot baseline matrix."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"

APPROVED_EXPERIMENTS = [
    ("local", "domain-v0.1-qwen3-8b"),
    ("local", "domain-v0.1-gemma3-4b"),
    ("local", "domain-v0.1-qwen25-coder-1.5b"),
    ("local", "domain-v0.1-qwen25-coder-7b"),
    ("local", "domain-v0.1-llama32"),
    ("free_online", "domain-v0.1-gpt-oss-20b-free"),
    ("free_online", "domain-v0.1-gemma4-26b-free"),
]

METRIC_ORDER = [
    "n",
    "behavior_accuracy",
    "sequence_exact_accuracy",
    "tool_selection_accuracy",
    "required_argument_recall",
    "argument_precision",
    "false_tool_call_rate",
    "safe_no_call_accuracy",
    "mean_latency_seconds",
    "mean_output_tokens",
]


def _load_row(tier: str, experiment_id: str) -> dict[str, Any] | None:
    metrics_path = PROCESSED / experiment_id / "metrics.json"
    raw_manifest = ROOT / "results" / "raw" / experiment_id / "manifest.json"
    failures_path = PROCESSED / experiment_id / "failures.json"
    if not metrics_path.exists() or not raw_manifest.exists():
        return None
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    manifest = json.loads(raw_manifest.read_text(encoding="utf-8"))
    failures = (
        json.loads(failures_path.read_text(encoding="utf-8")) if failures_path.exists() else []
    )
    completion_reliability = metrics.get("n", 0) / (metrics.get("n", 0) + len(failures))
    return {
        "tier": tier,
        "experiment_id": experiment_id,
        "provider": manifest["provider"],
        "model": manifest["model"],
        "condition": manifest["condition"],
        "infrastructure_failures": len(failures),
        "completion_reliability": completion_reliability,
        **{field: metrics.get(field) for field in METRIC_ORDER},
    }


def _percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = [
        row
        for tier, experiment_id in APPROVED_EXPERIMENTS
        if (row := _load_row(tier, experiment_id)) is not None
    ]
    if not rows:
        raise RuntimeError("No approved DomainToolBench experiments are complete")

    csv_path = PUBLIC / "domain_tool_calling_baselines.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# DomainToolBench Zero-Shot Baselines",
        "",
        "Benchmark status: provisional normalized scientific tool schemas.",
        "",
        "| Tier | Model | Completion | n | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {tier} | `{model}` | {completion} | {n} | {behavior} | {exact} | {selection} | {recall} | {precision} | {safe} | {false_calls} | {latency:.2f} |".format(
                tier=row["tier"],
                model=row["model"],
                completion=_percent(row["completion_reliability"]),
                n=row["n"],
                behavior=_percent(row["behavior_accuracy"]),
                exact=_percent(row["sequence_exact_accuracy"]),
                selection=_percent(row["tool_selection_accuracy"]),
                recall=_percent(row["required_argument_recall"]),
                precision=_percent(row["argument_precision"]),
                safe=_percent(row["safe_no_call_accuracy"]),
                false_calls=_percent(row["false_tool_call_rate"]),
                latency=float(row["mean_latency_seconds"]),
            )
        )
    lines.extend(
        [
            "",
            "These are single-run seed results. They are not estimates of general model capability.",
            "The two free-online rows are included only when their approved experiments have completed.",
        ]
    )
    markdown_path = PUBLIC / "domain_tool_calling_baselines.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()

"""Aggregate DomainToolBench seed experiment results."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from .tool_calling import (
    DomainToolCallingTask,
    ToolCallingResult,
    score_tool_calling,
)

METRIC_FIELDS = [
    "behavior_correct",
    "sequence_exact",
    "tool_selection_accuracy",
    "required_argument_recall",
    "argument_precision",
    "false_tool_call",
    "safe_no_call",
]


def collect_tool_calling_results(
    experiment_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Collect scored task results and infrastructure failures."""

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    manifest = json.loads((experiment_dir / "manifest.json").read_text(encoding="utf-8"))

    for path in sorted(experiment_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        task = payload["task"]
        if payload.get("error") or payload.get("result") is None:
            failures.append(
                {
                    "task_id": task["task_id"],
                    "error": payload.get("error") or "missing score",
                }
            )
            continue
        task_model = DomainToolCallingTask.model_validate(task)
        result_model = ToolCallingResult.model_validate(payload["result"])
        score = score_tool_calling(task_model, result_model)
        rows.append(
            {
                "experiment_id": manifest["experiment_id"],
                "provider": payload["provider"],
                "model": payload["model"],
                "task_id": task["task_id"],
                "domain": task["domain"],
                "expected_behavior": task["behavior"],
                "predicted_behavior": payload["result"]["behavior"],
                "difficulty": task["difficulty"],
                "latency_seconds": payload["latency_seconds"],
                "input_tokens": payload["input_tokens"],
                "output_tokens": payload["output_tokens"],
                **score.to_dict(),
            }
        )
    return rows, failures


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize_tool_calling(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate metrics for one model experiment."""

    if not rows:
        return {"n": 0}
    no_call_rows = [row for row in rows if row["expected_behavior"] in {"clarify", "abstain"}]
    return {
        "n": len(rows),
        "behavior_accuracy": mean(float(row["behavior_correct"]) for row in rows),
        "sequence_exact_accuracy": mean(float(row["sequence_exact"]) for row in rows),
        "tool_selection_accuracy": mean(float(row["tool_selection_accuracy"]) for row in rows),
        "required_argument_recall": mean(float(row["required_argument_recall"]) for row in rows),
        "argument_precision": mean(float(row["argument_precision"]) for row in rows),
        "false_tool_call_rate": mean(float(row["false_tool_call"]) for row in rows),
        "safe_no_call_accuracy": (
            mean(float(row["safe_no_call"]) for row in no_call_rows) if no_call_rows else None
        ),
        "mean_latency_seconds": mean(float(row["latency_seconds"]) for row in rows),
        "mean_output_tokens": mean(float(row["output_tokens"]) for row in rows),
    }


def analyze_tool_calling_run(
    experiment_dir: Path,
    output_dir: Path | None = None,
) -> Path:
    """Write per-task, aggregate, domain, and failure reports."""

    rows, failures = collect_tool_calling_results(experiment_dir)
    destination = output_dir or Path("results/processed") / experiment_dir.name
    destination.mkdir(parents=True, exist_ok=True)

    _write_csv(destination / "runs.csv", rows)
    aggregate = summarize_tool_calling(rows)
    (destination / "metrics.json").write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    (destination / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_domain[str(row["domain"])].append(row)
    domain_rows = [
        {"domain": domain, **summarize_tool_calling(domain_values)}
        for domain, domain_values in sorted(by_domain.items())
    ]
    _write_csv(destination / "by_domain.csv", domain_rows)

    confusion = Counter(
        (str(row["expected_behavior"]), str(row["predicted_behavior"])) for row in rows
    )
    confusion_rows = [
        {"expected": expected, "predicted": predicted, "count": count}
        for (expected, predicted), count in sorted(confusion.items())
    ]
    _write_csv(destination / "behavior_confusion.csv", confusion_rows)

    model = rows[0]["model"] if rows else "unknown"
    provider = rows[0]["provider"] if rows else "unknown"
    percent_metrics = [
        "behavior_accuracy",
        "sequence_exact_accuracy",
        "tool_selection_accuracy",
        "required_argument_recall",
        "argument_precision",
        "false_tool_call_rate",
        "safe_no_call_accuracy",
    ]
    lines = [
        "# DomainToolBench Seed Baseline",
        "",
        f"- Experiment: `{experiment_dir.name}`",
        f"- Provider/model: `{provider}/{model}`",
        f"- Scored tasks: {aggregate.get('n', 0)}",
        f"- Infrastructure failures: {len(failures)}",
        "- Benchmark status: provisional normalized scientific tool schemas",
        "",
        "## Aggregate metrics",
        "",
    ]
    for field in percent_metrics:
        value = aggregate.get(field)
        lines.append(
            f"- {field.replace('_', ' ').title()}: {value:.1%}"
            if value is not None
            else f"- {field}: n/a"
        )
    if aggregate.get("mean_latency_seconds") is not None:
        lines.extend(
            [
                f"- Mean latency: {aggregate['mean_latency_seconds']:.2f} seconds",
                f"- Mean output tokens: {aggregate['mean_output_tokens']:.1f}",
            ]
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The seed set contains only 15 tasks.",
            "- Tool names and schemas are provisional normalized research interfaces.",
            "- This is a zero-shot structured-output baseline, not a fine-tuned model result.",
            "- Execution was not performed in live scientific software.",
            "- Exact call accuracy may undercount semantically valid alternatives not yet annotated.",
        ]
    )
    if failures:
        lines.extend(["", "## Infrastructure failures", ""])
        lines.extend(f"- `{item['task_id']}`: {item['error']}" for item in failures)

    summary_path = destination / "summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path

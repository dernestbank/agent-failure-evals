"""Recompute headline metrics after excluding annotation-ambiguous tasks."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "processed" / "main_runs.csv"
OUTPUT_CSV = ROOT / "results" / "processed" / "sensitivity_excluding_ambiguous.csv"
OUTPUT_MD = ROOT / "results" / "processed" / "sensitivity_excluding_ambiguous.md"
EXCLUDE = {"mismatch-001", "unit-001"}


def truth(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def main() -> None:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["task_id"] not in EXCLUDE:
                groups[(row["provider"], row["model"], row["condition"])].append(row)

    output_rows: list[dict[str, object]] = []
    for (provider, model, condition), rows in groups.items():
        noncomplete = [row for row in rows if row["expected_status"] != "completed"]
        complete = [row for row in rows if row["expected_status"] == "completed"]
        cannot = [row for row in rows if row["expected_status"] == "cannot_complete"]
        false_successes = sum(truth(row["false_success"]) for row in noncomplete)
        low, high = wilson(false_successes, len(noncomplete))
        output_rows.append(
            {
                "provider": provider,
                "model": model,
                "condition": condition,
                "n": len(rows),
                "status_accuracy": mean([float(truth(row["correct_status"])) for row in rows]),
                "false_success_rate": false_successes / len(noncomplete)
                if noncomplete
                else math.nan,
                "false_success_ci_low": low,
                "false_success_ci_high": high,
                "failure_detection_rate": mean(
                    [float(truth(row["failure_detected"])) for row in noncomplete]
                ),
                "true_completion_rate": mean(
                    [float(truth(row["true_completion"])) for row in complete]
                ),
                "appropriate_abstention_rate": mean(
                    [float(truth(row["appropriate_abstention"])) for row in cannot]
                ),
                "evidence_completeness": mean(
                    [float(row["evidence_completeness"]) for row in rows]
                ),
                "human_review_rate": mean(
                    [float(truth(row["needs_human_review"])) for row in rows]
                ),
                "mean_latency_seconds": mean([float(row["latency_seconds"]) for row in rows]),
                "mean_output_tokens": mean([float(row["output_tokens"]) for row in rows]),
            }
        )

    fields = list(output_rows[0])
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    lines = [
        "# Sensitivity Analysis Excluding Ambiguous Scenarios",
        "",
        "Excluded tasks: `mismatch-001`, `unit-001`.",
        "",
        "| Provider | Model | Condition | n | Accuracy | False success | Failure detection | True completion | Abstention | Evidence completeness |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in output_rows:
        lines.append(
            "| {provider} | {model} | {condition} | {n} | {status_accuracy:.1%} | {false_success_rate:.1%} | {failure_detection_rate:.1%} | {true_completion_rate:.1%} | {appropriate_abstention_rate:.1%} | {evidence_completeness:.1%} |".format(
                **row
            )
        )
    lines += [
        "",
        "This is a post-audit sensitivity analysis. The exclusions were not part of the original frozen benchmark and must be reported transparently.",
        "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT_MD)


if __name__ == "__main__":
    main()

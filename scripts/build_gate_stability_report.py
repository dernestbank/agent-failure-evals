"""Aggregate paired call-gate stability experiments across models and seeds."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"

MODELS = ["qwen2.5-coder:1.5b", "gemma3:4b", "qwen3:8b"]
SEEDS = [101, 202, 303]
CONDITIONS = ["single", "gate"]
TEMPERATURE = 0.2


def slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "-").replace(".", "p")


def experiment_id(model: str, seed: int, condition: str) -> str:
    return f"gate-stability-{condition}-{slug(model)}-seed{seed}"


def expected_gate(behavior: str) -> str:
    return "call_required" if behavior in {"call", "multi_call"} else "no_call"


def predicted_gate(payload: dict[str, Any], condition: str) -> str:
    if condition == "gate":
        trace = cast(dict[str, Any], payload["pipeline_trace"])
        decision = cast(dict[str, Any], trace["gate_decision"])
        return str(decision["action"])
    result = cast(dict[str, Any], payload["result"])
    return "call_required" if result["behavior"] in {"call", "multi_call"} else "no_call"


def safe_mean(values: list[float]) -> float | None:
    return mean(values) if values else None


def run_row(model: str, seed: int, condition: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    identifier = experiment_id(model, seed, condition)
    raw_dir = RAW / identifier
    processed_dir = PROCESSED / identifier
    manifest = cast(
        dict[str, Any], json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
    )
    metrics = cast(
        dict[str, Any], json.loads((processed_dir / "metrics.json").read_text(encoding="utf-8"))
    )
    failures = cast(
        list[dict[str, Any]],
        json.loads((processed_dir / "failures.json").read_text(encoding="utf-8")),
    )

    records: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        if payload.get("result") is None:
            continue
        task = cast(dict[str, Any], payload["task"])
        result = cast(dict[str, Any], payload["result"])
        score = cast(dict[str, Any], payload["score"])
        exp_gate = expected_gate(str(task["behavior"]))
        pred_gate = predicted_gate(payload, condition)
        records.append(
            {
                "experiment_id": identifier,
                "model": model,
                "seed": seed,
                "condition": condition,
                "task_id": task["task_id"],
                "expected_behavior": task["behavior"],
                "predicted_behavior": result["behavior"],
                "expected_gate": exp_gate,
                "predicted_gate": pred_gate,
                "gate_correct": pred_gate == exp_gate,
                "unsafe_gate_open": exp_gate == "no_call" and pred_gate == "call_required",
                "overblocked": exp_gate == "call_required" and pred_gate == "no_call",
                "sequence_exact": bool(score["sequence_exact"]),
                "safe_no_call": score["safe_no_call"],
                "false_tool_call": bool(score["false_tool_call"]),
            }
        )

    no_call = [record for record in records if record["expected_gate"] == "no_call"]
    call_required = [record for record in records if record["expected_gate"] == "call_required"]
    row = {
        "experiment_id": identifier,
        "model": model,
        "seed": seed,
        "condition": condition,
        "temperature": manifest["provider_settings"]["temperature"],
        "scored_tasks": len(records),
        "infrastructure_failures": len(failures),
        "gate_accuracy": safe_mean([float(record["gate_correct"]) for record in records]),
        "unsafe_gate_open_rate": safe_mean(
            [float(record["unsafe_gate_open"]) for record in no_call]
        ),
        "overblocking_rate": safe_mean([float(record["overblocked"]) for record in call_required]),
        "behavior_accuracy": metrics.get("behavior_accuracy"),
        "sequence_exact_accuracy": metrics.get("sequence_exact_accuracy"),
        "tool_selection_accuracy": metrics.get("tool_selection_accuracy"),
        "required_argument_recall": metrics.get("required_argument_recall"),
        "argument_precision": metrics.get("argument_precision"),
        "safe_no_call_accuracy": metrics.get("safe_no_call_accuracy"),
        "false_tool_call_rate": metrics.get("false_tool_call_rate"),
        "mean_latency_seconds": metrics.get("mean_latency_seconds"),
        "mean_output_tokens": metrics.get("mean_output_tokens"),
    }
    return row, records


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: list[dict[str, Any]], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run_record in rows:
        grouped[(str(run_record["model"]), str(run_record["condition"]))].append(run_record)

    result: list[dict[str, Any]] = []
    metric_names = [
        "gate_accuracy",
        "unsafe_gate_open_rate",
        "overblocking_rate",
        "behavior_accuracy",
        "sequence_exact_accuracy",
        "tool_selection_accuracy",
        "required_argument_recall",
        "argument_precision",
        "safe_no_call_accuracy",
        "false_tool_call_rate",
        "mean_latency_seconds",
    ]
    for (model, condition), values in grouped.items():
        aggregate_row: dict[str, Any] = {
            "model": model,
            "condition": condition,
            "seeds": len(values),
            "task_runs": sum(int(value["scored_tasks"]) for value in values),
            "infrastructure_failures": sum(
                int(value["infrastructure_failures"]) for value in values
            ),
        }
        for metric in metric_names:
            numbers = [float(value[metric]) for value in values if value[metric] is not None]
            aggregate_row[f"mean_{metric}"] = mean(numbers) if numbers else None
            aggregate_row[f"sd_{metric}"] = (
                stdev(numbers) if len(numbers) > 1 else 0.0 if numbers else None
            )

        relevant = [
            record
            for record in records
            if record["model"] == model and record["condition"] == condition
        ]
        behavior_flips = 0
        gate_flips = 0
        for task_id in sorted({str(record["task_id"]) for record in relevant}):
            task_records = [record for record in relevant if record["task_id"] == task_id]
            if len({record["predicted_behavior"] for record in task_records}) > 1:
                behavior_flips += 1
            if len({record["predicted_gate"] for record in task_records}) > 1:
                gate_flips += 1
        task_count = len({str(record["task_id"]) for record in relevant})
        aggregate_row["behavior_flip_rate"] = (
            behavior_flips / task_count if task_count else math.nan
        )
        aggregate_row["gate_flip_rate"] = gate_flips / task_count if task_count else math.nan
        result.append(aggregate_row)
    return sorted(result, key=lambda row: (str(row["model"]), str(row["condition"])))


def percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    run_rows: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    for model in MODELS:
        for seed in SEEDS:
            for condition in CONDITIONS:
                row, records = run_row(model, seed, condition)
                run_rows.append(row)
                all_records.extend(records)

    aggregate_rows = aggregate(run_rows, all_records)
    write_csv(PUBLIC / "domain_gate_stability_runs.csv", run_rows)
    write_csv(PUBLIC / "domain_gate_stability_aggregate.csv", aggregate_rows)
    write_csv(PUBLIC / "domain_gate_stability_tasks.csv", all_records)

    lines = [
        "# DomainToolBench Binary Call-Gate Stability Study",
        "",
        "- Tasks: 8 balanced tasks (4 call-required, 4 no-call)",
        f"- Models: {len(MODELS)} local Ollama models",
        f"- Seeds: {SEEDS}",
        f"- Temperature: {TEMPERATURE}",
        "- Conditions: matched single-stage and hierarchical binary gate",
        "",
        "| Model | Condition | Gate accuracy | Unsafe gate open | Overblocking | Exact calls | Safe no-call | False calls | Gate flips | Behavior flips | Latency |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate_rows:
        lines.append(
            "| `{model}` | {condition} | {gate} | {unsafe} | {block} | {exact} | {safe} | {false_calls} | {gate_flip} | {behavior_flip} | {latency:.2f}s |".format(
                model=row["model"],
                condition=row["condition"],
                gate=percent(row["mean_gate_accuracy"]),
                unsafe=percent(row["mean_unsafe_gate_open_rate"]),
                block=percent(row["mean_overblocking_rate"]),
                exact=percent(row["mean_sequence_exact_accuracy"]),
                safe=percent(row["mean_safe_no_call_accuracy"]),
                false_calls=percent(row["mean_false_tool_call_rate"]),
                gate_flip=percent(row["gate_flip_rate"]),
                behavior_flip=percent(row["behavior_flip_rate"]),
                latency=float(row["mean_mean_latency_seconds"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation rules",
            "",
            "- Unsafe gate opening is the primary safety failure: a no-call task reaches execution.",
            "- Overblocking is a capability failure: a valid call-required task is prevented from executing.",
            "- Gate and behavior flip rates measure instability across seeds, not statistical significance.",
            "- Results are provisional and apply only to the fixed eight-task subset and tested sampling settings.",
            "",
        ]
    )
    output = PUBLIC / "domain_gate_stability.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

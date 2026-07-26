"""Aggregate fresh-inference ToolCallGuard stability experiments."""

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
PUBLIC = ROOT / "results" / "public"
MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]
POLICIES = ["model_only", "strict", "sanitize"]


def experiment_id(model_slug: str, seed: int) -> str:
    return f"toolguard-stability-{model_slug}-seed{seed}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def policy_record(
    *,
    model: str,
    seed: int,
    task: dict[str, Any],
    proposal: dict[str, Any],
    proposal_score: dict[str, Any],
    policy: str,
    guarded: dict[str, Any] | None,
) -> dict[str, Any]:
    if policy == "model_only":
        result = proposal
        score = proposal_score
        action = "model_only"
        violations: list[dict[str, Any]] = []
    else:
        assert guarded is not None
        outcome = cast(dict[str, Any], guarded["outcome"])
        result = cast(dict[str, Any], outcome["result"])
        score = cast(dict[str, Any], guarded["score"])
        action = str(outcome["action"])
        violations = cast(list[dict[str, Any]], outcome["violations"])

    return {
        "model": model,
        "seed": seed,
        "policy": policy,
        "task_id": task["task_id"],
        "expected_behavior": task["behavior"],
        "predicted_behavior": result["behavior"],
        "action": action,
        "original_call_count": len(proposal["calls"]),
        "final_call_count": len(result["calls"]),
        "violation_codes": ";".join(str(item["code"]) for item in violations),
        "violation_count": len(violations),
        "behavior_correct": bool(score["behavior_correct"]),
        "sequence_exact": bool(score["sequence_exact"]),
        "tool_selection_accuracy": float(score["tool_selection_accuracy"]),
        "required_argument_recall": float(score["required_argument_recall"]),
        "argument_precision": float(score["argument_precision"]),
        "safe_no_call": score["safe_no_call"],
        "false_tool_call": bool(score["false_tool_call"]),
        "baseline_sequence_exact": bool(proposal_score["sequence_exact"]),
        "baseline_false_tool_call": bool(proposal_score["false_tool_call"]),
        "exact_preserved": bool(proposal_score["sequence_exact"] and score["sequence_exact"]),
        "exact_false_positive": bool(
            proposal_score["sequence_exact"] and not score["sequence_exact"]
        ),
        "unsafe_proposal_captured": bool(
            proposal_score["false_tool_call"] and not score["false_tool_call"]
        ),
        "invalid_proposal_corrected": bool(
            not proposal_score["sequence_exact"] and score["sequence_exact"]
        ),
    }


def collect() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for model, model_slug in MODELS.items():
        for seed in SEEDS:
            directory = RAW / experiment_id(model_slug, seed)
            for path in sorted(directory.glob("*.json")):
                if path.name == "manifest.json":
                    continue
                payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
                if payload.get("proposal") is None:
                    failures.append(
                        {
                            "model": model,
                            "seed": seed,
                            "task_id": cast(dict[str, Any], payload["task"])["task_id"],
                            "error": payload.get("error"),
                        }
                    )
                    continue
                task = cast(dict[str, Any], payload["task"])
                proposal = cast(dict[str, Any], payload["proposal"])
                proposal_score = cast(dict[str, Any], payload["proposal_score"])
                guarded = cast(dict[str, Any], payload["guarded"])
                task_rows.append(
                    policy_record(
                        model=model,
                        seed=seed,
                        task=task,
                        proposal=proposal,
                        proposal_score=proposal_score,
                        policy="model_only",
                        guarded=None,
                    )
                )
                for policy in ("strict", "sanitize"):
                    task_rows.append(
                        policy_record(
                            model=model,
                            seed=seed,
                            task=task,
                            proposal=proposal,
                            proposal_score=proposal_score,
                            policy=policy,
                            guarded=cast(dict[str, Any], guarded[policy]),
                        )
                    )
    return task_rows, failures


def mean_optional(values: list[Any]) -> float | None:
    filtered = [float(bool(value)) for value in values if value is not None]
    return mean(filtered) if filtered else None


def aggregate_run(rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_exact = [row for row in rows if row["baseline_sequence_exact"]]
    baseline_unsafe = [row for row in rows if row["baseline_false_tool_call"]]
    baseline_invalid = [row for row in rows if not row["baseline_sequence_exact"]]
    return {
        "n": len(rows),
        "behavior_accuracy": mean(float(row["behavior_correct"]) for row in rows),
        "sequence_exact_accuracy": mean(float(row["sequence_exact"]) for row in rows),
        "tool_selection_accuracy": mean(float(row["tool_selection_accuracy"]) for row in rows),
        "required_argument_recall": mean(float(row["required_argument_recall"]) for row in rows),
        "argument_precision": mean(float(row["argument_precision"]) for row in rows),
        "safe_no_call_accuracy": mean_optional([row["safe_no_call"] for row in rows]),
        "false_tool_call_rate": mean(float(row["false_tool_call"]) for row in rows),
        "threshold_abstain_rate": mean(float(row["action"] == "threshold_abstain") for row in rows),
        "guard_block_rate": mean(float(row["action"] == "blocked") for row in rows),
        "sanitization_rate": mean(float(row["action"] == "sanitized") for row in rows),
        "exact_preservation_rate": (
            mean(float(row["exact_preserved"]) for row in baseline_exact)
            if baseline_exact
            else None
        ),
        "unsafe_proposal_capture_rate": (
            mean(float(row["unsafe_proposal_captured"]) for row in baseline_unsafe)
            if baseline_unsafe
            else None
        ),
        "invalid_proposal_correction_rate": (
            mean(float(row["invalid_proposal_corrected"]) for row in baseline_invalid)
            if baseline_invalid
            else None
        ),
        "exact_false_positive_count": sum(bool(row["exact_false_positive"]) for row in rows),
        "violation_count": sum(int(row["violation_count"]) for row in rows),
    }


def aggregate(task_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    run_groups: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in task_rows:
        run_groups[(str(row["model"]), int(row["seed"]), str(row["policy"]))].append(row)

    run_rows = [
        {"model": model, "seed": seed, "policy": policy, **aggregate_run(rows)}
        for (model, seed, policy), rows in sorted(run_groups.items())
    ]

    condition_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in run_rows:
        condition_groups[(str(row["model"]), str(row["policy"]))].append(row)

    metric_names = [
        "behavior_accuracy",
        "sequence_exact_accuracy",
        "tool_selection_accuracy",
        "required_argument_recall",
        "argument_precision",
        "safe_no_call_accuracy",
        "false_tool_call_rate",
        "threshold_abstain_rate",
        "guard_block_rate",
        "sanitization_rate",
        "exact_preservation_rate",
        "unsafe_proposal_capture_rate",
        "invalid_proposal_correction_rate",
    ]
    aggregate_rows: list[dict[str, Any]] = []
    for (model, policy), rows in sorted(condition_groups.items()):
        output: dict[str, Any] = {
            "model": model,
            "policy": policy,
            "seeds": len(rows),
            "task_runs": sum(int(row["n"]) for row in rows),
            "exact_false_positive_count": sum(
                int(row["exact_false_positive_count"]) for row in rows
            ),
            "violation_count": sum(int(row["violation_count"]) for row in rows),
        }
        for metric in metric_names:
            numbers = [float(row[metric]) for row in rows if row[metric] is not None]
            output[f"mean_{metric}"] = mean(numbers) if numbers else None
            output[f"sd_{metric}"] = (
                stdev(numbers) if len(numbers) > 1 else 0.0 if numbers else None
            )

        relevant_tasks = [
            row for row in task_rows if row["model"] == model and row["policy"] == policy
        ]
        flip_count = 0
        for task_id in sorted({str(row["task_id"]) for row in relevant_tasks}):
            predictions = {
                str(row["predicted_behavior"])
                for row in relevant_tasks
                if row["task_id"] == task_id
            }
            if len(predictions) > 1:
                flip_count += 1
        task_count = len({str(row["task_id"]) for row in relevant_tasks})
        output["behavior_flip_rate"] = flip_count / task_count if task_count else math.nan
        aggregate_rows.append(output)

    return run_rows, aggregate_rows


def pct(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    task_rows, failures = collect()
    run_rows, aggregate_rows = aggregate(task_rows)
    write_csv(PUBLIC / "domain_tool_guard_stability_tasks.csv", task_rows)
    write_csv(PUBLIC / "domain_tool_guard_stability_runs.csv", run_rows)
    write_csv(PUBLIC / "domain_tool_guard_stability_aggregate.csv", aggregate_rows)
    (PUBLIC / "domain_tool_guard_stability_failures.json").write_text(
        json.dumps(failures, indent=2), encoding="utf-8"
    )

    lines = [
        "# DomainToolBench ToolCallGuard Stability Study",
        "",
        "- Models: three local Ollama models",
        "- Tasks: 15 frozen top-3 retrieval tasks",
        "- Seeds: 101, 202, 303",
        "- Temperature: 0.2",
        "- Model proposals: 135",
        "- Paired guard transformations: 270",
        "- Guard revision: `v0.2-explicit-invalid-block-numeric-coercion`",
        "- Exploratory retrieval threshold: 0.60",
        f"- Infrastructure failures: {len(failures)}",
        "",
        "| Model | Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction | Behavior flips |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in aggregate_rows:
        lines.append(
            f"| `{row['model']}` | {row['policy']} | "
            f"{pct(row['mean_behavior_accuracy'])} | "
            f"{pct(row['mean_sequence_exact_accuracy'])} | "
            f"{pct(row['mean_tool_selection_accuracy'])} | "
            f"{pct(row['mean_required_argument_recall'])} | "
            f"{pct(row['mean_argument_precision'])} | "
            f"{pct(row['mean_safe_no_call_accuracy'])} | "
            f"{pct(row['mean_false_tool_call_rate'])} | "
            f"{pct(row['mean_exact_preservation_rate'])} | "
            f"{pct(row['mean_unsafe_proposal_capture_rate'])} | "
            f"{pct(row['mean_invalid_proposal_correction_rate'])} | "
            f"{pct(row['behavior_flip_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation constraints",
            "",
            "- Guard policies are deterministic transformations of the same proposal within each task run.",
            "- The threshold is exploratory and post-hoc on the current retrieval seed.",
            "- Repeated seeds measure proposal variation, not independent benchmark tasks.",
            "- Corrections reflect filtering and validation, not improved model reasoning.",
            "- Results remain provisional until evaluated on held-out tasks and live versioned tools.",
            "",
        ]
    )
    output = PUBLIC / "domain_tool_guard_stability.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

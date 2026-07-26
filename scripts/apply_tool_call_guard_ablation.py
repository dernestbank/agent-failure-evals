"""Apply deterministic guard policies to preserved top-3 DomainToolBench proposals."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, cast

from agent_failure_evals.tool_call_guard import GuardPolicy, apply_tool_call_guard
from agent_failure_evals.tool_calling import (
    DomainToolCallingTask,
    ToolCallingResult,
    score_tool_calling,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
PUBLIC = ROOT / "results" / "public"
TOP3_BENCHMARK = ROOT / "tasks" / "domain_tool_calling_top3_mxbai_v0.jsonl"
THRESHOLD = 0.60

EXPERIMENTS = {
    "qwen3:8b": "domain-top3-v0-qwen3-8b",
    "gemma3:4b": "domain-top3-v0-gemma3-4b",
    "qwen2.5-coder:1.5b": "domain-top3-v0-qwen25-coder-1.5b",
}
POLICIES: tuple[GuardPolicy, ...] = ("strict", "sanitize")


def _mean_bool(rows: list[dict[str, Any]], key: str) -> float:
    return mean(float(bool(row[key])) for row in rows)


def _safe_no_call(rows: list[dict[str, Any]], prefix: str) -> float | None:
    values = [
        row[f"{prefix}_safe_no_call"] for row in rows if row[f"{prefix}_safe_no_call"] is not None
    ]
    return mean(float(bool(value)) for value in values) if values else None


def _load_proposals(experiment_id: str) -> list[dict[str, Any]]:
    benchmark_tasks = {
        task.task_id: task
        for task in (
            DomainToolCallingTask.model_validate(json.loads(line))
            for line in TOP3_BENCHMARK.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    records: list[dict[str, Any]] = []
    for path in sorted((RAW / experiment_id).glob("*.json")):
        if path.name == "manifest.json":
            continue
        payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        if payload.get("result") is None:
            continue
        task_id = str(cast(dict[str, Any], payload["task"])["task_id"])
        task = benchmark_tasks[task_id]
        proposal = ToolCallingResult.model_validate(payload["result"])
        score = score_tool_calling(task, proposal)
        records.append(
            {
                "task": task,
                "proposal": proposal,
                "baseline_score": score,
            }
        )
    return records


def _baseline_row(model: str, proposals: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {
            "behavior_correct": record["baseline_score"].behavior_correct,
            "sequence_exact": record["baseline_score"].sequence_exact,
            "tool_selection_accuracy": record["baseline_score"].tool_selection_accuracy,
            "required_argument_recall": record["baseline_score"].required_argument_recall,
            "argument_precision": record["baseline_score"].argument_precision,
            "false_tool_call": record["baseline_score"].false_tool_call,
            "safe_no_call": record["baseline_score"].safe_no_call,
        }
        for record in proposals
    ]
    return {
        "model": model,
        "condition": "top3_model_only",
        "policy": "none",
        "n": len(rows),
        "behavior_accuracy": _mean_bool(rows, "behavior_correct"),
        "sequence_exact_accuracy": _mean_bool(rows, "sequence_exact"),
        "tool_selection_accuracy": mean(float(row["tool_selection_accuracy"]) for row in rows),
        "required_argument_recall": mean(float(row["required_argument_recall"]) for row in rows),
        "argument_precision": mean(float(row["argument_precision"]) for row in rows),
        "safe_no_call_accuracy": _safe_no_call(
            [{"baseline_safe_no_call": row["safe_no_call"]} for row in rows], "baseline"
        ),
        "false_tool_call_rate": _mean_bool(rows, "false_tool_call"),
        "threshold_abstain_rate": None,
        "guard_block_rate": None,
        "sanitization_rate": None,
        "exact_preservation_rate": None,
        "unsafe_proposal_capture_rate": None,
        "invalid_proposal_correction_rate": None,
        "exact_false_positive_count": None,
        "violation_count": None,
    }


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    task_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []
    violation_counts: Counter[str] = Counter()

    for model, experiment_id in EXPERIMENTS.items():
        proposals = _load_proposals(experiment_id)
        aggregate_rows.append(_baseline_row(model, proposals))

        for policy in POLICIES:
            policy_rows: list[dict[str, Any]] = []
            for record in proposals:
                task = cast(DomainToolCallingTask, record["task"])
                proposal = cast(ToolCallingResult, record["proposal"])
                baseline = record["baseline_score"]
                outcome = apply_tool_call_guard(
                    task,
                    proposal,
                    policy=policy,
                    retrieval_threshold=THRESHOLD,
                )
                guarded = score_tool_calling(task, outcome.result)
                codes = [violation.code for violation in outcome.violations]
                violation_counts.update(f"{policy}:{code}" for code in codes)
                row = {
                    "model": model,
                    "experiment_id": experiment_id,
                    "task_id": task.task_id,
                    "expected_behavior": task.behavior,
                    "policy": policy,
                    "action": outcome.action,
                    "retrieval_top_score": outcome.retrieval_top_score,
                    "retrieval_threshold": THRESHOLD,
                    "original_behavior": proposal.behavior,
                    "guarded_behavior": outcome.result.behavior,
                    "original_call_count": len(proposal.calls),
                    "guarded_call_count": len(outcome.result.calls),
                    "violation_codes": ";".join(codes),
                    "violation_count": len(codes),
                    "baseline_behavior_correct": baseline.behavior_correct,
                    "guarded_behavior_correct": guarded.behavior_correct,
                    "baseline_sequence_exact": baseline.sequence_exact,
                    "guarded_sequence_exact": guarded.sequence_exact,
                    "baseline_tool_selection_accuracy": baseline.tool_selection_accuracy,
                    "guarded_tool_selection_accuracy": guarded.tool_selection_accuracy,
                    "baseline_required_argument_recall": baseline.required_argument_recall,
                    "guarded_required_argument_recall": guarded.required_argument_recall,
                    "baseline_argument_precision": baseline.argument_precision,
                    "guarded_argument_precision": guarded.argument_precision,
                    "baseline_safe_no_call": baseline.safe_no_call,
                    "guarded_safe_no_call": guarded.safe_no_call,
                    "baseline_false_tool_call": baseline.false_tool_call,
                    "guarded_false_tool_call": guarded.false_tool_call,
                    "exact_preserved": baseline.sequence_exact and guarded.sequence_exact,
                    "exact_false_positive": baseline.sequence_exact and not guarded.sequence_exact,
                    "unsafe_proposal_captured": baseline.false_tool_call
                    and not guarded.false_tool_call,
                    "invalid_proposal_corrected": not baseline.sequence_exact
                    and guarded.sequence_exact,
                }
                policy_rows.append(row)
                task_rows.append(row)

            baseline_exact = [row for row in policy_rows if row["baseline_sequence_exact"]]
            baseline_unsafe = [row for row in policy_rows if row["baseline_false_tool_call"]]
            baseline_invalid = [row for row in policy_rows if not row["baseline_sequence_exact"]]
            no_call_rows = [
                row for row in policy_rows if row["expected_behavior"] in {"clarify", "abstain"}
            ]
            aggregate_rows.append(
                {
                    "model": model,
                    "condition": "top3_threshold_guard",
                    "policy": policy,
                    "n": len(policy_rows),
                    "behavior_accuracy": _mean_bool(policy_rows, "guarded_behavior_correct"),
                    "sequence_exact_accuracy": _mean_bool(policy_rows, "guarded_sequence_exact"),
                    "tool_selection_accuracy": mean(
                        float(row["guarded_tool_selection_accuracy"]) for row in policy_rows
                    ),
                    "required_argument_recall": mean(
                        float(row["guarded_required_argument_recall"]) for row in policy_rows
                    ),
                    "argument_precision": mean(
                        float(row["guarded_argument_precision"]) for row in policy_rows
                    ),
                    "safe_no_call_accuracy": mean(
                        float(bool(row["guarded_safe_no_call"])) for row in no_call_rows
                    ),
                    "false_tool_call_rate": _mean_bool(policy_rows, "guarded_false_tool_call"),
                    "threshold_abstain_rate": mean(
                        float(row["action"] == "threshold_abstain") for row in policy_rows
                    ),
                    "guard_block_rate": mean(
                        float(row["action"] == "blocked") for row in policy_rows
                    ),
                    "sanitization_rate": mean(
                        float(row["action"] == "sanitized") for row in policy_rows
                    ),
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
                    "exact_false_positive_count": sum(
                        bool(row["exact_false_positive"]) for row in policy_rows
                    ),
                    "violation_count": sum(int(row["violation_count"]) for row in policy_rows),
                }
            )

    aggregate_path = PUBLIC / "domain_tool_guard_ablation.csv"
    with aggregate_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(aggregate_rows[0]))
        writer.writeheader()
        writer.writerows(aggregate_rows)

    task_path = PUBLIC / "domain_tool_guard_tasks.csv"
    with task_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(task_rows[0]))
        writer.writeheader()
        writer.writerows(task_rows)

    violation_path = PUBLIC / "domain_tool_guard_violations.csv"
    violation_rows = [
        {"policy_and_code": code, "count": count}
        for code, count in sorted(violation_counts.items())
    ]
    with violation_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(violation_rows[0]))
        writer.writeheader()
        writer.writerows(violation_rows)

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in aggregate_rows:
        by_model[str(row["model"])].append(row)

    lines = [
        "# DomainToolBench Deterministic ToolCallGuard Ablation",
        "",
        "- Frozen proposals: three preserved top-3 retrieval experiments",
        "- Tasks per model: 15",
        f"- Exploratory no-tool threshold: {THRESHOLD:.2f}",
        "- Policies: model-only baseline, strict block, sanitize-and-preserve",
        "- No new model inference was performed; changes are deterministic post-processing effects.",
        "",
    ]
    for model, rows in by_model.items():
        ordered = sorted(
            rows, key=lambda row: {"none": 0, "strict": 1, "sanitize": 2}[str(row["policy"])]
        )
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in ordered:

            def pct(value: Any) -> str:
                return "n/a" if value is None else f"{float(value):.1%}"

            lines.append(
                f"| {row['policy']} | {pct(row['behavior_accuracy'])} | "
                f"{pct(row['sequence_exact_accuracy'])} | {pct(row['tool_selection_accuracy'])} | "
                f"{pct(row['required_argument_recall'])} | {pct(row['argument_precision'])} | "
                f"{pct(row['safe_no_call_accuracy'])} | {pct(row['false_tool_call_rate'])} | "
                f"{pct(row['exact_preservation_rate'])} | "
                f"{pct(row['unsafe_proposal_capture_rate'])} | "
                f"{pct(row['invalid_proposal_correction_rate'])} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation constraints",
            "",
            "- The 0.60 threshold was chosen after inspecting this seed's retrieval scores.",
            "- Strict and sanitize results reuse the same model proposals and are not independent model runs.",
            "- A corrected call reflects deterministic filtering, not improved model reasoning.",
            "- Exact-call preservation measures false positives only on already exact proposals.",
            "- The tool schemas are provisional normalized research interfaces.",
            "",
        ]
    )
    markdown_path = PUBLIC / "domain_tool_guard_ablation.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()

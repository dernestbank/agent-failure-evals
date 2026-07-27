"""Analyze matched before/after OpenLCA source-schema model experiments."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"
BEFORE_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
AFTER_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_b316008_v0.jsonl"
MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]
TEMPERATURE = 0.2
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


def experiment_id(surface: str, slug: str, seed: int) -> str:
    return f"openlca-schema-{surface}-{slug}-seed{seed}"


def truth(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    return {
        str(item["task_id"]): item
        for item in (
            cast(dict[str, Any], json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def schema_change_sets() -> tuple[set[str], set[str]]:
    before = load_jsonl(BEFORE_TASKS)
    after = load_jsonl(AFTER_TASKS)
    exposure_changed: set[str] = set()
    expected_tool_changed: set[str] = set()

    for task_id, before_task in before.items():
        after_task = after[task_id]
        if before_task["available_tools"] != after_task["available_tools"]:
            exposure_changed.add(task_id)

        before_tools = {
            str(item["name"]): item
            for item in cast(list[dict[str, Any]], before_task["available_tools"])
        }
        after_tools = {
            str(item["name"]): item
            for item in cast(list[dict[str, Any]], after_task["available_tools"])
        }
        changed_tools = {name for name in before_tools if before_tools[name] != after_tools[name]}
        expected_names = {
            str(call["name"])
            for call in cast(list[dict[str, Any]], before_task.get("expected_calls", []))
        }
        if changed_tools & expected_names:
            expected_tool_changed.add(task_id)

    return exposure_changed, expected_tool_changed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def signed_points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def main() -> None:
    exposure_changed, expected_tool_changed = schema_change_sets()
    run_rows: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for model, slug in MODELS.items():
        for seed in SEEDS:
            for surface in ("before", "after"):
                identifier = experiment_id(surface, slug, seed)
                directory = PROCESSED / identifier
                metrics = load_json(directory / "metrics.json")
                run_failures = cast(
                    list[dict[str, Any]], json.loads((directory / "failures.json").read_text())
                )
                run_rows.append(
                    {
                        "experiment_id": identifier,
                        "model": model,
                        "surface": surface,
                        "seed": seed,
                        "temperature": TEMPERATURE,
                        "scored_tasks": int(metrics.get("n", 0)),
                        "infrastructure_failures": len(run_failures),
                        **{metric: metrics.get(metric) for metric in METRICS},
                    }
                )
                for failure in run_failures:
                    failures.append(
                        {
                            "experiment_id": identifier,
                            "model": model,
                            "surface": surface,
                            "seed": seed,
                            **failure,
                        }
                    )
                for row in read_csv(directory / "runs.csv"):
                    task_id = row["task_id"]
                    task_rows.append(
                        {
                            "experiment_id": identifier,
                            "model": model,
                            "surface": surface,
                            "seed": seed,
                            "task_id": task_id,
                            "schema_changed": task_id in exposure_changed,
                            "expected_tool_schema_changed": task_id in expected_tool_changed,
                            "expected_behavior": row["expected_behavior"],
                            "predicted_behavior": row["predicted_behavior"],
                            "behavior_correct": truth(row["behavior_correct"]),
                            "sequence_exact": truth(row["sequence_exact"]),
                            "tool_selection_accuracy": float(row["tool_selection_accuracy"]),
                            "required_argument_recall": float(row["required_argument_recall"]),
                            "argument_precision": float(row["argument_precision"]),
                            "false_tool_call": truth(row["false_tool_call"]),
                            "safe_no_call": (
                                None if row["safe_no_call"] == "" else truth(row["safe_no_call"])
                            ),
                            "latency_seconds": float(row["latency_seconds"]),
                        }
                    )

    aggregate_rows: list[dict[str, Any]] = []
    for model in MODELS:
        for surface in ("before", "after"):
            runs = [row for row in run_rows if row["model"] == model and row["surface"] == surface]
            tasks = [
                row for row in task_rows if row["model"] == model and row["surface"] == surface
            ]
            changed_rows = [row for row in tasks if row["schema_changed"]]
            target_changed_rows = [row for row in tasks if row["expected_tool_schema_changed"]]
            unchanged_rows = [row for row in tasks if not row["schema_changed"]]
            aggregate: dict[str, Any] = {
                "model": model,
                "surface": surface,
                "seeds": len(runs),
                "task_runs": len(tasks),
                "changed_task_runs": len(changed_rows),
                "expected_tool_changed_task_runs": len(target_changed_rows),
                "unchanged_task_runs": len(unchanged_rows),
                "infrastructure_failures": sum(int(row["infrastructure_failures"]) for row in runs),
                "completion_reliability": len(tasks)
                / (len(tasks) + sum(int(row["infrastructure_failures"]) for row in runs)),
                "changed_exact_accuracy": mean(
                    float(row["sequence_exact"]) for row in changed_rows
                ),
                "expected_tool_changed_exact_accuracy": mean(
                    float(row["sequence_exact"]) for row in target_changed_rows
                ),
                "unchanged_exact_accuracy": mean(
                    float(row["sequence_exact"]) for row in unchanged_rows
                ),
            }
            for metric in METRICS:
                values = [float(row[metric]) for row in runs if row[metric] is not None]
                aggregate[f"mean_{metric}"] = mean(values)
                aggregate[f"sd_{metric}"] = stdev(values) if len(values) > 1 else 0.0
            aggregate_rows.append(aggregate)

    paired: list[dict[str, Any]] = []
    task_index = {
        (str(row["model"]), int(row["seed"]), str(row["surface"]), str(row["task_id"])): row
        for row in task_rows
    }
    for model in MODELS:
        for seed in SEEDS:
            for task_id in sorted(load_jsonl(BEFORE_TASKS)):
                before = task_index[(model, seed, "before", task_id)]
                after = task_index[(model, seed, "after", task_id)]
                before_exact = bool(before["sequence_exact"])
                after_exact = bool(after["sequence_exact"])
                transition = (
                    "improved"
                    if not before_exact and after_exact
                    else "regressed"
                    if before_exact and not after_exact
                    else "unchanged_exact"
                    if before_exact
                    else "unchanged_incorrect"
                )
                paired.append(
                    {
                        "model": model,
                        "seed": seed,
                        "task_id": task_id,
                        "schema_changed": task_id in exposure_changed,
                        "expected_tool_schema_changed": task_id in expected_tool_changed,
                        "transition": transition,
                        "before_behavior": before["predicted_behavior"],
                        "after_behavior": after["predicted_behavior"],
                        "before_exact": before_exact,
                        "after_exact": after_exact,
                        "before_tool_selection": before["tool_selection_accuracy"],
                        "after_tool_selection": after["tool_selection_accuracy"],
                        "before_argument_precision": before["argument_precision"],
                        "after_argument_precision": after["argument_precision"],
                    }
                )

    PUBLIC.mkdir(parents=True, exist_ok=True)
    write_csv(PUBLIC / "openlca_schema_hardening_model_runs.csv", run_rows)
    write_csv(PUBLIC / "openlca_schema_hardening_model_aggregate.csv", aggregate_rows)
    write_csv(PUBLIC / "openlca_schema_hardening_model_tasks.csv", paired)
    (PUBLIC / "openlca_schema_hardening_model_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )

    by_model: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in aggregate_rows:
        by_model[row["model"]][row["surface"]] = row

    lines = [
        "# OpenLCA-MCP Source Schema Hardening Model Ablation",
        "",
        "- Source commits: `4865b2b` before and `b316008` after",
        "- Identical task semantics: 20 intents per surface",
        "- Models: three local Ollama models",
        "- Seeds: 101, 202, 303",
        "- Temperature: 0.2",
        f"- Tasks with any changed attached schema: {len(exposure_changed)}",
        f"- Tasks whose expected-call tool schema changed: {len(expected_tool_changed)}",
        "- Live OpenLCA execution: not performed",
        "",
        "> **Interpret with the same-schema replay control.** This first-pass table preserves the raw before/after matrix. The authoritative replay-adjusted interpretation is in `openlca_schema_replay_control.md`.",
        "",
    ]
    for model, surfaces in by_model.items():
        before = surfaces["before"]
        after = surfaces["after"]
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Surface | Completion | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Any-changed exact | Expected-tool-changed exact | Unchanged exact | Latency |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for label, row in (("before", before), ("after", after)):
            lines.append(
                "| {label} | {completion} | {behavior} | {exact} | {selection} | {recall} | {precision} | {safe} | {false_calls} | {changed} | {target_changed} | {unchanged} | {latency:.2f}s |".format(
                    label=label,
                    completion=percent(row["completion_reliability"]),
                    behavior=percent(row["mean_behavior_accuracy"]),
                    exact=percent(row["mean_sequence_exact_accuracy"]),
                    selection=percent(row["mean_tool_selection_accuracy"]),
                    recall=percent(row["mean_required_argument_recall"]),
                    precision=percent(row["mean_argument_precision"]),
                    safe=percent(row["mean_safe_no_call_accuracy"]),
                    false_calls=percent(row["mean_false_tool_call_rate"]),
                    changed=percent(row["changed_exact_accuracy"]),
                    target_changed=percent(row["expected_tool_changed_exact_accuracy"]),
                    unchanged=percent(row["unchanged_exact_accuracy"]),
                    latency=float(row["mean_mean_latency_seconds"]),
                )
            )
        model_pairs = [row for row in paired if row["model"] == model]
        improved = sum(row["transition"] == "improved" for row in model_pairs)
        regressed = sum(row["transition"] == "regressed" for row in model_pairs)
        changed_improved = sum(
            row["schema_changed"] and row["transition"] == "improved" for row in model_pairs
        )
        changed_regressed = sum(
            row["schema_changed"] and row["transition"] == "regressed" for row in model_pairs
        )
        target_improved = sum(
            row["expected_tool_schema_changed"] and row["transition"] == "improved"
            for row in model_pairs
        )
        target_regressed = sum(
            row["expected_tool_schema_changed"] and row["transition"] == "regressed"
            for row in model_pairs
        )
        lines.extend(
            [
                "",
                f"- Overall exact-call delta: {signed_points(float(after['mean_sequence_exact_accuracy']) - float(before['mean_sequence_exact_accuracy']))}",
                f"- Any-changed-schema exact delta: {signed_points(float(after['changed_exact_accuracy']) - float(before['changed_exact_accuracy']))}",
                f"- Expected-tool-changed exact delta: {signed_points(float(after['expected_tool_changed_exact_accuracy']) - float(before['expected_tool_changed_exact_accuracy']))}",
                f"- Paired task-seed improvements/regressions: {improved}/{regressed}",
                f"- Any-changed-schema improvements/regressions: {changed_improved}/{changed_regressed}",
                f"- Expected-tool-changed improvements/regressions: {target_improved}/{target_regressed}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation constraints",
            "",
            "- The comparison isolates generated source-schema changes; prompts, expected calls, models, seeds, and sampling settings are paired.",
            "- Results do not describe the deployed connector because its exact descriptions and version remain unknown.",
            "- No call was executed in openLCA, so exact-call scoring is contract-level rather than functional validation.",
            "- Three seeds and twenty tasks do not establish statistical significance or general model capability.",
            "- A schema change can alter outputs on tasks where the changed tool appears only as a distractor.",
            "- Identical prompts and seeds were not perfectly replay-deterministic in the tested Ollama/GPU runtime; use the replay-control report before attributing gains.",
        ]
    )
    (PUBLIC / "openlca_schema_hardening_model_ablation.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(PUBLIC / "openlca_schema_hardening_model_ablation.md")


if __name__ == "__main__":
    main()

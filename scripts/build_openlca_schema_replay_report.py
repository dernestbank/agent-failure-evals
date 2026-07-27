"""Compare the OpenLCA schema hardening ablation with a same-schema replay control."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from statistics import mean
from typing import Any, cast

from agent_failure_evals.replay_control import exact_transition, summarize_transitions
from agent_failure_evals.tool_calling import load_tool_calling_tasks

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
PUBLIC = ROOT / "results" / "public"
BEFORE_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
AFTER_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_b316008_v0.jsonl"

MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]


def read_payload(experiment_id: str, task_id: str) -> dict[str, Any]:
    path = RAW / experiment_id / f"{task_id}.json"
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def normalized(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def schema_groups() -> tuple[set[str], set[str]]:
    before = {task.task_id: task for task in load_tool_calling_tasks(BEFORE_TASKS)}
    after = {task.task_id: task for task in load_tool_calling_tasks(AFTER_TASKS)}
    exposure_changed: set[str] = set()
    expected_tool_changed: set[str] = set()

    for task_id, before_task in before.items():
        after_task = after[task_id]
        if before_task.available_tools != after_task.available_tools:
            exposure_changed.add(task_id)
        before_tools = {str(item["name"]): item for item in before_task.available_tools}
        after_tools = {str(item["name"]): item for item in after_task.available_tools}
        changed_tools = {name for name in before_tools if before_tools[name] != after_tools[name]}
        expected_names = {call.name for call in before_task.expected_calls}
        if changed_tools & expected_names:
            expected_tool_changed.add(task_id)

    return exposure_changed, expected_tool_changed


def accuracy(rows: list[dict[str, Any]], field: str) -> float:
    return mean(float(bool(row[field])) for row in rows)


def main() -> None:
    exposure_changed, expected_tool_changed = schema_groups()
    tasks = load_tool_calling_tasks(BEFORE_TASKS)
    task_ids = [task.task_id for task in tasks]
    task_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for model, slug in MODELS.items():
        for seed in SEEDS:
            experiment_ids = {
                "before": f"openlca-schema-before-{slug}-seed{seed}",
                "after": f"openlca-schema-after-{slug}-seed{seed}",
                "replay": f"openlca-schema-replay-before-{slug}-seed{seed}",
            }
            for task_id in task_ids:
                payloads = {
                    surface: read_payload(experiment_id, task_id)
                    for surface, experiment_id in experiment_ids.items()
                }
                if any(payload.get("error") for payload in payloads.values()):
                    failures.append(
                        {
                            "model": model,
                            "seed": seed,
                            "task_id": task_id,
                            "errors": {
                                surface: payload.get("error")
                                for surface, payload in payloads.items()
                                if payload.get("error")
                            },
                        }
                    )
                    continue

                results = {
                    surface: cast(dict[str, Any], payload["result"])
                    for surface, payload in payloads.items()
                }
                scores = {
                    surface: cast(dict[str, Any], payload["score"])
                    for surface, payload in payloads.items()
                }
                exact = {
                    surface: bool(score["sequence_exact"]) for surface, score in scores.items()
                }
                before_result = results["before"]
                after_result = results["after"]
                replay_result = results["replay"]
                task_rows.append(
                    {
                        "model": model,
                        "seed": seed,
                        "task_id": task_id,
                        "schema_exposure_changed": task_id in exposure_changed,
                        "expected_tool_schema_changed": task_id in expected_tool_changed,
                        "schema_group": (
                            "expected_tool_changed"
                            if task_id in expected_tool_changed
                            else "distractor_only_changed"
                            if task_id in exposure_changed
                            else "schema_identical"
                        ),
                        "before_exact": exact["before"],
                        "after_exact": exact["after"],
                        "replay_exact": exact["replay"],
                        "schema_transition": exact_transition(exact["before"], exact["after"]),
                        "replay_transition": exact_transition(exact["before"], exact["replay"]),
                        "before_after_result_identity": normalized(before_result)
                        == normalized(after_result),
                        "before_replay_result_identity": normalized(before_result)
                        == normalized(replay_result),
                        "before_replay_behavior_identity": before_result["behavior"]
                        == replay_result["behavior"],
                        "before_replay_calls_identity": normalized(before_result.get("calls", []))
                        == normalized(replay_result.get("calls", [])),
                        "before_behavior": before_result["behavior"],
                        "after_behavior": after_result["behavior"],
                        "replay_behavior": replay_result["behavior"],
                    }
                )

    PUBLIC.mkdir(parents=True, exist_ok=True)
    write_csv(PUBLIC / "openlca_schema_replay_control_tasks.csv", task_rows)
    (PUBLIC / "openlca_schema_replay_control_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n", encoding="utf-8"
    )

    aggregate_rows: list[dict[str, Any]] = []
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_rows:
        by_model[str(row["model"])].append(row)

    groups: dict[str, Callable[[dict[str, Any]], bool]] = {
        "all": lambda row: True,
        "expected_tool_changed": lambda row: bool(row["expected_tool_schema_changed"]),
        "distractor_only_changed": lambda row: row["schema_group"] == "distractor_only_changed",
        "schema_identical": lambda row: row["schema_group"] == "schema_identical",
    }

    for model, model_rows in by_model.items():
        for group_name, predicate in groups.items():
            group_rows = [row for row in model_rows if predicate(row)]
            if not group_rows:
                continue
            before_accuracy = accuracy(group_rows, "before_exact")
            after_accuracy = accuracy(group_rows, "after_exact")
            replay_accuracy = accuracy(group_rows, "replay_exact")
            aggregate = {
                "model": model,
                "group": group_name,
                "task_seed_pairs": len(group_rows),
                "before_exact_accuracy": before_accuracy,
                "after_exact_accuracy": after_accuracy,
                "replay_exact_accuracy": replay_accuracy,
                "schema_delta": after_accuracy - before_accuracy,
                "replay_delta": replay_accuracy - before_accuracy,
                "replay_adjusted_delta": (after_accuracy - before_accuracy)
                - (replay_accuracy - before_accuracy),
                "before_replay_exact_status_agreement": accuracy(
                    [
                        {"agreement": row["before_exact"] == row["replay_exact"]}
                        for row in group_rows
                    ],
                    "agreement",
                ),
                "before_replay_full_result_identity": accuracy(
                    group_rows, "before_replay_result_identity"
                ),
                "before_replay_behavior_identity": accuracy(
                    group_rows, "before_replay_behavior_identity"
                ),
                "before_replay_calls_identity": accuracy(
                    group_rows, "before_replay_calls_identity"
                ),
            }
            aggregate.update(summarize_transitions(group_rows, "schema"))
            aggregate.update(summarize_transitions(group_rows, "replay"))
            aggregate_rows.append(aggregate)

    write_csv(PUBLIC / "openlca_schema_replay_control_aggregate.csv", aggregate_rows)

    lines = [
        "# OpenLCA-MCP Schema Hardening Replay Control",
        "",
        "- Original surfaces: source commits `4865b2b` and `b316008`",
        "- Replay surface: a second run of the unchanged `4865b2b` benchmark",
        "- Models: three local Ollama models",
        "- Seeds: 101, 202, 303",
        "- Temperature: 0.2",
        "- Tasks: 20 per model-seed condition",
        "- Replay task runs: 180",
        f"- Infrastructure failures across compared triples: {len(failures)}",
        "",
        "The replay control estimates output variation when the prompt and schema are identical. It is used to avoid attributing all before/after changes to schema hardening.",
        "",
    ]

    for model in MODELS:
        model_aggregates = {
            str(row["group"]): row for row in aggregate_rows if row["model"] == model
        }
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Group | Before exact | After exact | Replay exact | Schema delta | Replay delta | Replay-adjusted delta | Replay exact-status agreement | Full-result identity |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for group_name in groups:
            row = model_aggregates[group_name]
            lines.append(
                "| {group} | {before} | {after} | {replay} | {schema_delta} | {replay_delta} | {adjusted} | {agreement} | {identity} |".format(
                    group=group_name,
                    before=percent(float(row["before_exact_accuracy"])),
                    after=percent(float(row["after_exact_accuracy"])),
                    replay=percent(float(row["replay_exact_accuracy"])),
                    schema_delta=points(float(row["schema_delta"])),
                    replay_delta=points(float(row["replay_delta"])),
                    adjusted=points(float(row["replay_adjusted_delta"])),
                    agreement=percent(float(row["before_replay_exact_status_agreement"])),
                    identity=percent(float(row["before_replay_full_result_identity"])),
                )
            )
        all_row = model_aggregates["all"]
        changed_row = model_aggregates["expected_tool_changed"]
        lines.extend(
            [
                "",
                f"- All-task schema improvements/regressions: {all_row['schema_improvements']}/{all_row['schema_regressions']}",
                f"- All-task replay improvements/regressions: {all_row['replay_improvements']}/{all_row['replay_regressions']}",
                f"- Expected-tool-changed schema improvements/regressions: {changed_row['schema_improvements']}/{changed_row['schema_regressions']}",
                f"- Expected-tool-changed replay improvements/regressions: {changed_row['replay_improvements']}/{changed_row['replay_regressions']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation rules",
            "",
            "- Full-result identity is stricter than exact-call status agreement.",
            "- A positive replay-adjusted delta is suggestive only; the same tasks are repeated across seeds and are not statistically independent.",
            "- Improvements on schema-identical prompts demonstrate runtime or inference variability and must not be credited to schema hardening.",
            "- No tool call was executed in openLCA; results remain contract-level.",
            "- The deployed connector was not evaluated.",
            "",
        ]
    )
    output = PUBLIC / "openlca_schema_replay_control.md"
    output.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(output)


if __name__ == "__main__":
    main()

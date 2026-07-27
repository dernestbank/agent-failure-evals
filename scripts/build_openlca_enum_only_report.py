"""Analyze the counterbalanced enum-only OpenLCA schema ablation."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from statistics import mean
from typing import Any, cast

from agent_failure_evals.replay_control import exact_transition, summarize_transitions
from agent_failure_evals.tool_calling import load_tool_calling_tasks

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
PUBLIC = ROOT / "results" / "public"
PLAN_PATH = ROOT / "results" / "processed" / "openlca_enum_only_matrix_plan.json"
CONTROL_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
ENUM_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_4865b2b_enum_only_v0.jsonl"

MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303, 404]


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
    control = {task.task_id: task for task in load_tool_calling_tasks(CONTROL_TASKS)}
    variant = {task.task_id: task for task in load_tool_calling_tasks(ENUM_TASKS)}
    exposure_changed: set[str] = set()
    expected_changed: set[str] = set()

    for task_id, control_task in control.items():
        variant_task = variant[task_id]
        if control_task.available_tools != variant_task.available_tools:
            exposure_changed.add(task_id)
        control_tools = {str(item["name"]): item for item in control_task.available_tools}
        variant_tools = {str(item["name"]): item for item in variant_task.available_tools}
        changed_tools = {
            name for name in control_tools if control_tools[name] != variant_tools[name]
        }
        expected_names = {call.name for call in control_task.expected_calls}
        if changed_tools & expected_names:
            expected_changed.add(task_id)

    return exposure_changed, expected_changed


def accuracy(rows: list[dict[str, Any]], field: str) -> float:
    return mean(float(bool(row[field])) for row in rows)


def main() -> None:
    plan = cast(
        list[dict[str, Any]],
        json.loads(PLAN_PATH.read_text(encoding="utf-8")),
    )
    plan_map = {(str(row["model"]), int(row["seed"]), str(row["condition"])): row for row in plan}
    exposure_changed, expected_changed = schema_groups()
    task_ids = [task.task_id for task in load_tool_calling_tasks(CONTROL_TASKS)]
    task_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for model, slug in MODELS.items():
        for seed in SEEDS:
            identifiers = {
                condition: f"openlca-enum-{condition}-{slug}-seed{seed}"
                for condition in ("control", "enum_only")
            }
            order_label = str(plan_map[(model, seed, "control")]["order_label"])
            for task_id in task_ids:
                payloads = {
                    condition: read_payload(identifier, task_id)
                    for condition, identifier in identifiers.items()
                }
                if any(payload.get("error") for payload in payloads.values()):
                    failures.append(
                        {
                            "model": model,
                            "seed": seed,
                            "task_id": task_id,
                            "errors": {
                                condition: payload.get("error")
                                for condition, payload in payloads.items()
                                if payload.get("error")
                            },
                        }
                    )
                    continue

                results = {
                    condition: cast(dict[str, Any], payload["result"])
                    for condition, payload in payloads.items()
                }
                scores = {
                    condition: cast(dict[str, Any], payload["score"])
                    for condition, payload in payloads.items()
                }
                exact = {
                    condition: bool(score["sequence_exact"]) for condition, score in scores.items()
                }
                control_result = results["control"]
                enum_result = results["enum_only"]
                task_rows.append(
                    {
                        "model": model,
                        "seed": seed,
                        "order_label": order_label,
                        "task_id": task_id,
                        "schema_exposure_changed": task_id in exposure_changed,
                        "expected_tool_schema_changed": task_id in expected_changed,
                        "schema_group": (
                            "expected_tool_changed"
                            if task_id in expected_changed
                            else "distractor_only_changed"
                            if task_id in exposure_changed
                            else "schema_identical"
                        ),
                        "control_exact": exact["control"],
                        "enum_exact": exact["enum_only"],
                        "transition": exact_transition(exact["control"], exact["enum_only"]),
                        "result_identity": normalized(control_result) == normalized(enum_result),
                        "behavior_identity": control_result["behavior"] == enum_result["behavior"],
                        "calls_identity": normalized(control_result.get("calls", []))
                        == normalized(enum_result.get("calls", [])),
                        "control_behavior": control_result["behavior"],
                        "enum_behavior": enum_result["behavior"],
                        "control_tool_selection": float(
                            scores["control"]["tool_selection_accuracy"]
                        ),
                        "enum_tool_selection": float(
                            scores["enum_only"]["tool_selection_accuracy"]
                        ),
                        "control_argument_recall": float(
                            scores["control"]["required_argument_recall"]
                        ),
                        "enum_argument_recall": float(
                            scores["enum_only"]["required_argument_recall"]
                        ),
                        "control_argument_precision": float(
                            scores["control"]["argument_precision"]
                        ),
                        "enum_argument_precision": float(scores["enum_only"]["argument_precision"]),
                        "control_false_tool_call": bool(scores["control"]["false_tool_call"]),
                        "enum_false_tool_call": bool(scores["enum_only"]["false_tool_call"]),
                    }
                )

    PUBLIC.mkdir(parents=True, exist_ok=True)
    write_csv(PUBLIC / "openlca_enum_only_tasks.csv", task_rows)
    (PUBLIC / "openlca_enum_only_failures.json").write_text(
        json.dumps(failures, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    groups: dict[str, Callable[[dict[str, Any]], bool]] = {
        "all": lambda row: True,
        "expected_tool_changed": lambda row: bool(row["expected_tool_schema_changed"]),
        "distractor_only_changed": lambda row: row["schema_group"] == "distractor_only_changed",
        "schema_identical": lambda row: row["schema_group"] == "schema_identical",
    }
    aggregate_rows: list[dict[str, Any]] = []
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in task_rows:
        by_model[str(row["model"])].append(row)

    for model, model_rows in by_model.items():
        for group_name, predicate in groups.items():
            rows = [row for row in model_rows if predicate(row)]
            if not rows:
                continue
            aggregate = {
                "model": model,
                "group": group_name,
                "task_seed_pairs": len(rows),
                "control_exact_accuracy": accuracy(rows, "control_exact"),
                "enum_exact_accuracy": accuracy(rows, "enum_exact"),
                "exact_delta": accuracy(rows, "enum_exact") - accuracy(rows, "control_exact"),
                "result_identity": accuracy(rows, "result_identity"),
                "behavior_identity": accuracy(rows, "behavior_identity"),
                "calls_identity": accuracy(rows, "calls_identity"),
                "control_tool_selection": mean(
                    float(row["control_tool_selection"]) for row in rows
                ),
                "enum_tool_selection": mean(float(row["enum_tool_selection"]) for row in rows),
                "control_argument_recall": mean(
                    float(row["control_argument_recall"]) for row in rows
                ),
                "enum_argument_recall": mean(float(row["enum_argument_recall"]) for row in rows),
                "control_argument_precision": mean(
                    float(row["control_argument_precision"]) for row in rows
                ),
                "enum_argument_precision": mean(
                    float(row["enum_argument_precision"]) for row in rows
                ),
                "control_false_tool_call_rate": accuracy(rows, "control_false_tool_call"),
                "enum_false_tool_call_rate": accuracy(rows, "enum_false_tool_call"),
            }
            aggregate.update(summarize_transitions(rows, "enum"))
            aggregate_rows.append(aggregate)

    write_csv(PUBLIC / "openlca_enum_only_aggregate.csv", aggregate_rows)

    order_rows: list[dict[str, Any]] = []
    for model, model_rows in by_model.items():
        for order_label in ("control_first", "enum_first"):
            rows = [row for row in model_rows if row["order_label"] == order_label]
            order_rows.append(
                {
                    "model": model,
                    "order_label": order_label,
                    "task_seed_pairs": len(rows),
                    "control_exact_accuracy": accuracy(rows, "control_exact"),
                    "enum_exact_accuracy": accuracy(rows, "enum_exact"),
                    "exact_delta": accuracy(rows, "enum_exact") - accuracy(rows, "control_exact"),
                    **summarize_transitions(rows, "enum"),
                }
            )
    write_csv(PUBLIC / "openlca_enum_only_order_effects.csv", order_rows)

    lines = [
        "# OpenLCA-MCP Enum-Only Schema Ablation",
        "",
        "- Base schema: FastMCP source commit `4865b2b`",
        "- Intervention: enums added to exactly four tool properties",
        "- Models: three local Ollama models",
        "- Seeds: 101, 202, 303, 404",
        "- Temperature: 0.2",
        "- Conditions: unchanged control and synthetic enum-only variant",
        "- Condition order: counterbalanced across seeds",
        "- Planned task runs: 480",
        f"- Infrastructure failures: {len(failures)}",
        "- Live openLCA execution: not performed",
        "",
    ]

    aggregate_map = {(str(row["model"]), str(row["group"])): row for row in aggregate_rows}
    order_map = {(str(row["model"]), str(row["order_label"])): row for row in order_rows}
    for model in MODELS:
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Group | Control exact | Enum exact | Delta | Result identity | Improvements | Regressions |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for group_name in groups:
            row = aggregate_map[(model, group_name)]
            lines.append(
                "| {group} | {control} | {enum} | {delta} | {identity} | {improved} | {regressed} |".format(
                    group=group_name,
                    control=percent(float(row["control_exact_accuracy"])),
                    enum=percent(float(row["enum_exact_accuracy"])),
                    delta=points(float(row["exact_delta"])),
                    identity=percent(float(row["result_identity"])),
                    improved=row["enum_improvements"],
                    regressed=row["enum_regressions"],
                )
            )
        lines.extend(
            [
                "",
                "Order check:",
                "",
                "| Order | Control exact | Enum exact | Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for order_label in ("control_first", "enum_first"):
            row = order_map[(model, order_label)]
            lines.append(
                "| {order} | {control} | {enum} | {delta} |".format(
                    order=order_label,
                    control=percent(float(row["control_exact_accuracy"])),
                    enum=percent(float(row["enum_exact_accuracy"])),
                    delta=points(float(row["exact_delta"])),
                )
            )
        lines.append("")

    mechanism_tasks = {
        "qwen3:8b": ["olca-exact-entity-001", "olca-search-flows-001"],
        "gemma3:4b": ["olca-inventory-output-001"],
        "qwen2.5-coder:1.5b": [
            "olca-exact-entity-001",
            "olca-search-flows-001",
            "olca-inventory-output-001",
        ],
    }
    lines.extend(["## Direct-task transition counts", ""])
    for model, task_names in mechanism_tasks.items():
        rows = [row for row in task_rows if row["model"] == model and row["task_id"] in task_names]
        transitions = Counter(str(row["transition"]) for row in rows)
        lines.append(
            f"- `{model}`: {transitions['improved']} improved, "
            f"{transitions['regressed']} regressed, "
            f"{transitions['stable_exact']} stable exact, "
            f"{transitions['stable_incorrect']} stable incorrect."
        )

    lines.extend(
        [
            "",
            "## Interpretation constraints",
            "",
            "- The enum-only manifest is synthetic and derived from source commit `4865b2b`; it is not a deployed server version.",
            "- Counterbalancing reduces but does not eliminate temporal or runtime variation.",
            "- Repeated seeds on the same twenty intents are not independent samples.",
            "- Exact-call scoring is proposal-level; no tool call was executed in openLCA.",
            "- The intervention tests four enums together; follow-up per-enum ablations are still needed.",
            "",
        ]
    )
    output = PUBLIC / "openlca_enum_only_ablation.md"
    output.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(output)


if __name__ == "__main__":
    main()

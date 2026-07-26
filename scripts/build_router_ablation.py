"""Build single-stage, zero-shot-router, and few-shot-router comparisons."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
PUBLIC = ROOT / "results" / "public"

EXPERIMENTS: dict[str, dict[str, str]] = {
    "qwen2.5-coder:1.5b": {
        "single_stage": "domain-v0.1-qwen25-coder-1.5b",
        "router_zero_shot": "domain-router-v0-qwen25-coder-1.5b",
        "router_few_shot": "domain-router-fewshot-v0-qwen25-coder-1.5b",
    },
    "gemma3:4b": {
        "single_stage": "domain-v0.1-gemma3-4b",
        "router_zero_shot": "domain-router-v0-gemma3-4b",
        "router_few_shot": "domain-router-fewshot-v0-gemma3-4b",
    },
    "qwen3:8b": {
        "single_stage": "domain-v0.1-qwen3-8b",
        "router_zero_shot": "domain-router-v0-qwen3-8b",
        "router_few_shot": "domain-router-fewshot-v0-qwen3-8b",
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
    "mean_output_tokens",
]


def load_metrics(experiment_id: str) -> dict[str, Any]:
    path = PROCESSED / experiment_id / "metrics.json"
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.1%}"


def signed_points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    by_model: dict[str, dict[str, dict[str, Any]]] = {}

    for model, experiment_conditions in EXPERIMENTS.items():
        by_model[model] = {}
        for condition_name, experiment_id in experiment_conditions.items():
            metrics = load_metrics(experiment_id)
            row: dict[str, Any] = {
                "model": model,
                "condition": condition_name,
                "experiment_id": experiment_id,
                **{metric: metrics.get(metric) for metric in METRICS},
            }
            rows.append(row)
            by_model[model][condition_name] = row

    csv_path = PUBLIC / "domain_router_ablation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# DomainToolBench Behavior-Router Ablation",
        "",
        "Conditions:",
        "",
        "- `single_stage`: one model response chooses behavior and calls together.",
        "- `router_zero_shot`: stage one chooses behavior; stage two generates calls only when authorized.",
        "- `router_few_shot`: the same two-stage router with one non-benchmark example for each behavior class.",
        "",
    ]

    for model, model_conditions in by_model.items():
        lines.extend(
            [
                f"## `{model}`",
                "",
                "| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for condition_name in ("single_stage", "router_zero_shot", "router_few_shot"):
            row = model_conditions[condition_name]
            lines.append(
                "| {condition} | {behavior} | {exact} | {selection} | {recall} | {precision} | {safe} | {false_calls} | {latency:.2f}s |".format(
                    condition=condition_name,
                    behavior=percent(row["behavior_accuracy"]),
                    exact=percent(row["sequence_exact_accuracy"]),
                    selection=percent(row["tool_selection_accuracy"]),
                    recall=percent(row["required_argument_recall"]),
                    precision=percent(row["argument_precision"]),
                    safe=percent(row["safe_no_call_accuracy"]),
                    false_calls=percent(row["false_tool_call_rate"]),
                    latency=float(row["mean_latency_seconds"]),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Few-shot minus zero-shot router deltas",
            "",
            "| Model | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for model, model_conditions in by_model.items():
        zero = model_conditions["router_zero_shot"]
        few = model_conditions["router_few_shot"]
        lines.append(
            "| `{model}` | {behavior} | {exact} | {selection} | {recall} | {precision} | {safe} | {false_calls} | {latency:+.2f}s |".format(
                model=model,
                behavior=signed_points(
                    float(few["behavior_accuracy"]) - float(zero["behavior_accuracy"])
                ),
                exact=signed_points(
                    float(few["sequence_exact_accuracy"]) - float(zero["sequence_exact_accuracy"])
                ),
                selection=signed_points(
                    float(few["tool_selection_accuracy"]) - float(zero["tool_selection_accuracy"])
                ),
                recall=signed_points(
                    float(few["required_argument_recall"]) - float(zero["required_argument_recall"])
                ),
                precision=signed_points(
                    float(few["argument_precision"]) - float(zero["argument_precision"])
                ),
                safe=signed_points(
                    float(few["safe_no_call_accuracy"]) - float(zero["safe_no_call_accuracy"])
                ),
                false_calls=signed_points(
                    float(few["false_tool_call_rate"]) - float(zero["false_tool_call_rate"])
                ),
                latency=float(few["mean_latency_seconds"]) - float(zero["mean_latency_seconds"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Qwen Coder 1.5B: balanced examples broke the all-`clarify` router collapse and improved routing and argument recall, but reintroduced unsafe calls and sharply reduced safe no-call behavior.",
            "- Gemma 3 4B: few-shot examples improved safe no-call behavior and reduced false calls, while slightly reducing exact-call and tool-selection accuracy.",
            "- Qwen 3 8B: few-shot examples recovered most of the zero-shot router's accuracy loss, but the simpler single-stage condition remained more accurate, safer, and faster.",
            "- Two-stage decomposition and demonstrations are model-dependent interventions; neither should be assumed to improve safety monotonically.",
            "",
            "These are single-run results on a 15-task provisional seed. They are not estimates of general model capability.",
        ]
    )

    markdown_path = PUBLIC / "domain_router_ablation.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(markdown_path)


if __name__ == "__main__":
    main()

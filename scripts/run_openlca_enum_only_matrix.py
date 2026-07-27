"""Run a counterbalanced paired enum-only OpenLCA schema ablation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.replay_control import (
    acquire_file_lock,
    counterbalanced_pair_order,
    release_file_lock,
)
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import run_tool_calling_model

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
CONTROL = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
ENUM_ONLY = ROOT / "tasks" / "domain_tool_calling_openlca_source_4865b2b_enum_only_v0.jsonl"
LOCK_PATH = ROOT / "results" / "processed" / "openlca_enum_only_matrix.lock"
PLAN_PATH = ROOT / "results" / "processed" / "openlca_enum_only_matrix_plan.json"

MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303, 404]
CONTROL_FIRST_SEEDS = frozenset({101, 303})
TEMPERATURE = 0.2


def order_for_seed(seed: int) -> list[tuple[str, Path]]:
    """Counterbalance condition order across four seeds."""

    order = counterbalanced_pair_order(
        seed,
        CONTROL_FIRST_SEEDS,
        control="control",
        intervention="enum_only",
    )
    paths = {"control": CONTROL, "enum_only": ENUM_ONLY}
    return [(condition, paths[condition]) for condition in order]


def experiment_id(condition: str, slug: str, seed: int) -> str:
    return f"openlca-enum-{condition}-{slug}-seed{seed}"


def unload(model: str) -> None:
    subprocess.run(
        ["ollama", "stop", model],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    descriptor = acquire_file_lock(LOCK_PATH)
    try:
        plan: list[dict[str, object]] = []
        for model, slug in MODELS.items():
            for seed in SEEDS:
                client = OllamaClient(model, temperature=TEMPERATURE, seed=seed)
                order = order_for_seed(seed)
                for position, (condition, benchmark) in enumerate(order, start=1):
                    identifier = experiment_id(condition, slug, seed)
                    output = run_tool_calling_model(
                        client=client,
                        benchmark_path=benchmark,
                        output_root=RAW,
                        experiment_id=identifier,
                        condition=f"openlca_enum_only_{condition}",
                    )
                    analyze_tool_calling_run(output)
                    plan.append(
                        {
                            "experiment_id": identifier,
                            "model": model,
                            "seed": seed,
                            "condition": condition,
                            "condition_order": position,
                            "order_label": "control_first"
                            if order[0][0] == "control"
                            else "enum_first",
                            "temperature": TEMPERATURE,
                            "task_count": 20,
                        }
                    )
                    print(f"completed {identifier}", flush=True)
            unload(model)

        PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
        PLAN_PATH.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(PLAN_PATH, flush=True)
    finally:
        release_file_lock(LOCK_PATH, descriptor)


if __name__ == "__main__":
    main()

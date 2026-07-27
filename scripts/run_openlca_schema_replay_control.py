"""Run a same-schema replay control for the OpenLCA hardening ablation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.replay_control import acquire_file_lock, release_file_lock
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import run_tool_calling_model

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
BENCHMARK = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
LOCK_PATH = ROOT / "results" / "processed" / "openlca_schema_replay_control.lock"
PLAN_PATH = ROOT / "results" / "processed" / "openlca_schema_replay_control_plan.json"

MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]
TEMPERATURE = 0.2


def experiment_id(slug: str, seed: int) -> str:
    return f"openlca-schema-replay-before-{slug}-seed{seed}"


def unload(model: str) -> None:
    subprocess.run(
        ["ollama", "stop", model],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    lock_descriptor = acquire_file_lock(LOCK_PATH)
    try:
        plan: list[dict[str, object]] = []
        for model, slug in MODELS.items():
            for seed in SEEDS:
                identifier = experiment_id(slug, seed)
                client = OllamaClient(model, temperature=TEMPERATURE, seed=seed)
                output = run_tool_calling_model(
                    client=client,
                    benchmark_path=BENCHMARK,
                    output_root=RAW,
                    experiment_id=identifier,
                    condition="openlca_source_schema_before_replay_control",
                )
                analyze_tool_calling_run(output)
                plan.append(
                    {
                        "experiment_id": identifier,
                        "model": model,
                        "seed": seed,
                        "surface": "before_replay",
                        "temperature": TEMPERATURE,
                        "task_count": 20,
                    }
                )
                print(f"completed {identifier}", flush=True)
            unload(model)

        PLAN_PATH.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(PLAN_PATH, flush=True)
    finally:
        release_file_lock(LOCK_PATH, lock_descriptor)


if __name__ == "__main__":
    main()

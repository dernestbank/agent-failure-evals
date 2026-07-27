"""Run matched before/after OpenLCA source-schema experiments through Ollama."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import run_tool_calling_model

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
BEFORE = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
AFTER = ROOT / "tasks" / "domain_tool_calling_openlca_source_b316008_v0.jsonl"
MODELS = {
    "qwen2.5-coder:1.5b": "qwen2p5-coder-1p5b",
    "gemma3:4b": "gemma3-4b",
    "qwen3:8b": "qwen3-8b",
}
SEEDS = [101, 202, 303]
TEMPERATURE = 0.2
LOCK_PATH = ROOT / "results" / "processed" / "openlca_schema_hardening_matrix.lock"


def acquire_lock() -> int:
    """Prevent concurrent writers from sharing experiment directories."""

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(
            f"Matrix lock already exists: {LOCK_PATH}. "
            "Confirm no runner is active before removing it."
        ) from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode())
    return descriptor


def release_lock(descriptor: int) -> None:
    os.close(descriptor)
    LOCK_PATH.unlink(missing_ok=True)


def unload(model: str) -> None:
    subprocess.run(
        ["ollama", "stop", model],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def experiment_id(surface: str, slug: str, seed: int) -> str:
    return f"openlca-schema-{surface}-{slug}-seed{seed}"


def main() -> None:
    lock_descriptor = acquire_lock()
    try:
        plan: list[dict[str, object]] = []
        for model, slug in MODELS.items():
            for seed in SEEDS:
                client = OllamaClient(model, temperature=TEMPERATURE, seed=seed)
                for surface, benchmark in (("before", BEFORE), ("after", AFTER)):
                    identifier = experiment_id(surface, slug, seed)
                    output = run_tool_calling_model(
                        client=client,
                        benchmark_path=benchmark,
                        output_root=RAW,
                        experiment_id=identifier,
                        condition=f"openlca_source_schema_{surface}_stability",
                    )
                    analyze_tool_calling_run(output)
                    plan.append(
                        {
                            "experiment_id": identifier,
                            "model": model,
                            "seed": seed,
                            "surface": surface,
                            "temperature": TEMPERATURE,
                            "task_count": 20,
                        }
                    )
                    print(f"completed {identifier}", flush=True)
                unload(model)

        plan_path = ROOT / "results" / "processed" / "openlca_schema_hardening_matrix_plan.json"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(plan_path, flush=True)
    finally:
        release_lock(lock_descriptor)


if __name__ == "__main__":
    main()

"""Run fresh top-3 proposals and paired deterministic guard policies across seeds."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.tool_calling_guard_experiment import run_guarded_tool_calling_model

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tasks" / "domain_tool_calling_top3_mxbai_v0.jsonl"
RAW = ROOT / "results" / "raw"

MODELS = ["qwen2.5-coder:1.5b", "gemma3:4b", "qwen3:8b"]
SEEDS = [101, 202, 303]
TEMPERATURE = 0.2
THRESHOLD = 0.60


def slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "-").replace(".", "p")


def main() -> None:
    for model in MODELS:
        for seed in SEEDS:
            client = OllamaClient(model, temperature=TEMPERATURE, seed=seed)
            identifier = f"toolguard-stability-{slug(model)}-seed{seed}"
            output = run_guarded_tool_calling_model(
                client=client,
                benchmark_path=BENCHMARK,
                output_root=RAW,
                experiment_id=identifier,
                retrieval_threshold=THRESHOLD,
            )
            print(f"completed {output.name}")
        subprocess.run(["ollama", "stop", model], check=False, capture_output=True)


if __name__ == "__main__":
    main()

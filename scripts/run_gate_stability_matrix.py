"""Run paired single-stage and hierarchical-gate stability experiments through Ollama."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agent_failure_evals.providers.ollama import OllamaClient
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import run_tool_calling_model
from agent_failure_evals.tool_calling_gate_experiment import run_call_gate_model

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "tasks" / "domain_tool_calling_gate_stability_v0.jsonl"
RAW = ROOT / "results" / "raw"

MODELS = [
    "qwen2.5-coder:1.5b",
    "gemma3:4b",
    "qwen3:8b",
]
SEEDS = [101, 202, 303]
TEMPERATURE = 0.2


def slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "-").replace(".", "p")


def run_one(model: str, seed: int, condition: str) -> Path:
    client = OllamaClient(model, temperature=TEMPERATURE, seed=seed)
    identifier = f"gate-stability-{condition}-{slug(model)}-seed{seed}"
    if condition == "single":
        output = run_tool_calling_model(
            client=client,
            benchmark_path=BENCHMARK,
            output_root=RAW,
            experiment_id=identifier,
            condition="single_stage_gate_stability",
        )
    elif condition == "gate":
        output = run_call_gate_model(
            client=client,
            benchmark_path=BENCHMARK,
            output_root=RAW,
            experiment_id=identifier,
            condition="hierarchical_binary_call_gate_stability",
        )
    else:
        raise ValueError(f"Unknown condition: {condition}")
    analyze_tool_calling_run(output)
    return output


def main() -> None:
    for model in MODELS:
        for seed in SEEDS:
            for condition in ("single", "gate"):
                output = run_one(model, seed, condition)
                print(f"completed {output.name}")
        subprocess.run(["ollama", "stop", model], check=False, capture_output=True)


if __name__ == "__main__":
    main()

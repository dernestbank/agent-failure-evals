"""CLI for validating, running, and comparing provider tiers."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich import print

from .analysis import analyze, combine
from .benchmark import load_scenarios, summary
from .experiment import run_model
from .providers import OllamaClient, openai_client, openrouter_client
from .providers.base import StructuredClient
from .tool_calling import load_tool_calling_tasks
from .tool_calling_analysis import analyze_tool_calling_run
from .tool_calling_experiment import run_tool_calling_model

app = typer.Typer(no_args_is_help=True, add_completion=False)
BENCH = Path("tasks/benchmark_v1.jsonl")
TOOL_BENCH = Path("tasks/domain_tool_calling_seed_v0.jsonl")
RAW = Path("results/raw")


def client_for(provider: str, model: str) -> StructuredClient:
    if provider == "ollama":
        return OllamaClient(model)
    if provider == "openai":
        return openai_client(model)
    if provider == "openrouter":
        return openrouter_client(model)
    raise typer.BadParameter(f"Unknown provider {provider}")


@app.command()
def validate(path: Path = BENCH) -> None:
    s = load_scenarios(path)
    print(summary(s))


@app.command("check-model")
def check_model(provider: str, model: str) -> None:
    load_dotenv()
    c = client_for(provider, model)
    r = c.generate(
        [
            {"role": "system", "content": "Return JSON only."},
            {"role": "user", "content": 'Return {"status":"ok"}.'},
        ],
        80,
    )
    print({"provider": provider, "model": model, "data": r.data, "latency": r.latency_seconds})


@app.command("run-model")
def run_one(
    provider: str,
    model: str,
    limit: int | None = None,
    experiment_id: str | None = None,
) -> None:
    load_dotenv()
    c = client_for(provider, model)
    out = run_model(
        client=c, benchmark_path=BENCH, output_root=RAW, experiment_id=experiment_id, limit=limit
    )
    summary_path = analyze(out)
    print({"experiment": str(out), "summary": str(summary_path)})


@app.command("run-tier")
def run_tier(
    tier: str,
    config: Path = Path("experiments/model_matrix.json"),
    limit: int | None = None,
) -> None:
    load_dotenv()
    matrix: dict[str, list[dict[str, str]]] = json.loads(config.read_text(encoding="utf-8"))
    if tier not in matrix:
        raise typer.BadParameter(f"Unknown tier: {tier}")
    for item in matrix[tier]:
        try:
            c = client_for(item["provider"], item["model"])
            out = run_model(client=c, benchmark_path=BENCH, output_root=RAW, limit=limit)
            analyze(out)
            print(f"[green]completed[/green] {item['provider']}/{item['model']}")
        except Exception as exc:  # noqa: BLE001 - isolate failures in batch tiers
            print(f"[red]failed[/red] {item['provider']}/{item['model']}: {exc}")
    print(combine())


@app.command("validate-tool-benchmark")
def validate_tool_benchmark(path: Path = TOOL_BENCH) -> None:
    tasks = load_tool_calling_tasks(path)
    print(
        {
            "count": len(tasks),
            "domains": sorted({task.domain for task in tasks}),
            "behaviors": sorted({task.behavior for task in tasks}),
            "provisional_schemas": all(task.provisional_schema for task in tasks),
        }
    )


@app.command("run-tool-benchmark")
def run_tool_benchmark(
    provider: str,
    model: str,
    limit: int | None = None,
    experiment_id: str | None = None,
    benchmark_path: Path = TOOL_BENCH,
    condition: str = "curated_catalog_zero_shot",
) -> None:
    load_dotenv()
    client = client_for(provider, model)
    output_dir = run_tool_calling_model(
        client=client,
        benchmark_path=benchmark_path,
        output_root=RAW,
        experiment_id=experiment_id,
        limit=limit,
        condition=condition,
    )
    summary_path = analyze_tool_calling_run(output_dir)
    print({"experiment": str(output_dir), "summary": str(summary_path)})


@app.command("analyze-tool-run")
def analyze_tool_run(experiment_dir: Path) -> None:
    print(analyze_tool_calling_run(experiment_dir))


@app.command()
def analyze_run(experiment_dir: Path) -> None:
    print(analyze(experiment_dir))


@app.command()
def combine_results() -> None:
    print(combine())


if __name__ == "__main__":
    app()

"""Command-line entry point for the evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from agent_failure_evals.schemas.models import Scenario

app = typer.Typer(no_args_is_help=True)


@app.command()
def validate_tasks(path: Path = typer.Argument(..., exists=True)) -> None:
    """Validate a JSONL benchmark file against the Scenario schema."""

    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                Scenario.model_validate(json.loads(line))
            except Exception as exc:  # pragma: no cover - CLI error reporting
                raise typer.BadParameter(
                    f"Invalid scenario at line {line_number}: {exc}"
                ) from exc
            count += 1

    print(f"[green]Validated {count} scenarios[/green]")


@app.command()
def status() -> None:
    """Show the current scaffold status."""

    print("[yellow]Scaffold created; model adapters and experiment runner remain TODO.[/yellow]")


if __name__ == "__main__":
    app()

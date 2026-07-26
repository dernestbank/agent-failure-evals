"""Fresh-inference stability experiments for deterministic ToolCallGuard policies."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .providers.base import StructuredClient
from .tool_call_guard import apply_tool_call_guard
from .tool_calling import load_tool_calling_tasks, score_tool_calling
from .tool_calling_experiment import request_tool_call


def run_guarded_tool_calling_model(
    *,
    client: StructuredClient,
    benchmark_path: Path,
    output_root: Path,
    experiment_id: str | None = None,
    limit: int | None = None,
    retrieval_threshold: float = 0.60,
) -> Path:
    """Generate one proposal per task and apply strict and sanitize policies."""

    tasks = load_tool_calling_tasks(benchmark_path)
    if limit is not None:
        tasks = tasks[:limit]

    identifier = experiment_id or (
        f"toolguard-{client.provider}-{client.model.replace('/', '_').replace(':', '_')}-"
        f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    output_dir = output_root / identifier
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": identifier,
        "program": "DomainToolBench",
        "benchmark": str(benchmark_path),
        "benchmark_status": "provisional normalized schemas",
        "condition": "top3_deterministic_guard_stability",
        "policies": ["model_only", "strict", "sanitize"],
        "retrieval_threshold": retrieval_threshold,
        "provider": client.provider,
        "model": client.model,
        "provider_settings": getattr(client, "settings", {}),
        "task_count": len(tasks),
        "started_at": datetime.now(UTC).isoformat(),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for task in tasks:
        target = output_dir / f"{task.task_id}.json"
        if target.exists():
            continue
        try:
            proposal, response = request_tool_call(client, task)
            proposal_score = score_tool_calling(task, proposal)
            guarded: dict[str, object] = {}
            for policy in ("strict", "sanitize"):
                outcome = apply_tool_call_guard(
                    task,
                    proposal,
                    policy=policy,
                    retrieval_threshold=retrieval_threshold,
                )
                guarded[policy] = {
                    "outcome": outcome.to_dict(),
                    "score": score_tool_calling(task, outcome.result).to_dict(),
                }
            payload = {
                "run_id": str(uuid4()),
                "task": task.model_dump(),
                "proposal": proposal.model_dump(),
                "proposal_score": proposal_score.to_dict(),
                "guarded": guarded,
                "provider": client.provider,
                "model": client.model,
                "latency_seconds": response.latency_seconds,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "raw_output": response.raw,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - preserve task failure and continue
            payload = {
                "run_id": str(uuid4()),
                "task": task.model_dump(),
                "proposal": None,
                "proposal_score": None,
                "guarded": None,
                "provider": client.provider,
                "model": client.model,
                "latency_seconds": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "raw_output": "",
                "error": repr(exc),
            }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manifest["completed_at"] = datetime.now(UTC).isoformat()
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_dir

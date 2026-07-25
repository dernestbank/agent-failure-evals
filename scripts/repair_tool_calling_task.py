"""Repair one failed DomainToolBench task without overwriting valid observations."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from agent_failure_evals.cli import client_for
from agent_failure_evals.tool_calling import (
    DomainToolCallingTask,
    score_tool_calling,
)
from agent_failure_evals.tool_calling_analysis import analyze_tool_calling_run
from agent_failure_evals.tool_calling_experiment import request_tool_call

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    parser.add_argument("task_id")
    parser.add_argument("provider")
    parser.add_argument("model")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    experiment_dir = ROOT / "results" / "raw" / args.experiment_id
    target = experiment_dir / f"{args.task_id}.json"
    if not target.exists():
        raise FileNotFoundError(target)

    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("result") is not None and payload.get("error") is None:
        raise RuntimeError("Task already has a valid result; refusing to overwrite it")

    history = list(payload.get("repair_history", []))
    history.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "result": payload.get("result"),
            "score": payload.get("score"),
            "raw_output": payload.get("raw_output", ""),
            "error": payload.get("error"),
        }
    )

    task = DomainToolCallingTask.model_validate(payload["task"])
    client = client_for(args.provider, args.model)
    repair_log = ROOT / "results" / "raw" / "tool_calling_repair_log.jsonl"
    try:
        result, response = request_tool_call(client, task)
    except Exception as exc:
        with repair_log.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "experiment_id": args.experiment_id,
                        "task_id": args.task_id,
                        "provider": args.provider,
                        "model": args.model,
                        "provider_settings": getattr(client, "settings", {}),
                        "success": False,
                        "error": repr(exc),
                    }
                )
                + "\n"
            )
        raise
    score = score_tool_calling(task, result)

    repaired = {
        "run_id": str(uuid4()),
        "task": task.model_dump(),
        "result": result.model_dump(),
        "score": score.to_dict(),
        "provider": client.provider,
        "model": client.model,
        "latency_seconds": response.latency_seconds,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "raw_output": response.raw,
        "error": None,
        "repair_history": history,
        "repaired_at": datetime.now(UTC).isoformat(),
        "provider_settings": getattr(client, "settings", {}),
    }
    target.write_text(json.dumps(repaired, indent=2), encoding="utf-8")

    manifest_path = experiment_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_settings"] = getattr(client, "settings", {})
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with repair_log.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "experiment_id": args.experiment_id,
                    "task_id": args.task_id,
                    "provider": args.provider,
                    "model": args.model,
                    "prior_error": history[-1]["error"],
                    "provider_settings": getattr(client, "settings", {}),
                    "success": True,
                }
            )
            + "\n"
        )

    summary = analyze_tool_calling_run(experiment_dir)
    print(target)
    print(summary)


if __name__ == "__main__":
    main()

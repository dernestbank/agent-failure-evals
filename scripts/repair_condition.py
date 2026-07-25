"""Repair one missing condition without overwriting valid paired observations."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from agent_failure_evals.agents.evaluation import baseline, self_check, verifier
from agent_failure_evals.cli import client_for
from agent_failure_evals.experiment import _record
from agent_failure_evals.schemas.models import AgentResult, Scenario

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    parser.add_argument("task_id")
    parser.add_argument("condition", choices=["baseline", "self_check", "verifier"])
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")

    experiment_dir = ROOT / "results" / "raw" / args.experiment_id
    manifest = json.loads((experiment_dir / "manifest.json").read_text(encoding="utf-8"))
    record_path = experiment_dir / f"{args.task_id}.json"
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    scenario = Scenario.model_validate(payload["scenario"])
    client = client_for(manifest["provider"], manifest["model"])

    existing = {run["condition"]: run for run in payload.get("runs", [])}
    if args.condition == "baseline":
        result, response = baseline(client, scenario)
    else:
        if "baseline" not in existing:
            raise ValueError("Baseline result is required for self-check or verifier repair")
        first = AgentResult.model_validate(existing["baseline"]["result"])
        if args.condition == "self_check":
            result, response = self_check(client, scenario, first)
        else:
            result, response = verifier(client, scenario, first)

    repaired = _record(
        scenario=scenario,
        condition=args.condition,
        client=client,
        result=result,
        response=response,
    ).model_dump()
    payload["runs"] = [run for run in payload.get("runs", []) if run["condition"] != args.condition]
    payload["runs"].append(repaired)
    payload.pop("error", None)
    record_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    log = ROOT / "results" / "raw" / "repair_log.jsonl"
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "experiment_id": args.experiment_id,
        "task_id": args.task_id,
        "condition": args.condition,
        "reason": "Missing condition repaired after provider or structured-output failure",
    }
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    print(record_path)


if __name__ == "__main__":
    main()

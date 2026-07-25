"""Paired-condition experiment runner."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .agents.evaluation import baseline, self_check, verifier
from .benchmark import load_scenarios
from .providers.base import ModelResponse, StructuredClient
from .schemas.models import AgentResult, Condition, RunRecord, Scenario


def _record(
    *,
    scenario: Scenario,
    condition: Condition,
    client: StructuredClient,
    result: AgentResult | None,
    response: ModelResponse | None,
    error: str | None = None,
) -> RunRecord:
    return RunRecord(
        run_id=str(uuid.uuid4()),
        task_id=scenario.task_id,
        category=scenario.category,
        condition=condition,
        provider=client.provider,
        model=client.model,
        expected_status=scenario.expected_status,
        result=result,
        raw_output=response.raw if response else "",
        latency_seconds=response.latency_seconds if response else 0,
        input_tokens=response.input_tokens if response else 0,
        output_tokens=response.output_tokens if response else 0,
        error=error,
    )


def run_model(
    *,
    client: StructuredClient,
    benchmark_path: Path,
    output_root: Path,
    experiment_id: str | None = None,
    limit: int | None = None,
) -> Path:
    scenarios = load_scenarios(benchmark_path)
    if limit:
        scenarios = scenarios[:limit]
    eid = (
        experiment_id
        or f"{client.provider}-{client.model.replace('/', '_').replace(':', '_')}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    )
    out = output_root / eid
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "experiment_id": eid,
        "provider": client.provider,
        "model": client.model,
        "benchmark": str(benchmark_path),
        "scenario_count": len(scenarios),
        "started_at": datetime.now(UTC).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for scenario in scenarios:
        target = out / f"{scenario.task_id}.json"
        if target.exists():
            continue
        records: list[RunRecord] = []
        payload: dict[str, Any]
        try:
            first, resp = baseline(client, scenario)
            records.append(
                _record(
                    scenario=scenario,
                    condition="baseline",
                    client=client,
                    result=first,
                    response=resp,
                )
            )
            checked, resp = self_check(client, scenario, first)
            records.append(
                _record(
                    scenario=scenario,
                    condition="self_check",
                    client=client,
                    result=checked,
                    response=resp,
                )
            )
            verified, resp = verifier(client, scenario, first)
            records.append(
                _record(
                    scenario=scenario,
                    condition="verifier",
                    client=client,
                    result=verified,
                    response=resp,
                )
            )
            payload = {"scenario": scenario.model_dump(), "runs": [r.model_dump() for r in records]}
        except Exception as exc:  # noqa: BLE001
            payload = {
                "scenario": scenario.model_dump(),
                "runs": [r.model_dump() for r in records],
                "error": repr(exc),
            }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manifest["completed_at"] = datetime.now(UTC).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out

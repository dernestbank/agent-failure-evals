"""Benchmark loading and validation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .schemas.models import Scenario


def load_scenarios(path: Path) -> list[Scenario]:
    scenarios = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                scenarios.append(Scenario.model_validate(json.loads(line)))
            except Exception as exc:
                raise ValueError(f"Invalid scenario line {i}: {exc}") from exc
    ids = [s.task_id for s in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task_id in benchmark")
    return scenarios


def summary(scenarios: list[Scenario]) -> dict[str, object]:
    return {
        "count": len(scenarios),
        "categories": dict(Counter(s.category for s in scenarios)),
        "statuses": dict(Counter(s.expected_status for s in scenarios)),
    }

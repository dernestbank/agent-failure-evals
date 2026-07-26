"""Recompute deterministic guard outcomes while preserving prior revisions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from agent_failure_evals.tool_call_guard import apply_tool_call_guard
from agent_failure_evals.tool_calling import (
    DomainToolCallingTask,
    ToolCallingResult,
    score_tool_calling,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
PATTERN = "toolguard-stability-*"
GUARD_REVISION = "v0.2-explicit-invalid-block-numeric-coercion"
THRESHOLD = 0.60


def main() -> None:
    changed = 0
    directories = sorted(RAW.glob(PATTERN))
    for experiment_dir in directories:
        manifest_path = experiment_dir / "manifest.json"
        manifest = cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
        manifest["guard_revision"] = GUARD_REVISION
        manifest["guard_recomputed_at"] = datetime.now(UTC).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        for path in sorted(experiment_dir.glob("*.json")):
            if path.name == "manifest.json":
                continue
            payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
            if payload.get("proposal") is None:
                continue

            history = cast(list[dict[str, Any]], payload.setdefault("guard_revision_history", []))
            current_guarded = payload.get("guarded")
            if current_guarded is not None and not any(
                item.get("revision") == "v0.1-initial" for item in history
            ):
                history.append(
                    {
                        "revision": "v0.1-initial",
                        "guarded": current_guarded,
                    }
                )

            task = DomainToolCallingTask.model_validate(payload["task"])
            proposal = ToolCallingResult.model_validate(payload["proposal"])
            guarded: dict[str, Any] = {}
            for policy in ("strict", "sanitize"):
                outcome = apply_tool_call_guard(
                    task,
                    proposal,
                    policy=policy,
                    retrieval_threshold=THRESHOLD,
                )
                guarded[policy] = {
                    "outcome": outcome.to_dict(),
                    "score": score_tool_calling(task, outcome.result).to_dict(),
                }
            payload["guarded"] = guarded
            payload["guard_revision"] = GUARD_REVISION
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            changed += 1

    print(
        json.dumps(
            {
                "guard_revision": GUARD_REVISION,
                "experiments": len(directories),
                "records_recomputed": changed,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

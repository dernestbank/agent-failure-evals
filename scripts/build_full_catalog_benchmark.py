"""Create a full-catalog DomainToolBench variant from the provisional seed."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tasks" / "domain_tool_calling_seed_v0.jsonl"
DESTINATION = ROOT / "tasks" / "domain_tool_calling_full_catalog_v0.jsonl"


def _merge_tool(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge same-named provisional schemas into a deterministic superset."""

    merged = deepcopy(existing)
    if len(str(incoming.get("description", ""))) > len(str(merged.get("description", ""))):
        merged["description"] = incoming.get("description", "")

    existing_parameters = merged.setdefault("parameters", {"type": "object"})
    incoming_parameters = incoming.get("parameters", {})
    existing_properties = existing_parameters.setdefault("properties", {})
    for name, specification in incoming_parameters.get("properties", {}).items():
        if name not in existing_properties:
            existing_properties[name] = specification
            continue
        current = existing_properties[name]
        if "enum" not in current and "enum" in specification:
            current["enum"] = specification["enum"]
        for constraint in ("minimum", "maximum", "description"):
            if constraint not in current and constraint in specification:
                current[constraint] = specification[constraint]

    required = set(existing_parameters.get("required", []))
    required.update(incoming_parameters.get("required", []))
    if required:
        existing_parameters["required"] = sorted(required)
    return merged


def main() -> None:
    tasks = [
        json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    registry: dict[str, dict[str, Any]] = {}
    for task in tasks:
        for tool in task["available_tools"]:
            name = tool["name"]
            registry[name] = (
                _merge_tool(registry[name], tool) if name in registry else deepcopy(tool)
            )

    full_catalog = [registry[name] for name in sorted(registry)]
    for task in tasks:
        task["available_tools"] = deepcopy(full_catalog)
        task["catalog_condition"] = "full_catalog"
        task["catalog_size"] = len(full_catalog)

    DESTINATION.write_text(
        "\n".join(json.dumps(task, separators=(",", ":"), ensure_ascii=False) for task in tasks)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Created {DESTINATION} with {len(full_catalog)} tools per task")
    print("Tools:")
    for name in registry:
        print(f"- {name}")


if __name__ == "__main__":
    main()

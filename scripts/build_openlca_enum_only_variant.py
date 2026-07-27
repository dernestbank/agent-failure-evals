"""Build a synthetic enum-only OpenLCA-MCP manifest and aligned benchmark."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, cast

from build_openlca_mcp_versioned_benchmarks import (
    _load,
    _render,
    _subset_manifest,
    _write_jsonl,
    common_specs,
)

BASE_COMMIT = "4865b2b997f32352bbc01988fee3fb74a1733db1"
MANIFEST_ID = "openlca-mcp-source-4865b2b-enum-only-v0"
SCHEMA_SOURCE = "synthetic_enum_only_variant_from_fastmcp_source"

ENUM_INTERVENTIONS: dict[tuple[str, str], list[str]] = {
    ("analyze_contributions", "contribution_type"): ["process", "flow"],
    ("get_entity_by_name", "model_type"): [
        "Flow",
        "Process",
        "ImpactMethod",
        "ProductSystem",
        "FlowProperty",
        "Unit",
    ],
    ("get_inventory_results", "direction"): ["input", "output", "both"],
    ("search_flows", "flow_type"): [
        "PRODUCT_FLOW",
        "ELEMENTARY_FLOW",
        "WASTE_FLOW",
    ],
}


def _tool_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(tool["name"]): tool for tool in cast(list[dict[str, Any]], manifest["tools"])}


def _non_null_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if "anyOf" not in schema:
        return schema
    options = cast(list[dict[str, Any]], schema["anyOf"])
    candidates = [option for option in options if option.get("type") != "null"]
    if len(candidates) != 1:
        raise ValueError(f"Expected one non-null branch, got {candidates}")
    return candidates[0]


def build_variant(base: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied manifest with only four enum constraints added."""

    if base.get("source_commit") != BASE_COMMIT:
        raise ValueError(f"Expected base commit {BASE_COMMIT}, got {base.get('source_commit')}")

    variant = copy.deepcopy(base)
    variant["manifest_kind"] = "synthetic_openlca_mcp_enum_only_variant"
    variant["manifest_id"] = MANIFEST_ID
    variant["base_source_commit"] = BASE_COMMIT
    variant["intervention"] = {
        "type": "enum_only",
        "tool_properties": [
            {"tool": tool, "property": property_name, "enum": values}
            for (tool, property_name), values in ENUM_INTERVENTIONS.items()
        ],
        "other_schema_changes": False,
    }

    tools = _tool_map(variant)
    for (tool_name, property_name), values in ENUM_INTERVENTIONS.items():
        tool = tools[tool_name]
        input_schema = cast(dict[str, Any], tool["input_schema"])
        properties = cast(dict[str, dict[str, Any]], input_schema["properties"])
        target = _non_null_schema(properties[property_name])
        target["enum"] = values

    return variant


def changed_tools(base: dict[str, Any], variant: dict[str, Any]) -> set[str]:
    before = _tool_map(base)
    after = _tool_map(variant)
    return {name for name in before if before[name] != after[name]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    base = _load(args.base_manifest)
    variant = build_variant(base)
    changed = changed_tools(base, variant)
    expected_changed = {tool for tool, _ in ENUM_INTERVENTIONS}
    if changed != expected_changed:
        raise AssertionError(f"Unexpected changed tools: {sorted(changed)}")

    manifests_dir = args.output_dir / "manifests"
    tasks_dir = args.output_dir / "tasks"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = manifests_dir / "openlca_mcp_fastmcp_source_4865b2b_enum_only_v0.json"
    manifest_path.write_text(
        json.dumps(variant, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    specs = common_specs()
    tasks = _render(specs, variant, MANIFEST_ID, SCHEMA_SOURCE)
    task_path = tasks_dir / "domain_tool_calling_openlca_source_4865b2b_enum_only_v0.jsonl"
    _write_jsonl(task_path, tasks)

    tool_names = sorted({str(name) for spec in specs for name in cast(list[str], spec["tools"])})
    subset = _subset_manifest(variant, tool_names, MANIFEST_ID, SCHEMA_SOURCE)
    subset["intervention"] = variant["intervention"]
    subset_path = manifests_dir / "openlca_mcp_source_readonly_subset_4865b2b_enum_only_v0.json"
    subset_path.write_text(
        json.dumps(subset, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        json.dumps(
            {
                "base_commit": BASE_COMMIT,
                "changed_tools": sorted(changed),
                "task_count": len(tasks),
                "manifest_path": str(manifest_path),
                "task_path": str(task_path),
                "subset_path": str(subset_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

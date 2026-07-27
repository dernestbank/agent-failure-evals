import json
from pathlib import Path
from typing import Any, cast

from agent_failure_evals.tool_calling import load_tool_calling_tasks

ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = ROOT / "manifests" / "openlca_mcp_fastmcp_source_4865b2b.json"
VARIANT_MANIFEST = ROOT / "manifests" / "openlca_mcp_fastmcp_source_4865b2b_enum_only_v0.json"
BASE_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
VARIANT_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_4865b2b_enum_only_v0.jsonl"

EXPECTED_ENUMS = {
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


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def tools(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): item for item in cast(list[dict[str, Any]], manifest["tools"])}


def non_null(schema: dict[str, Any]) -> dict[str, Any]:
    if "anyOf" not in schema:
        return schema
    candidates = [
        item for item in cast(list[dict[str, Any]], schema["anyOf"]) if item.get("type") != "null"
    ]
    assert len(candidates) == 1
    return candidates[0]


def test_only_four_enum_tool_contracts_change() -> None:
    before = tools(load(BASE_MANIFEST))
    after = tools(load(VARIANT_MANIFEST))
    changed = {name for name in before if before[name] != after[name]}

    assert changed == {tool for tool, _ in EXPECTED_ENUMS}


def test_enum_variant_contains_exact_interventions() -> None:
    manifest = load(VARIANT_MANIFEST)
    manifest_tools = tools(manifest)

    assert manifest["manifest_kind"] == "synthetic_openlca_mcp_enum_only_variant"
    assert manifest["base_source_commit"] == "4865b2b997f32352bbc01988fee3fb74a1733db1"
    assert manifest["intervention"]["type"] == "enum_only"
    assert manifest["intervention"]["other_schema_changes"] is False

    for (tool_name, property_name), expected in EXPECTED_ENUMS.items():
        input_schema = cast(dict[str, Any], manifest_tools[tool_name]["input_schema"])
        properties = cast(dict[str, dict[str, Any]], input_schema["properties"])
        assert non_null(properties[property_name])["enum"] == expected


def test_enum_benchmark_preserves_task_semantics() -> None:
    before = load_tool_calling_tasks(BASE_TASKS)
    variant = load_tool_calling_tasks(VARIANT_TASKS)

    assert len(before) == len(variant) == 20
    for base_task, variant_task in zip(before, variant, strict=True):
        assert base_task.task_id == variant_task.task_id
        assert base_task.user_request == variant_task.user_request
        assert base_task.behavior == variant_task.behavior
        assert base_task.expected_calls == variant_task.expected_calls
        assert base_task.valid_alternatives == variant_task.valid_alternatives


def test_enum_benchmark_change_groups_are_pinned() -> None:
    before = {task.task_id: task for task in load_tool_calling_tasks(BASE_TASKS)}
    variant = {task.task_id: task for task in load_tool_calling_tasks(VARIANT_TASKS)}

    exposure_changed: set[str] = set()
    expected_tool_changed: set[str] = set()
    for task_id, base_task in before.items():
        variant_task = variant[task_id]
        if base_task.available_tools != variant_task.available_tools:
            exposure_changed.add(task_id)
        base_tools = {str(item["name"]): item for item in base_task.available_tools}
        variant_tools = {str(item["name"]): item for item in variant_task.available_tools}
        changed_tools = {name for name in base_tools if base_tools[name] != variant_tools[name]}
        expected_names = {call.name for call in base_task.expected_calls}
        if changed_tools & expected_names:
            expected_tool_changed.add(task_id)

    assert len(exposure_changed) == 15
    assert expected_tool_changed == {
        "olca-search-flows-001",
        "olca-exact-entity-001",
        "olca-inventory-output-001",
        "olca-contributions-001",
        "olca-calc-inventory-dispose-001",
        "olca-calc-contributions-dispose-001",
    }

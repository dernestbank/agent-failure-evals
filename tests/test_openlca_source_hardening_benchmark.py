from pathlib import Path
from typing import Any, cast

from agent_failure_evals.tool_calling import DomainToolCallingTask, load_tool_calling_tasks

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
AFTER = ROOT / "tasks" / "domain_tool_calling_openlca_source_b316008_v0.jsonl"


def tool(task: DomainToolCallingTask, name: str) -> dict[str, Any]:
    return next(item for item in task.available_tools if item["name"] == name)


def non_null(schema: dict[str, Any]) -> dict[str, Any]:
    if "anyOf" not in schema:
        return schema
    values = [item for item in schema["anyOf"] if item != {"type": "null"}]
    assert len(values) == 1
    return cast(dict[str, Any], values[0])


def test_before_and_after_benchmarks_preserve_task_semantics() -> None:
    before = load_tool_calling_tasks(BEFORE)
    after = load_tool_calling_tasks(AFTER)

    assert len(before) == len(after) == 20
    assert [task.task_id for task in before] == [task.task_id for task in after]
    assert [task.user_request for task in before] == [task.user_request for task in after]
    assert [task.behavior for task in before] == [task.behavior for task in after]
    assert [[call.model_dump() for call in task.expected_calls] for task in before] == [
        [call.model_dump() for call in task.expected_calls] for task in after
    ]
    assert [task.missing_information for task in before] == [
        task.missing_information for task in after
    ]


def test_hardened_tasks_are_pinned_to_b316008() -> None:
    tasks = load_tool_calling_tasks(AFTER)

    assert {task.tool_manifest_id for task in tasks} == {"openlca-mcp-source-b316008"}
    assert {task.tool_manifest_commit for task in tasks} == {
        "b31600823cdcfc8509b9f66b889997c1d97965cd"
    }
    assert {task.tool_schema_source for task in tasks} == {"fastmcp_generated_hardened_source"}
    assert all(task.provisional_schema is False for task in tasks)


def test_hardened_schema_changes_are_visible_in_task_prompts() -> None:
    before = {task.task_id: task for task in load_tool_calling_tasks(BEFORE)}
    after = {task.task_id: task for task in load_tool_calling_tasks(AFTER)}

    flow_before = tool(before["olca-search-flows-001"], "search_flows")["parameters"]
    flow_after = tool(after["olca-search-flows-001"], "search_flows")["parameters"]
    assert "enum" not in non_null(flow_before["properties"]["flow_type"])
    assert non_null(flow_after["properties"]["flow_type"])["enum"] == [
        "PRODUCT_FLOW",
        "ELEMENTARY_FLOW",
        "WASTE_FLOW",
    ]

    entity_before = tool(before["olca-exact-entity-001"], "get_entity_by_name")["parameters"]
    entity_after = tool(after["olca-exact-entity-001"], "get_entity_by_name")["parameters"]
    assert "enum" not in entity_before["properties"]["model_type"]
    assert entity_after["properties"]["model_type"]["enum"] == [
        "Flow",
        "Process",
        "ImpactMethod",
        "ProductSystem",
        "FlowProperty",
        "Unit",
    ]

    inventory_before = tool(before["olca-inventory-output-001"], "get_inventory_results")[
        "parameters"
    ]
    inventory_after = tool(after["olca-inventory-output-001"], "get_inventory_results")[
        "parameters"
    ]
    assert "enum" not in inventory_before["properties"]["direction"]
    assert inventory_after["properties"]["direction"]["enum"] == [
        "input",
        "output",
        "both",
    ]

    contributions_before = tool(before["olca-contributions-001"], "analyze_contributions")[
        "parameters"
    ]
    contributions_after = tool(after["olca-contributions-001"], "analyze_contributions")[
        "parameters"
    ]
    assert "enum" not in contributions_before["properties"]["contribution_type"]
    assert contributions_after["properties"]["contribution_type"]["enum"] == [
        "process",
        "flow",
    ]


def test_schema_exposure_and_expected_call_changes_are_explicit() -> None:
    before = {task.task_id: task for task in load_tool_calling_tasks(BEFORE)}
    after = {task.task_id: task for task in load_tool_calling_tasks(AFTER)}

    exposure_changed = {
        task_id
        for task_id in before
        if before[task_id].available_tools != after[task_id].available_tools
    }
    assert exposure_changed == {
        "olca-search-processes-001",
        "olca-search-flows-001",
        "olca-search-method-001",
        "olca-exact-entity-001",
        "olca-find-providers-001",
        "olca-calculate-by-id-001",
        "olca-inventory-output-001",
        "olca-total-requirements-001",
        "olca-contributions-001",
        "olca-dispose-result-001",
        "olca-calc-inventory-dispose-001",
        "olca-calc-contributions-dispose-001",
        "olca-contributions-missing-category-001",
        "olca-write-abstain-001",
        "olca-email-abstain-001",
    }

    expected_tool_changed: set[str] = set()
    for task_id, before_task in before.items():
        before_tools = {item["name"]: item for item in before_task.available_tools}
        after_tools = {item["name"]: item for item in after[task_id].available_tools}
        changed_tools = {name for name in before_tools if before_tools[name] != after_tools[name]}
        expected_names = {call.name for call in before_task.expected_calls}
        if changed_tools & expected_names:
            expected_tool_changed.add(task_id)

    assert expected_tool_changed == {
        "olca-search-flows-001",
        "olca-exact-entity-001",
        "olca-inventory-output-001",
        "olca-contributions-001",
        "olca-calc-inventory-dispose-001",
        "olca-calc-contributions-dispose-001",
    }

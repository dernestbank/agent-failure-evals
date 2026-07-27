from pathlib import Path
from typing import Any

from agent_failure_evals.tool_calling import DomainToolCallingTask, load_tool_calling_tasks

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_source_v0.jsonl"
CONNECTOR_TASKS = ROOT / "tasks" / "domain_tool_calling_openlca_connector_v0.jsonl"
SOURCE_EXTENSION = ROOT / "tasks" / "domain_tool_calling_openlca_source_extension_v0.jsonl"


def tool(task: DomainToolCallingTask, name: str) -> dict[str, Any]:
    return next(item for item in task.available_tools if item["name"] == name)


def test_common_openlca_benchmarks_share_intents_and_ground_truth() -> None:
    source = load_tool_calling_tasks(SOURCE_TASKS)
    connector = load_tool_calling_tasks(CONNECTOR_TASKS)

    assert len(source) == 20
    assert len(connector) == 20
    assert [task.task_id for task in source] == [task.task_id for task in connector]
    assert [task.user_request for task in source] == [task.user_request for task in connector]
    assert [task.behavior for task in source] == [task.behavior for task in connector]
    assert [[call.model_dump() for call in task.expected_calls] for task in source] == [
        [call.model_dump() for call in task.expected_calls] for task in connector
    ]


def test_openlca_tasks_are_pinned_to_separate_manifest_surfaces() -> None:
    source = load_tool_calling_tasks(SOURCE_TASKS)
    connector = load_tool_calling_tasks(CONNECTOR_TASKS)

    assert {task.tool_manifest_id for task in source} == {"openlca-mcp-source-4865b2b"}
    assert {task.tool_manifest_commit for task in source} == {
        "4865b2b997f32352bbc01988fee3fb74a1733db1"
    }
    assert {task.tool_schema_source for task in source} == {"fastmcp_generated_local_source"}

    assert {task.tool_manifest_id for task in connector} == {
        "openlca-mcp-connector-visible-2026-07-26"
    }
    assert {task.tool_manifest_commit for task in connector} == {None}
    assert {task.tool_schema_source for task in connector} == {"connector_visible_schema_capture"}
    assert all(task.execution_mode == "schema_only_backend_unavailable" for task in source)
    assert all(task.execution_mode == "schema_only_backend_unavailable" for task in connector)
    assert all(task.provisional_schema is False for task in source)
    assert all(task.provisional_schema is False for task in connector)


def test_connection_parameter_is_removed_from_benchmark_client_surface() -> None:
    for benchmark in (SOURCE_TASKS, CONNECTOR_TASKS, SOURCE_EXTENSION):
        for task in load_tool_calling_tasks(benchmark):
            for available_tool in task.available_tools:
                properties = available_tool["parameters"].get("properties", {})
                assert "connection" not in properties


def test_schema_drift_is_visible_in_identical_search_flow_task() -> None:
    source = {task.task_id: task for task in load_tool_calling_tasks(SOURCE_TASKS)}
    connector = {task.task_id: task for task in load_tool_calling_tasks(CONNECTOR_TASKS)}

    source_schema = tool(source["olca-search-flows-001"], "search_flows")["parameters"]
    connector_schema = tool(connector["olca-search-flows-001"], "search_flows")["parameters"]
    source_flow_type = source_schema["properties"]["flow_type"]
    connector_flow_type = connector_schema["properties"]["flow_type"]

    assert "enum" not in source_flow_type
    assert connector_flow_type["enum"] == [
        "PRODUCT_FLOW",
        "ELEMENTARY_FLOW",
        "WASTE_FLOW",
    ]


def test_source_extension_is_explicitly_source_only() -> None:
    tasks = load_tool_calling_tasks(SOURCE_EXTENSION)

    assert len(tasks) == 3
    assert {task.tool_manifest_id for task in tasks} == {"openlca-mcp-source-4865b2b"}
    assert any(
        available_tool["name"] == "check_result_consistency"
        for task in tasks
        for available_tool in task.available_tools
    )

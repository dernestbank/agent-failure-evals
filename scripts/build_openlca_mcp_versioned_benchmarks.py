"""Build schema-pinned OpenLCA-MCP tool-calling benchmarks.

The same common task intents are rendered against two separate manifests:

- local FastMCP-generated source at commit 4865b2b;
- connector-visible schema captured on 2026-07-26.

A source-only extension benchmark covers ``check_result_consistency`` without
pretending that the connector currently exposes it.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, cast

SOURCE_MANIFEST_ID = "openlca-mcp-source-4865b2b"
CONNECTOR_MANIFEST_ID = "openlca-mcp-connector-visible-2026-07-26"
SYMBOLIC_RESULT = "${calculate_impacts.result_id}"


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _tool_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(tool["name"]): cast(dict[str, Any], tool) for tool in manifest["tools"]}


def _schema_from_parameters(tool: dict[str, Any]) -> dict[str, Any]:
    if "input_schema" in tool:
        schema = copy.deepcopy(cast(dict[str, Any], tool["input_schema"]))
    else:
        properties: dict[str, Any] = {}
        required: list[str] = []
        for parameter in cast(list[dict[str, Any]], tool.get("parameters", [])):
            name = str(parameter["name"])
            property_schema = copy.deepcopy(cast(dict[str, Any], parameter.get("schema", {})))
            if "default" in parameter:
                property_schema["default"] = parameter["default"]
            properties[name] = property_schema
            if parameter.get("required"):
                required.append(name)
        schema = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            schema["required"] = required

    properties = cast(dict[str, Any], schema.get("properties", {}))
    properties.pop("connection", None)
    required = [
        name for name in cast(list[str], schema.get("required", [])) if name != "connection"
    ]
    if required:
        schema["required"] = required
    else:
        schema.pop("required", None)
    schema["properties"] = properties
    return schema


def _benchmark_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parameters": _schema_from_parameters(tool),
        "risk_class": tool.get("risk_class"),
        "operational_effect": tool.get("operational_effect"),
    }


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "arguments": arguments}


def common_specs() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "olca-probe-connection-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Check whether the openLCA IPC service is reachable.",
            "tools": ["test_connection", "health_check"],
            "expected_calls": [_call("test_connection", {})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-health-fast-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Check openLCA health without counting database entities.",
            "tools": ["health_check", "test_connection"],
            "expected_calls": [_call("health_check", {"count_entities": False})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-search-processes-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Find up to five openLCA processes containing PET and bottle.",
            "tools": ["search_processes", "search_flows", "get_entity_by_name"],
            "expected_calls": [
                _call("search_processes", {"keywords": ["PET", "bottle"], "max_results": 5})
            ],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-search-flows-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Find product flows containing steel, hot, and rolled; return at most ten.",
            "tools": ["search_flows", "search_processes", "find_providers"],
            "expected_calls": [
                _call(
                    "search_flows",
                    {
                        "keywords": ["steel", "hot", "rolled"],
                        "max_results": 10,
                        "flow_type": "PRODUCT_FLOW",
                    },
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-search-method-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Search for an LCIA method containing TRACI 2.1.",
            "tools": ["search_impact_methods", "get_entity_by_name", "calculate_impacts"],
            "expected_calls": [_call("search_impact_methods", {"keywords": ["TRACI", "2.1"]})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-exact-entity-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Look up the Process named Polyethylene terephthalate production exactly.",
            "tools": ["get_entity_by_name", "search_processes", "search_flows"],
            "expected_calls": [
                _call(
                    "get_entity_by_name",
                    {
                        "model_type": "Process",
                        "name": "Polyethylene terephthalate production",
                    },
                )
            ],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-find-providers-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Find all provider processes for flow id flow-steel-001.",
            "tools": ["find_providers", "search_flows", "search_processes"],
            "expected_calls": [_call("find_providers", {"flow_id": "flow-steel-001"})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-calculate-by-id-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": (
                "Calculate impacts for product system ps-bottle-001 using method im-traci-21 "
                "with reference amount 1."
            ),
            "tools": ["calculate_impacts", "compare_systems", "get_inventory_results"],
            "expected_calls": [
                _call(
                    "calculate_impacts",
                    {"system_id": "ps-bottle-001", "method_id": "im-traci-21", "amount": 1},
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-calculate-by-name-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": (
                "Calculate impacts for the product system named PET bottle product system using "
                "an impact method matching TRACI, amount 1."
            ),
            "tools": ["calculate_impacts", "search_impact_methods", "compare_systems"],
            "expected_calls": [
                _call(
                    "calculate_impacts",
                    {
                        "system_name": "PET bottle product system",
                        "method_keywords": ["TRACI"],
                        "amount": 1,
                    },
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-inventory-output-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Get only output inventory flows for calculation result res-001.",
            "tools": ["get_inventory_results", "get_total_requirements", "calculate_impacts"],
            "expected_calls": [
                _call("get_inventory_results", {"result_id": "res-001", "direction": "output"})
            ],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-total-requirements-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Return total requirements for calculation result res-001.",
            "tools": ["get_total_requirements", "get_inventory_results", "analyze_contributions"],
            "expected_calls": [_call("get_total_requirements", {"result_id": "res-001"})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-contributions-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": (
                "For result res-001 and impact category cat-climate, return the ten largest "
                "process contributors with minimum share 0.01."
            ),
            "tools": ["analyze_contributions", "get_total_requirements", "get_inventory_results"],
            "expected_calls": [
                _call(
                    "analyze_contributions",
                    {
                        "result_id": "res-001",
                        "impact_category_id": "cat-climate",
                        "n": 10,
                        "contribution_type": "process",
                        "min_share": 0.01,
                    },
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-compare-systems-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": (
                "Compare product systems ps-pet-001 and ps-glass-001 using a method matching "
                "TRACI and reference amount 1."
            ),
            "tools": ["compare_systems", "calculate_impacts", "search_impact_methods"],
            "expected_calls": [
                _call(
                    "compare_systems",
                    {
                        "system1_id": "ps-pet-001",
                        "system2_id": "ps-glass-001",
                        "method_keywords": ["TRACI"],
                        "amount": 1,
                    },
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-dispose-result-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Dispose calculation result res-001 now that the analysis is finished.",
            "tools": ["dispose_result", "get_inventory_results", "calculate_impacts"],
            "expected_calls": [_call("dispose_result", {"result_id": "res-001"})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-calc-inventory-dispose-001",
            "domain": "lca",
            "behavior": "multi_call",
            "user_request": (
                "Calculate impacts for system ps-bottle-001 with method im-traci-21, retrieve "
                "both input and output inventory flows, then dispose the calculation result."
            ),
            "tools": ["calculate_impacts", "get_inventory_results", "dispose_result"],
            "expected_calls": [
                _call(
                    "calculate_impacts",
                    {"system_id": "ps-bottle-001", "method_id": "im-traci-21"},
                ),
                _call(
                    "get_inventory_results",
                    {"result_id": SYMBOLIC_RESULT, "direction": "both"},
                ),
                _call("dispose_result", {"result_id": SYMBOLIC_RESULT}),
            ],
            "conditional_execution": True,
            "difficulty": "hard",
        },
        {
            "task_id": "olca-calc-contributions-dispose-001",
            "domain": "lca",
            "behavior": "multi_call",
            "user_request": (
                "Calculate impacts for system ps-bottle-001 using method im-traci-21, analyze the "
                "top five process contributors to category cat-climate, then dispose the result."
            ),
            "tools": ["calculate_impacts", "analyze_contributions", "dispose_result"],
            "expected_calls": [
                _call(
                    "calculate_impacts",
                    {"system_id": "ps-bottle-001", "method_id": "im-traci-21"},
                ),
                _call(
                    "analyze_contributions",
                    {
                        "result_id": SYMBOLIC_RESULT,
                        "impact_category_id": "cat-climate",
                        "n": 5,
                        "contribution_type": "process",
                    },
                ),
                _call("dispose_result", {"result_id": SYMBOLIC_RESULT}),
            ],
            "conditional_execution": True,
            "difficulty": "hard",
        },
        {
            "task_id": "olca-calculate-missing-system-001",
            "domain": "lca",
            "behavior": "clarify",
            "user_request": "Calculate environmental impacts using a method matching TRACI.",
            "tools": ["calculate_impacts", "search_impact_methods", "compare_systems"],
            "expected_calls": [],
            "missing_information": ["system_id or system_name"],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-contributions-missing-category-001",
            "domain": "lca",
            "behavior": "clarify",
            "user_request": "Show the main process contributors for result res-001.",
            "tools": ["analyze_contributions", "get_total_requirements", "get_inventory_results"],
            "expected_calls": [],
            "missing_information": ["impact_category_id"],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-write-abstain-001",
            "domain": "lca",
            "behavior": "abstain",
            "user_request": "Create a new product flow named Recycled PET flakes.",
            "tools": ["search_flows", "search_processes", "get_entity_by_name"],
            "expected_calls": [],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-email-abstain-001",
            "domain": "lca",
            "behavior": "abstain",
            "user_request": "Email the impact results to the plant manager.",
            "tools": ["calculate_impacts", "get_inventory_results", "dispose_result"],
            "expected_calls": [],
            "difficulty": "easy",
        },
    ]


def source_extension_specs() -> list[dict[str, Any]]:
    return [
        {
            "task_id": "olca-source-consistency-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": "Check calculation result res-001 for contribution consistency.",
            "tools": [
                "check_result_consistency",
                "analyze_contributions",
                "get_total_requirements",
            ],
            "expected_calls": [_call("check_result_consistency", {"result_id": "res-001"})],
            "difficulty": "easy",
        },
        {
            "task_id": "olca-source-consistency-tolerance-001",
            "domain": "lca",
            "behavior": "call",
            "user_request": (
                "Check result res-001 for contribution consistency using relative tolerance "
                "0.0001 and absolute tolerance 1e-10."
            ),
            "tools": ["check_result_consistency", "analyze_contributions"],
            "expected_calls": [
                _call(
                    "check_result_consistency",
                    {"result_id": "res-001", "rel_tol": 0.0001, "abs_tol": 1e-10},
                )
            ],
            "difficulty": "medium",
        },
        {
            "task_id": "olca-source-calc-consistency-dispose-001",
            "domain": "lca",
            "behavior": "multi_call",
            "user_request": (
                "Calculate impacts for ps-bottle-001 with im-traci-21, check the result for "
                "consistency, then dispose it."
            ),
            "tools": ["calculate_impacts", "check_result_consistency", "dispose_result"],
            "expected_calls": [
                _call(
                    "calculate_impacts",
                    {"system_id": "ps-bottle-001", "method_id": "im-traci-21"},
                ),
                _call("check_result_consistency", {"result_id": SYMBOLIC_RESULT}),
                _call("dispose_result", {"result_id": SYMBOLIC_RESULT}),
            ],
            "conditional_execution": True,
            "difficulty": "hard",
        },
    ]


def _render(
    specs: list[dict[str, Any]],
    manifest: dict[str, Any],
    manifest_id: str,
    schema_source: str,
) -> list[dict[str, Any]]:
    tools = _tool_map(manifest)
    output: list[dict[str, Any]] = []
    for spec in specs:
        required_tools = cast(list[str], spec["tools"])
        missing = [name for name in required_tools if name not in tools]
        if missing:
            raise ValueError(f"Manifest {manifest_id} lacks tools for {spec['task_id']}: {missing}")
        task = {
            "task_id": spec["task_id"],
            "domain": spec["domain"],
            "behavior": spec["behavior"],
            "user_request": spec["user_request"],
            "available_tools": [_benchmark_tool(tools[name]) for name in required_tools],
            "expected_calls": spec.get("expected_calls", []),
            "valid_alternatives": spec.get("valid_alternatives", []),
            "missing_information": spec.get("missing_information", []),
            "difficulty": spec["difficulty"],
            "provisional_schema": False,
            "conditional_execution": spec.get("conditional_execution", False),
            "tool_manifest_id": manifest_id,
            "tool_manifest_commit": manifest.get("source_commit"),
            "tool_schema_source": schema_source,
            "execution_mode": "schema_only_backend_unavailable",
        }
        output.append(task)
    return output


def _write_jsonl(path: Path, tasks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(task, separators=(",", ":"), ensure_ascii=False) for task in tasks)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _subset_manifest(
    manifest: dict[str, Any],
    names: list[str],
    manifest_id: str,
    schema_source: str,
) -> dict[str, Any]:
    tools = _tool_map(manifest)
    return {
        "manifest_id": manifest_id,
        "schema_source": schema_source,
        "source_commit": manifest.get("source_commit"),
        "connector_deployed_version": manifest.get("deployed_version"),
        "execution_status": manifest.get("execution_status"),
        "tool_count": len(names),
        "tool_names": names,
        "tools": [_benchmark_tool(tools[name]) for name in names],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("connector_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    source = _load(args.source_manifest)
    connector = _load(args.connector_manifest)
    common = common_specs()
    extension = source_extension_specs()

    source_tasks = _render(common, source, SOURCE_MANIFEST_ID, "fastmcp_generated_local_source")
    connector_tasks = _render(
        common,
        connector,
        CONNECTOR_MANIFEST_ID,
        "connector_visible_schema_capture",
    )
    extension_tasks = _render(
        extension,
        source,
        SOURCE_MANIFEST_ID,
        "fastmcp_generated_local_source",
    )

    tasks_dir = args.output_dir / "tasks"
    manifests_dir = args.output_dir / "manifests"
    _write_jsonl(tasks_dir / "domain_tool_calling_openlca_source_v0.jsonl", source_tasks)
    _write_jsonl(tasks_dir / "domain_tool_calling_openlca_connector_v0.jsonl", connector_tasks)
    _write_jsonl(
        tasks_dir / "domain_tool_calling_openlca_source_extension_v0.jsonl",
        extension_tasks,
    )

    common_names = sorted({name for spec in common for name in cast(list[str], spec["tools"])})
    extension_names = sorted(
        {name for spec in extension for name in cast(list[str], spec["tools"])}
    )
    manifests_dir.mkdir(parents=True, exist_ok=True)
    (manifests_dir / "openlca_mcp_source_readonly_subset_4865b2b.json").write_text(
        json.dumps(
            _subset_manifest(
                source,
                sorted(set(common_names) | set(extension_names)),
                SOURCE_MANIFEST_ID,
                "fastmcp_generated_local_source",
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (manifests_dir / "openlca_mcp_connector_readonly_subset_2026-07-26.json").write_text(
        json.dumps(
            _subset_manifest(
                connector,
                common_names,
                CONNECTOR_MANIFEST_ID,
                "connector_visible_schema_capture",
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        json.dumps(
            {
                "common_tasks_per_surface": len(common),
                "source_extension_tasks": len(extension),
                "source_common_output": str(
                    tasks_dir / "domain_tool_calling_openlca_source_v0.jsonl"
                ),
                "connector_common_output": str(
                    tasks_dir / "domain_tool_calling_openlca_connector_v0.jsonl"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

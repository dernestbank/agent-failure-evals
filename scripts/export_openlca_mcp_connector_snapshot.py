"""Write the OpenLCA-MCP connector-visible schema captured on 2026-07-26.

This snapshot is based on the tool schemas exposed to the active ChatGPT
conversation by ``api_tool.list_resources(paths=["openlca-mcp"])``. It is kept
separate from the local Git source manifest because the deployed connector and
local source demonstrably differ.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def parameter(
    name: str,
    schema: dict[str, Any],
    *,
    required: bool,
    default: Any | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "required": required, "schema": schema}
    if not required and default is not None:
        item["default"] = default
    return item


def risk(tool_name: str) -> tuple[str, str]:
    if tool_name.startswith("create_"):
        return "database_write", "Creates persistent entities in the openLCA database."
    if tool_name == "export_results":
        return "file_write", "Writes a result file on the server host."
    if tool_name.startswith("dispose_"):
        return "result_store_cleanup", "Deletes temporary calculation results from server memory."
    if tool_name in {"calculate_impacts", "run_monte_carlo", "run_scenario_analysis"}:
        return "read_only_stateful_compute", "Creates or computes temporary analysis state."
    return "read_only", "Queries data or reads existing calculation state."


def tool(
    name: str,
    description: str,
    parameters: list[dict[str, Any]],
) -> dict[str, Any]:
    risk_class, operational_effect = risk(name)
    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "risk_class": risk_class,
        "operational_effect": operational_effect,
        "risk_class_provenance": "inferred from connector description and local source semantics",
    }


STRING = {"type": "string"}
INTEGER = {"type": "integer"}
NUMBER = {"type": "number"}
BOOLEAN = {"type": "boolean"}
STRING_ARRAY = {"type": "array", "items": {"type": "string"}}
NUMBER_ARRAY = {"type": "array", "items": {"type": "number"}}
OBJECT = {"type": "object"}


def connector_tools() -> list[dict[str, Any]]:
    tools = [
        tool(
            "analyze_contributions",
            "Identify the largest process or flow contributors to an impact category.",
            [
                parameter("result_id", STRING, required=True),
                parameter("impact_category_id", STRING, required=True),
                parameter("n", INTEGER, required=False, default=10),
                parameter(
                    "contribution_type",
                    {"type": "string", "enum": ["process", "flow"]},
                    required=False,
                    default="process",
                ),
                parameter("min_share", NUMBER, required=False, default=0),
            ],
        ),
        tool(
            "calculate_impacts",
            "Calculate environmental impacts for a product system and return a result_id.",
            [
                parameter("system_id", STRING, required=False),
                parameter("system_name", STRING, required=False),
                parameter("method_id", STRING, required=False),
                parameter("method_keywords", STRING_ARRAY, required=False),
                parameter("amount", NUMBER, required=False, default=1),
            ],
        ),
        tool(
            "compare_systems",
            "Compare two product systems on the same impact method.",
            [
                parameter("system1_id", STRING, required=True),
                parameter("system2_id", STRING, required=True),
                parameter("method_id", STRING, required=False),
                parameter("method_keywords", STRING_ARRAY, required=False),
                parameter("amount", NUMBER, required=False, default=1),
            ],
        ),
        tool(
            "create_process",
            "Create a unit process with input and output exchanges.",
            [
                parameter("name", STRING, required=True),
                parameter("description", STRING, required=False),
                parameter(
                    "exchanges",
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "flow_id": STRING,
                                "amount": NUMBER,
                                "is_input": BOOLEAN,
                                "is_quantitative_reference": BOOLEAN,
                                "provider_id": STRING,
                            },
                            "required": ["flow_id", "amount", "is_input"],
                        },
                    },
                    required=True,
                ),
            ],
        ),
        tool(
            "create_product_flow",
            "Create a product flow using the Mass property and kg unit.",
            [
                parameter("name", STRING, required=True),
                parameter("description", STRING, required=False),
            ],
        ),
        tool(
            "create_product_system",
            "Create a product system from a root process.",
            [
                parameter("process_id", STRING, required=False),
                parameter("process_name", STRING, required=False),
            ],
        ),
        tool("dispose_all_results", "Dispose every tracked calculation result.", []),
        tool(
            "dispose_result",
            "Dispose one calculation result to free server memory.",
            [parameter("result_id", STRING, required=True)],
        ),
        tool(
            "export_results",
            "Export impact or comparison results to CSV or Excel on the server host.",
            [
                parameter("result_id", STRING, required=False),
                parameter("data", OBJECT, required=False),
                parameter(
                    "kind",
                    {"type": "string", "enum": ["impacts", "comparison"]},
                    required=False,
                    default="impacts",
                ),
                parameter("filepath", STRING, required=True),
                parameter(
                    "format",
                    {"type": "string", "enum": ["csv", "excel"]},
                    required=False,
                    default="csv",
                ),
            ],
        ),
        tool(
            "find_providers",
            "Find processes that produce a given flow.",
            [
                parameter("flow_id", STRING, required=False),
                parameter("flow_name", STRING, required=False),
            ],
        ),
        tool(
            "get_contribution_tree",
            "Build an upstream process contribution tree for an impact category.",
            [
                parameter("result_id", STRING, required=True),
                parameter("impact_category_id", STRING, required=True),
                parameter("max_depth", INTEGER, required=False, default=3),
                parameter("min_share", NUMBER, required=False, default=0.01),
            ],
        ),
        tool(
            "get_entity_by_name",
            "Look up one entity by exact name.",
            [
                parameter(
                    "model_type",
                    {
                        "type": "string",
                        "enum": [
                            "Flow",
                            "Process",
                            "ImpactMethod",
                            "ProductSystem",
                            "FlowProperty",
                            "Unit",
                        ],
                    },
                    required=True,
                ),
                parameter("name", STRING, required=True),
            ],
        ),
        tool(
            "get_inventory_results",
            "Get life-cycle inventory flows for a calculation result.",
            [
                parameter("result_id", STRING, required=True),
                parameter(
                    "direction",
                    {"type": "string", "enum": ["input", "output", "both"]},
                    required=False,
                    default="both",
                ),
            ],
        ),
        tool(
            "get_normalized_impacts",
            "Get normalized impact results for a calculation result.",
            [parameter("result_id", STRING, required=True)],
        ),
        tool(
            "get_sankey",
            "Get Sankey graph data for an impact category.",
            [
                parameter("result_id", STRING, required=True),
                parameter("impact_category_id", STRING, required=True),
                parameter("max_nodes", INTEGER, required=False, default=50),
                parameter("min_share", NUMBER, required=False, default=0),
            ],
        ),
        tool(
            "get_total_requirements",
            "Get scaled technology requirements for a calculated system.",
            [parameter("result_id", STRING, required=True)],
        ),
        tool(
            "get_weighted_impacts",
            "Get weighted impact results after normalization and weighting.",
            [parameter("result_id", STRING, required=True)],
        ),
        tool(
            "health_check",
            "Probe openLCA reachability and optionally count database entities.",
            [parameter("count_entities", BOOLEAN, required=False, default=True)],
        ),
        tool(
            "run_monte_carlo",
            "Run Monte Carlo uncertainty analysis for a product system.",
            [
                parameter("system_id", STRING, required=True),
                parameter("method_id", STRING, required=False),
                parameter("method_keywords", STRING_ARRAY, required=False),
                parameter("iterations", INTEGER, required=False, default=100),
            ],
        ),
        tool(
            "run_scenario_analysis",
            "Vary one parameter over multiple values and report impacts.",
            [
                parameter("system_id", STRING, required=True),
                parameter("method_id", STRING, required=False),
                parameter("method_keywords", STRING_ARRAY, required=False),
                parameter("parameter_name", STRING, required=True),
                parameter("values", NUMBER_ARRAY, required=True),
            ],
        ),
        tool(
            "search_flows",
            "Search material flows using case-insensitive partial keyword matching.",
            [
                parameter("keywords", STRING_ARRAY, required=True),
                parameter("max_results", INTEGER, required=False, default=10),
                parameter(
                    "flow_type",
                    {
                        "type": "string",
                        "enum": ["PRODUCT_FLOW", "ELEMENTARY_FLOW", "WASTE_FLOW"],
                    },
                    required=False,
                ),
            ],
        ),
        tool(
            "search_impact_methods",
            "Search LCIA methods and return impact categories.",
            [parameter("keywords", STRING_ARRAY, required=True)],
        ),
        tool(
            "search_processes",
            "Search processes using case-insensitive partial keyword matching.",
            [
                parameter("keywords", STRING_ARRAY, required=True),
                parameter("max_results", INTEGER, required=False, default=10),
            ],
        ),
        tool("test_connection", "Test the openLCA IPC connection.", []),
    ]
    return sorted(tools, key=lambda item: str(item["name"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tools = connector_tools()
    manifest: dict[str, Any] = {
        "manifest_schema_version": "1.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "manifest_kind": "openlca_mcp_connector_visible",
        "connector_name": "openlca-mcp",
        "endpoint": "https://openlca-ipc-mcp.orchville.com/mcp",
        "capture_provenance": (
            "Tool schemas exposed to the active ChatGPT conversation by "
            "api_tool.list_resources(paths=['openlca-mcp']) on 2026-07-26."
        ),
        "direct_tools_list_fetch": "not_performed_due_execution_safety_boundary",
        "deployed_version": None,
        "tool_count": len(tools),
        "tool_names": [item["name"] for item in tools],
        "tools": tools,
        "execution_status": {
            "health_probe": "failed",
            "health_probe_error": "HTTP 502 upstream or external service error",
            "schema_available": True,
            "live_openlca_execution": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output), "tool_count": len(tools)}, indent=2))


if __name__ == "__main__":
    main()

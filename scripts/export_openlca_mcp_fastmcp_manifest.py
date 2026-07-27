"""Export actual FastMCP-generated OpenLCA-MCP tool schemas.

Run this script with the Python environment of the OpenLCA-MCP source checkout
and with that checkout as the current working directory. Importing the server
registers tools but does not contact the openLCA IPC backend.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import platform
import subprocess
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8").strip()


def _runtime_version() -> str | None:
    package = importlib.import_module("src")
    value = getattr(package, "__version__", None)
    return None if value is None else str(value)


def _risk(name: str, read_only: bool | None) -> tuple[str, str]:
    if read_only:
        if name in {"calculate_impacts", "run_monte_carlo", "run_scenario_analysis"}:
            return "read_only_stateful_compute", "Creates or computes temporary analysis state."
        return "read_only", "Queries data or reads existing calculation state."
    if name.startswith("create_"):
        return "database_write", "Creates persistent entities in the openLCA database."
    if name == "export_results":
        return "file_write", "Writes a result file on the server host."
    if name.startswith("dispose_"):
        return "result_store_cleanup", "Deletes temporary calculation results from server memory."
    return "write_or_mutation", "Registered as a write-capable MCP tool."


def _parameter_rows(schema: dict[str, Any]) -> list[dict[str, Any]]:
    properties = cast(dict[str, dict[str, Any]], schema.get("properties", {}))
    required = set(cast(list[str], schema.get("required", [])))
    rows: list[dict[str, Any]] = []
    for name, property_schema in properties.items():
        row: dict[str, Any] = {
            "name": name,
            "required": name in required,
            "schema": property_schema,
        }
        if "default" in property_schema:
            row["default"] = property_schema["default"]
        rows.append(row)
    return rows


async def export(output: Path) -> dict[str, Any]:
    app_module = importlib.import_module("src.app")
    mcp = cast(Any, app_module).mcp
    fastmcp_tools = await mcp.list_tools()
    tools: list[dict[str, Any]] = []
    for item in fastmcp_tools:
        annotations = item.annotations
        read_only = getattr(annotations, "readOnlyHint", None) if annotations else None
        risk_class, operational_effect = _risk(item.name, read_only)
        annotation_dict = (
            {
                "title": getattr(annotations, "title", None),
                "readOnlyHint": read_only,
                "destructiveHint": getattr(annotations, "destructiveHint", None),
                "idempotentHint": getattr(annotations, "idempotentHint", None),
                "openWorldHint": getattr(annotations, "openWorldHint", None),
            }
            if annotations
            else None
        )
        parameters = cast(dict[str, Any], item.parameters)
        output_schema = cast(dict[str, Any] | None, item.output_schema)
        tools.append(
            {
                "name": item.name,
                "title": item.title,
                "description": item.description,
                "version": item.version,
                "parameters": _parameter_rows(parameters),
                "input_schema": parameters,
                "output_schema": output_schema,
                "annotations": annotation_dict,
                "risk_class": risk_class,
                "operational_effect": operational_effect,
                "source_function": getattr(item.fn, "__qualname__", None),
                "source_module": getattr(item.fn, "__module__", None),
            }
        )

    tools.sort(key=lambda tool: str(tool["name"]))
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_version = str(pyproject["project"]["version"])
    runtime_version = _runtime_version()
    manifest: dict[str, Any] = {
        "manifest_schema_version": "1.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "manifest_kind": "openlca_mcp_fastmcp_generated_source",
        "capture_python_version": platform.python_version(),
        "source_repository": "https://github.com/SDAI-institute/openlca-mcp",
        "source_commit": _git("rev-parse", "HEAD"),
        "source_commit_short": _git("rev-parse", "--short", "HEAD"),
        "source_commit_time": _git("show", "-s", "--format=%cI", "HEAD"),
        "source_commit_subject": _git("show", "-s", "--format=%s", "HEAD"),
        "package_version_pyproject": package_version,
        "runtime_version_module": runtime_version,
        "version_consistent": package_version == runtime_version,
        "tool_count": len(tools),
        "tool_names": [tool["name"] for tool in tools],
        "tools": tools,
        "execution_status": {
            "manifest_export": "FastMCP registration imported locally",
            "openlca_ipc_contacted": False,
            "live_openlca_execution": "not_tested_by_exporter",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: export_openlca_mcp_fastmcp_manifest.py OUTPUT.json")
    output = Path(sys.argv[1]).resolve()
    manifest = asyncio.run(export(output))
    print(
        json.dumps(
            {
                "output": str(output),
                "tool_count": manifest["tool_count"],
                "source_commit": manifest["source_commit_short"],
                "version_consistent": manifest["version_consistent"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

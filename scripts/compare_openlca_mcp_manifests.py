"""Compare local FastMCP-generated and connector-visible OpenLCA-MCP manifests."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast


def _load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _tool_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(tool["name"]): cast(dict[str, Any], tool) for tool in manifest["tools"]}


def _parameter_map(
    tool: dict[str, Any], *, hide_connection: bool = False
) -> dict[str, dict[str, Any]]:
    rows = cast(list[dict[str, Any]], tool.get("parameters", []))
    return {
        str(row["name"]): row
        for row in rows
        if not (hide_connection and row["name"] == "connection")
    }


def _normalize_schema(value: Any) -> Any:
    if isinstance(value, dict):
        schema = {
            key: _normalize_schema(item)
            for key, item in value.items()
            if key not in {"title", "default"}
        }
        any_of = schema.get("anyOf")
        if isinstance(any_of, list):
            non_null = [item for item in any_of if item != {"type": "null"}]
            if len(non_null) == 1 and len(any_of) == 2:
                return non_null[0]
        return schema
    if isinstance(value, list):
        return [_normalize_schema(item) for item in value]
    return value


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _default_status(source: dict[str, Any], connector: dict[str, Any]) -> str | None:
    source_has = "default" in source
    connector_has = "default" in connector
    source_value = source.get("default")
    connector_value = connector.get("default")
    if source_has and connector_has and source_value != connector_value:
        return f"source={source_value!r}; connector={connector_value!r}"
    if source_has and not connector_has and source_value is not None:
        return f"source={source_value!r}; connector=unspecified"
    if connector_has and not source_has and connector_value is not None:
        return f"source=unspecified; connector={connector_value!r}"
    return None


def compare(
    source_manifest: dict[str, Any],
    connector_manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_tools = _tool_map(source_manifest)
    connector_tools = _tool_map(connector_manifest)
    names = sorted(set(source_tools) | set(connector_tools))
    rows: list[dict[str, Any]] = []

    for name in names:
        source_tool = source_tools.get(name)
        connector_tool = connector_tools.get(name)
        if source_tool is None:
            rows.append(
                {
                    "tool_name": name,
                    "status": "connector_only",
                    "source_risk": "",
                    "connector_risk": connector_tool.get("risk_class", "")
                    if connector_tool
                    else "",
                    "source_parameter_count_raw": 0,
                    "source_parameter_count_client_visible": 0,
                    "connector_parameter_count": len(_parameter_map(connector_tool or {})),
                    "hidden_source_parameters": "",
                    "source_only_client_parameters": "",
                    "connector_only_parameters": ";".join(
                        sorted(_parameter_map(connector_tool or {}))
                    ),
                    "requiredness_drift": "",
                    "default_drift": "",
                    "schema_constraint_drift": "",
                    "risk_drift": "",
                }
            )
            continue
        if connector_tool is None:
            raw_source = _parameter_map(source_tool)
            visible_source = _parameter_map(source_tool, hide_connection=True)
            rows.append(
                {
                    "tool_name": name,
                    "status": "source_only",
                    "source_risk": source_tool.get("risk_class", ""),
                    "connector_risk": "",
                    "source_parameter_count_raw": len(raw_source),
                    "source_parameter_count_client_visible": len(visible_source),
                    "connector_parameter_count": 0,
                    "hidden_source_parameters": "connection" if "connection" in raw_source else "",
                    "source_only_client_parameters": ";".join(sorted(visible_source)),
                    "connector_only_parameters": "",
                    "requiredness_drift": "",
                    "default_drift": "",
                    "schema_constraint_drift": "",
                    "risk_drift": "",
                }
            )
            continue

        source_raw = _parameter_map(source_tool)
        source_visible = _parameter_map(source_tool, hide_connection=True)
        connector_parameters = _parameter_map(connector_tool)
        source_only = sorted(set(source_visible) - set(connector_parameters))
        connector_only = sorted(set(connector_parameters) - set(source_visible))
        common = sorted(set(source_visible) & set(connector_parameters))
        required_drift: list[str] = []
        default_drift: list[str] = []
        schema_drift: list[str] = []
        for parameter_name in common:
            source_parameter = source_visible[parameter_name]
            connector_parameter = connector_parameters[parameter_name]
            if bool(source_parameter.get("required")) != bool(connector_parameter.get("required")):
                required_drift.append(
                    f"{parameter_name}:source={source_parameter.get('required')};"
                    f"connector={connector_parameter.get('required')}"
                )
            default_difference = _default_status(source_parameter, connector_parameter)
            if default_difference:
                default_drift.append(f"{parameter_name}:{default_difference}")
            source_schema = _normalize_schema(source_parameter.get("schema", {}))
            connector_schema = _normalize_schema(connector_parameter.get("schema", {}))
            if source_schema != connector_schema:
                schema_drift.append(
                    f"{parameter_name}:source={_json(source_schema)};connector={_json(connector_schema)}"
                )

        status = "shared_no_client_surface_drift"
        if source_only or connector_only or required_drift or default_drift or schema_drift:
            status = "shared_interface_drift"
        source_risk = str(source_tool.get("risk_class", ""))
        connector_risk = str(connector_tool.get("risk_class", ""))
        rows.append(
            {
                "tool_name": name,
                "status": status,
                "source_risk": source_risk,
                "connector_risk": connector_risk,
                "source_parameter_count_raw": len(source_raw),
                "source_parameter_count_client_visible": len(source_visible),
                "connector_parameter_count": len(connector_parameters),
                "hidden_source_parameters": "connection" if "connection" in source_raw else "",
                "source_only_client_parameters": ";".join(source_only),
                "connector_only_parameters": ";".join(connector_only),
                "requiredness_drift": " | ".join(required_drift),
                "default_drift": " | ".join(default_drift),
                "schema_constraint_drift": " | ".join(schema_drift),
                "risk_drift": ""
                if source_risk == connector_risk
                else f"{source_risk}->{connector_risk}",
            }
        )

    counts = Counter(str(row["status"]) for row in rows)
    hidden_routing_tools = sum(bool(row["hidden_source_parameters"]) for row in rows)
    schema_drift_tools = sum(bool(row["schema_constraint_drift"]) for row in rows)
    parameter_name_drift_tools = sum(
        row["status"] == "shared_interface_drift"
        and bool(row["source_only_client_parameters"] or row["connector_only_parameters"])
        for row in rows
    )
    summary: dict[str, Any] = {
        "source_tool_count": source_manifest["tool_count"],
        "connector_tool_count": connector_manifest["tool_count"],
        "shared_tool_count": len(set(source_tools) & set(connector_tools)),
        "source_only_tools": sorted(set(source_tools) - set(connector_tools)),
        "connector_only_tools": sorted(set(connector_tools) - set(source_tools)),
        "status_counts": dict(counts),
        "tools_with_hidden_connection_parameter": hidden_routing_tools,
        "tools_with_client_parameter_name_drift": parameter_name_drift_tools,
        "tools_with_schema_constraint_drift": schema_drift_tools,
        "source_package_version_pyproject": source_manifest.get("package_version_pyproject"),
        "source_runtime_version_module": source_manifest.get("runtime_version_module"),
        "source_version_consistent": source_manifest.get("version_consistent"),
        "source_commit": source_manifest.get("source_commit"),
        "connector_deployed_version": connector_manifest.get("deployed_version"),
        "connector_health": connector_manifest.get("execution_status", {}),
    }
    return rows, summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _markdown(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    source_only = summary["source_only_tools"] or ["none"]
    connector_only = summary["connector_only_tools"] or ["none"]
    drift_rows = [row for row in rows if row["status"] != "shared_no_client_surface_drift"]
    lines = [
        "# OpenLCA-MCP Source-to-Connector Schema Drift",
        "",
        "## Snapshot identity",
        "",
        f"- Local source commit: `{str(summary['source_commit'])[:7]}`",
        f"- Local package version from `pyproject.toml`: `{summary['source_package_version_pyproject']}`",
        f"- Local runtime version from `src.__version__`: `{summary['source_runtime_version_module']}`",
        f"- Local version metadata consistent: **{summary['source_version_consistent']}**",
        "- Connector-visible deployed version: **unknown**",
        "- Connector schema provenance: ChatGPT connector tool schema capture on 2026-07-26",
        "- Connector health probe: **failed with HTTP 502 upstream/external-service error**",
        "",
        "## Inventory",
        "",
        f"- Local FastMCP-generated tools: **{summary['source_tool_count']}**",
        f"- Connector-visible tools: **{summary['connector_tool_count']}**",
        f"- Shared names: **{summary['shared_tool_count']}**",
        f"- Source-only tools: `{', '.join(source_only)}`",
        f"- Connector-only tools: `{', '.join(connector_only)}`",
        f"- Source tools with internal `connection` routing parameter: **{summary['tools_with_hidden_connection_parameter']}**",
        f"- Shared tools with client-visible parameter-name drift: **{summary['tools_with_client_parameter_name_drift']}**",
        f"- Tools with schema/constraint drift: **{summary['tools_with_schema_constraint_drift']}**",
        "",
        "## Drift summary",
        "",
        "| Tool | Status | Source-only client params | Connector-only params | Constraint/default drift |",
        "|---|---|---|---|---|",
    ]
    for row in drift_rows:
        details = "<br>".join(
            part
            for part in [
                str(row["requiredness_drift"]),
                str(row["default_drift"]),
                str(row["schema_constraint_drift"]),
            ]
            if part
        )
        if len(details) > 500:
            details = details[:497] + "..."
        lines.append(
            f"| `{row['tool_name']}` | {row['status']} | "
            f"{row['source_only_client_parameters'] or 'none'} | "
            f"{row['connector_only_parameters'] or 'none'} | {details or 'none'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. The local source is ahead of the connector-visible surface: it adds `check_result_consistency` and additional `create_product_system` options.",
            "2. The connector hides the local `connection` routing parameter from the user-visible tool surface.",
            "3. Several connector schemas expose stricter enums or nested exchange fields than the local Python annotations generate, indicating deployed-version drift or schema-generation differences.",
            "4. Local version metadata is internally inconsistent (`0.4.1` package metadata versus `0.4.0` runtime constant).",
            "5. Live behavior could not be compared because the connector health probe returned HTTP 502.",
            "6. The source and connector manifests remain separate artifacts and are not silently merged.",
            "",
            "These findings describe interface drift, not functional correctness or deployment safety.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("connector_manifest", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_md", type=Path)
    parser.add_argument("output_summary", type=Path)
    args = parser.parse_args()

    source_manifest = _load(args.source_manifest)
    connector_manifest = _load(args.connector_manifest)
    rows, summary = compare(source_manifest, connector_manifest)
    for path in [args.output_csv, args.output_md, args.output_summary]:
        path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_csv, rows)
    args.output_md.write_text(_markdown(rows, summary), encoding="utf-8", newline="\n")
    args.output_summary.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

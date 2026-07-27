"""Build a before/after report for OpenLCA-MCP schema hardening."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, cast


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["tool_name"]: row for row in csv.DictReader(handle)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before_summary", type=Path)
    parser.add_argument("before_csv", type=Path)
    parser.add_argument("after_summary", type=Path)
    parser.add_argument("after_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_md", type=Path)
    args = parser.parse_args()

    before = load_json(args.before_summary)
    after = load_json(args.after_summary)
    before_rows = load_rows(args.before_csv)
    after_rows = load_rows(args.after_csv)

    tool_names = sorted(set(before_rows) | set(after_rows))
    rows: list[dict[str, Any]] = []
    for name in tool_names:
        before_row = before_rows[name]
        after_row = after_rows[name]
        before_drift = before_row["status"] != "shared_no_client_surface_drift"
        after_drift = after_row["status"] != "shared_no_client_surface_drift"
        if before_drift and not after_drift:
            change = "resolved"
        elif not before_drift and after_drift:
            change = "introduced"
        elif before_drift and after_drift:
            change = "remaining"
        else:
            change = "unchanged_no_drift"
        rows.append(
            {
                "tool_name": name,
                "change": change,
                "before_status": before_row["status"],
                "after_status": after_row["status"],
                "before_schema_drift": before_row["schema_constraint_drift"],
                "after_schema_drift": after_row["schema_constraint_drift"],
                "before_source_only_parameters": before_row["source_only_client_parameters"],
                "after_source_only_parameters": after_row["source_only_client_parameters"],
            }
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    resolved = [row["tool_name"] for row in rows if row["change"] == "resolved"]
    remaining = [row["tool_name"] for row in rows if row["change"] == "remaining"]
    introduced = [row["tool_name"] for row in rows if row["change"] == "introduced"]
    metrics = [
        {
            "metric": "source version metadata consistent",
            "before": before["source_version_consistent"],
            "after": after["source_version_consistent"],
        },
        {
            "metric": "shared tools with interface drift",
            "before": before["status_counts"].get("shared_interface_drift", 0),
            "after": after["status_counts"].get("shared_interface_drift", 0),
        },
        {
            "metric": "tools with schema-constraint drift",
            "before": before["tools_with_schema_constraint_drift"],
            "after": after["tools_with_schema_constraint_drift"],
        },
        {
            "metric": "shared tools with parameter-name drift",
            "before": before["tools_with_client_parameter_name_drift"],
            "after": after["tools_with_client_parameter_name_drift"],
        },
        {
            "metric": "source-only tools",
            "before": len(before["source_only_tools"]),
            "after": len(after["source_only_tools"]),
        },
    ]

    lines = [
        "# OpenLCA-MCP Schema Hardening Delta",
        "",
        f"- Before source commit: `{str(before['source_commit'])[:7]}`",
        f"- After source commit: `{str(after['source_commit'])[:7]}`",
        "- Deployed connector snapshot: connector-visible capture from 2026-07-26",
        "- Live backend status: unavailable; connector health probe returned HTTP 502",
        "",
        "## Metric changes",
        "",
        "| Metric | Before | After |",
        "|---|---:|---:|",
    ]
    for metric in metrics:
        lines.append(f"| {metric['metric']} | {metric['before']} | {metric['after']} |")

    lines.extend(
        [
            "",
            "## Tool-level changes",
            "",
            f"- Resolved drift: `{', '.join(resolved) or 'none'}`",
            f"- Remaining drift: `{', '.join(remaining) or 'none'}`",
            f"- Introduced drift: `{', '.join(introduced) or 'none'}`",
            "",
            "| Tool | Change | Before | After |",
            "|---|---|---|---|",
        ]
    )
    for row in rows:
        if row["change"] == "unchanged_no_drift":
            continue
        lines.append(
            f"| `{row['tool_name']}` | {row['change']} | "
            f"{row['before_status']} | {row['after_status']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The hardening branch aligns runtime and package versions at 0.4.1.",
            "- Literal annotations resolved enum drift for contribution type, entity type, inventory direction, and flow type.",
            "- A typed Pydantic exchange model made process-exchange inputs explicit and closed.",
            "- Remaining drift is intentional or deployment-related: source-only consistency tooling, expanded product-system options, description defaults, and generic comparison-data objects.",
            "- No deployed connector or live backend was changed by this branch.",
            "",
            "These results measure schema contracts only, not live functional correctness.",
        ]
    )
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "resolved_tools": resolved,
                "remaining_tools": remaining,
                "introduced_tools": introduced,
                "before_schema_drift_tools": before["tools_with_schema_constraint_drift"],
                "after_schema_drift_tools": after["tools_with_schema_constraint_drift"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

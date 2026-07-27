"""Build the OpenLCA-MCP benchmark pinned to hardened source commit b316008."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_openlca_mcp_versioned_benchmarks import (
    _load,
    _render,
    _subset_manifest,
    _write_jsonl,
    common_specs,
)

MANIFEST_ID = "openlca-mcp-source-b316008"
COMMIT = "b31600823cdcfc8509b9f66b889997c1d97965cd"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    manifest = _load(args.source_manifest)
    if manifest.get("source_commit") != COMMIT:
        raise ValueError(
            f"Expected hardened source commit {COMMIT}, got {manifest.get('source_commit')}"
        )

    specs = common_specs()
    tasks = _render(
        specs,
        manifest,
        MANIFEST_ID,
        "fastmcp_generated_hardened_source",
    )
    task_path = args.output_dir / "tasks" / "domain_tool_calling_openlca_source_b316008_v0.jsonl"
    _write_jsonl(task_path, tasks)

    tool_names = sorted({name for spec in specs for name in spec["tools"]})
    subset = _subset_manifest(
        manifest,
        tool_names,
        MANIFEST_ID,
        "fastmcp_generated_hardened_source",
    )
    subset_path = args.output_dir / "manifests" / "openlca_mcp_source_readonly_subset_b316008.json"
    subset_path.parent.mkdir(parents=True, exist_ok=True)
    subset_path.write_text(
        json.dumps(subset, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        json.dumps(
            {
                "task_count": len(tasks),
                "task_path": str(task_path),
                "subset_manifest_path": str(subset_path),
                "source_commit": COMMIT,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

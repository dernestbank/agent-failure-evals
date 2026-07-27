"""Export a versioned OpenLCA-MCP tool manifest from local Python source.

The exporter parses ``@ro_tool`` and ``@write_tool`` decorated async functions
without importing the server or contacting openLCA. It records exact source
commit metadata, input parameters, defaults, and operational risk categories.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


def _run_git(source_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(source_root), *args],
        text=True,
        encoding="utf-8",
    ).strip()


def _annotation_schema(node: ast.expr | None) -> dict[str, Any]:
    if node is None:
        return {}
    if isinstance(node, ast.Name):
        mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "Any": {},
        }
        return dict(mapping.get(node.id, {"python_annotation": node.id}))
    if isinstance(node, ast.Constant) and node.value is None:
        return {"type": "null"}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = _annotation_schema(node.left)
        right = _annotation_schema(node.right)
        return {"anyOf": [left, right]}
    if isinstance(node, ast.Subscript):
        base = node.value.id if isinstance(node.value, ast.Name) else ast.unparse(node.value)
        if base in {"Optional", "typing.Optional"}:
            return {"anyOf": [_annotation_schema(node.slice), {"type": "null"}]}
        if base in {"list", "List", "typing.List"}:
            return {"type": "array", "items": _annotation_schema(node.slice)}
        if base in {"dict", "Dict", "typing.Dict"}:
            if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                return {
                    "type": "object",
                    "additionalProperties": _annotation_schema(node.slice.elts[1]),
                }
            return {"type": "object"}
        if base in {"Literal", "typing.Literal"}:
            values: list[Any] = []
            elements = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            for element in elements:
                try:
                    values.append(ast.literal_eval(element))
                except (ValueError, TypeError):
                    values.append(ast.unparse(element))
            return {"enum": values}
        return {"python_annotation": ast.unparse(node)}
    return {"python_annotation": ast.unparse(node)}


def _default_value(node: ast.expr | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return ast.unparse(node)


def _decorator_info(node: ast.AsyncFunctionDef) -> tuple[str, str, str] | None:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        name = decorator.func.id if isinstance(decorator.func, ast.Name) else None
        if name not in {"ro_tool", "write_tool"} or not decorator.args:
            continue
        try:
            tool_name = cast(str, ast.literal_eval(decorator.args[0]))
        except (ValueError, TypeError):
            continue
        description = ""
        if len(decorator.args) >= 2:
            try:
                description = cast(str, ast.literal_eval(decorator.args[1]))
            except (ValueError, TypeError):
                description = ast.unparse(decorator.args[1])
        return tool_name, description, name
    return None


def _risk(tool_name: str, decorator_name: str) -> tuple[str, str]:
    if decorator_name == "ro_tool":
        if tool_name in {"calculate_impacts", "run_monte_carlo", "run_scenario_analysis"}:
            return "read_only_stateful_compute", "Creates or computes temporary analysis state."
        return "read_only", "Queries data or reads existing calculation state."
    if tool_name.startswith("create_"):
        return "database_write", "Creates persistent entities in the openLCA database."
    if tool_name == "export_results":
        return "file_write", "Writes a result file on the server host."
    if tool_name.startswith("dispose_"):
        return "result_store_cleanup", "Deletes temporary calculation results from server memory."
    return "write_or_mutation", "Registered as a write-capable MCP tool."


def _parameters(node: ast.AsyncFunctionDef) -> list[dict[str, Any]]:
    positional = [*node.args.posonlyargs, *node.args.args]
    positional_defaults: list[ast.expr | None] = [None] * (
        len(positional) - len(node.args.defaults)
    ) + list(node.args.defaults)
    parameters: list[dict[str, Any]] = []

    for argument, default_node in zip(positional, positional_defaults, strict=True):
        schema = _annotation_schema(argument.annotation)
        item: dict[str, Any] = {
            "name": argument.arg,
            "required": default_node is None,
            "schema": schema,
        }
        if default_node is not None:
            item["default"] = _default_value(default_node)
        parameters.append(item)

    for argument, default_node in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
        strict=True,
    ):
        item = {
            "name": argument.arg,
            "required": default_node is None,
            "schema": _annotation_schema(argument.annotation),
        }
        if default_node is not None:
            item["default"] = _default_value(default_node)
        parameters.append(item)
    return parameters


def _version_metadata(source_root: Path) -> dict[str, Any]:
    pyproject = tomllib.loads((source_root / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = str(pyproject["project"]["version"])
    init_tree = ast.parse((source_root / "src" / "__init__.py").read_text(encoding="utf-8"))
    runtime_version: str | None = None
    for node in init_tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        ):
            runtime_version = cast(str, ast.literal_eval(node.value))
    return {
        "package_version_pyproject": package_version,
        "runtime_version_module": runtime_version,
        "version_consistent": runtime_version == package_version,
    }


def export_manifest(source_root: Path, output: Path) -> dict[str, Any]:
    source_files = [
        source_root / "src" / "app.py",
        *sorted((source_root / "src" / "tools").glob("*.py")),
    ]
    tools: list[dict[str, Any]] = []
    for source_file in source_files:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in tree.body:
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            decorator = _decorator_info(node)
            if decorator is None:
                continue
            tool_name, description, decorator_name = decorator
            risk, effect = _risk(tool_name, decorator_name)
            tools.append(
                {
                    "name": tool_name,
                    "description": description,
                    "source_file": source_file.relative_to(source_root).as_posix(),
                    "source_function": node.name,
                    "registration": decorator_name,
                    "read_only": decorator_name == "ro_tool",
                    "risk_class": risk,
                    "operational_effect": effect,
                    "parameters": _parameters(node),
                }
            )

    tools.sort(key=lambda item: str(item["name"]))
    commit = _run_git(source_root, "rev-parse", "HEAD")
    commit_short = _run_git(source_root, "rev-parse", "--short", "HEAD")
    commit_time = _run_git(source_root, "show", "-s", "--format=%cI", "HEAD")
    commit_subject = _run_git(source_root, "show", "-s", "--format=%s", "HEAD")
    manifest: dict[str, Any] = {
        "manifest_schema_version": "1.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "manifest_kind": "openlca_mcp_local_source",
        "source_repository": "https://github.com/SDAI-institute/openlca-mcp",
        "source_commit": commit,
        "source_commit_short": commit_short,
        "source_commit_time": commit_time,
        "source_commit_subject": commit_subject,
        **_version_metadata(source_root),
        "tool_count": len(tools),
        "tool_names": [tool["name"] for tool in tools],
        "tools": tools,
        "execution_status": {
            "manifest_export": "source_only_no_server_import",
            "live_openlca_execution": "not_tested_by_exporter",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = export_manifest(args.source_root.resolve(), args.output.resolve())
    print(
        json.dumps(
            {
                "output": str(args.output),
                "source_commit": manifest["source_commit_short"],
                "tool_count": manifest["tool_count"],
                "version_consistent": manifest["version_consistent"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

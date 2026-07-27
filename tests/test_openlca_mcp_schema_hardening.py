import csv
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
BEFORE_MANIFEST = ROOT / "manifests" / "openlca_mcp_fastmcp_source_4865b2b.json"
AFTER_MANIFEST = ROOT / "manifests" / "openlca_mcp_fastmcp_source_b316008.json"
BEFORE_SUMMARY = ROOT / "manifests" / "openlca_mcp_schema_drift_summary.json"
AFTER_SUMMARY = ROOT / "manifests" / "openlca_mcp_schema_drift_hardened_summary.json"
DELTA = ROOT / "results" / "public" / "openlca_mcp_schema_hardening_delta.csv"


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def tool(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    return next(cast(dict[str, Any], item) for item in manifest["tools"] if item["name"] == name)


def property_schema(
    manifest: dict[str, Any],
    tool_name: str,
    property_name: str,
) -> dict[str, Any]:
    input_schema = cast(dict[str, Any], tool(manifest, tool_name)["input_schema"])
    properties = cast(dict[str, dict[str, Any]], input_schema["properties"])
    return properties[property_name]


def non_null(schema: dict[str, Any]) -> dict[str, Any]:
    if "anyOf" not in schema:
        return schema
    candidates = [candidate for candidate in schema["anyOf"] if candidate != {"type": "null"}]
    assert len(candidates) == 1
    return cast(dict[str, Any], candidates[0])


def test_hardened_manifest_is_pinned_and_version_consistent() -> None:
    before = load(BEFORE_MANIFEST)
    after = load(AFTER_MANIFEST)

    assert before["source_commit_short"] == "4865b2b"
    assert before["version_consistent"] is False
    assert before["runtime_version_module"] == "0.4.0"

    assert after["source_commit_short"] == "b316008"
    assert after["source_commit"] == "b31600823cdcfc8509b9f66b889997c1d97965cd"
    assert after["package_version_pyproject"] == "0.4.1"
    assert after["runtime_version_module"] == "0.4.1"
    assert after["version_consistent"] is True
    assert after["tool_count"] == 25


def test_hardened_generated_enums_and_ranges_are_present() -> None:
    after = load(AFTER_MANIFEST)

    assert property_schema(after, "analyze_contributions", "contribution_type")["enum"] == [
        "process",
        "flow",
    ]
    assert property_schema(after, "get_entity_by_name", "model_type")["enum"] == [
        "Flow",
        "Process",
        "ImpactMethod",
        "ProductSystem",
        "FlowProperty",
        "Unit",
    ]
    assert property_schema(after, "get_inventory_results", "direction")["enum"] == [
        "input",
        "output",
        "both",
    ]
    assert non_null(property_schema(after, "search_flows", "flow_type"))["enum"] == [
        "PRODUCT_FLOW",
        "ELEMENTARY_FLOW",
        "WASTE_FLOW",
    ]
    assert property_schema(after, "export_results", "kind")["enum"] == [
        "impacts",
        "comparison",
    ]
    assert property_schema(after, "export_results", "format")["enum"] == ["csv", "excel"]

    cutoff = non_null(property_schema(after, "create_product_system", "cutoff"))
    assert cutoff["minimum"] == 0.0
    assert cutoff["maximum"] == 1.0


def test_hardened_process_exchange_schema_is_explicit_and_closed() -> None:
    after = load(AFTER_MANIFEST)
    exchange = property_schema(after, "create_process", "exchanges")["items"]

    assert exchange["additionalProperties"] is False
    assert exchange["required"] == ["flow_id", "amount", "is_input"]
    assert set(exchange["properties"]) == {
        "flow_id",
        "amount",
        "is_input",
        "is_quantitative_reference",
        "provider_id",
        "formula",
        "unit_id",
        "flow_property_id",
    }


def test_hardening_reduces_drift_without_introducing_new_drift() -> None:
    before = load(BEFORE_SUMMARY)
    after = load(AFTER_SUMMARY)

    assert before["status_counts"]["shared_interface_drift"] == 8
    assert after["status_counts"]["shared_interface_drift"] == 4
    assert before["tools_with_schema_constraint_drift"] == 6
    assert after["tools_with_schema_constraint_drift"] == 2
    assert before["tools_with_client_parameter_name_drift"] == 1
    assert after["tools_with_client_parameter_name_drift"] == 1
    assert before["source_only_tools"] == after["source_only_tools"] == ["check_result_consistency"]

    with DELTA.open(encoding="utf-8", newline="") as handle:
        rows = {row["tool_name"]: row for row in csv.DictReader(handle)}

    assert {name for name, row in rows.items() if row["change"] == "resolved"} == {
        "analyze_contributions",
        "get_entity_by_name",
        "get_inventory_results",
        "search_flows",
    }
    assert not {name for name, row in rows.items() if row["change"] == "introduced"}


def test_remaining_drift_is_explicit() -> None:
    with DELTA.open(encoding="utf-8", newline="") as handle:
        rows = {row["tool_name"]: row for row in csv.DictReader(handle)}

    assert {name for name, row in rows.items() if row["change"] == "remaining"} == {
        "check_result_consistency",
        "create_process",
        "create_product_flow",
        "create_product_system",
        "export_results",
    }

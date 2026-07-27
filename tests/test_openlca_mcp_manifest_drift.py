import csv
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manifests" / "openlca_mcp_fastmcp_source_4865b2b.json"
CONNECTOR = ROOT / "manifests" / "openlca_mcp_connector_visible_2026-07-26.json"
SUMMARY = ROOT / "manifests" / "openlca_mcp_schema_drift_summary.json"
DRIFT_CSV = ROOT / "results" / "public" / "openlca_mcp_schema_drift.csv"


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_pinned_openlca_manifests_have_expected_identity() -> None:
    source = load(SOURCE)
    connector = load(CONNECTOR)

    assert source["source_commit_short"] == "4865b2b"
    assert source["tool_count"] == 25
    assert source["package_version_pyproject"] == "0.4.1"
    assert source["runtime_version_module"] == "0.4.0"
    assert source["version_consistent"] is False
    assert "capture_command_python" not in source

    assert connector["tool_count"] == 24
    assert connector["deployed_version"] is None
    assert connector["execution_status"]["health_probe"] == "failed"
    assert "502" in connector["execution_status"]["health_probe_error"]


def test_source_and_connector_tool_name_drift_is_explicit() -> None:
    source = load(SOURCE)
    connector = load(CONNECTOR)
    source_names = set(source["tool_names"])
    connector_names = set(connector["tool_names"])

    assert source_names - connector_names == {"check_result_consistency"}
    assert connector_names - source_names == set()
    assert len(source_names & connector_names) == 24


def test_schema_drift_summary_matches_pinned_contract() -> None:
    summary = load(SUMMARY)

    assert summary["source_tool_count"] == 25
    assert summary["connector_tool_count"] == 24
    assert summary["shared_tool_count"] == 24
    assert summary["source_only_tools"] == ["check_result_consistency"]
    assert summary["connector_only_tools"] == []
    assert summary["tools_with_hidden_connection_parameter"] == 23
    assert summary["tools_with_client_parameter_name_drift"] == 1
    assert summary["tools_with_schema_constraint_drift"] == 6


def test_important_tool_level_drift_is_preserved() -> None:
    with DRIFT_CSV.open(encoding="utf-8", newline="") as handle:
        rows = {row["tool_name"]: row for row in csv.DictReader(handle)}

    assert rows["check_result_consistency"]["status"] == "source_only"
    assert rows["create_product_system"]["source_only_client_parameters"] == (
        "cutoff;default_providers;preferred_type"
    )
    assert "enum" in rows["get_entity_by_name"]["schema_constraint_drift"]
    assert "enum" in rows["search_flows"]["schema_constraint_drift"]
    assert "exchanges" in rows["create_process"]["schema_constraint_drift"]

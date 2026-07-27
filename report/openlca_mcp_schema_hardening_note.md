# OpenLCA-MCP Schema Contract Hardening

## Measuring a source-level remediation against a pinned connector snapshot

**Author:** Ernest Boakye Danquah, SDAI Labs

**Status:** Preliminary technical note; not peer reviewed

**Study date:** July 26, 2026

## Abstract

A prior interface audit found that local OpenLCA-MCP source at commit `4865b2b` exposed 25 tools while the connector-visible surface exposed 24. Six shared tools differed in machine-readable schema constraints, one shared tool differed in top-level client parameters, and local version metadata disagreed between `pyproject.toml` (`0.4.1`) and `src.__version__` (`0.4.0`).

A separate source branch, `research/schema-contract-hardening`, applied contract-level remediations without changing or deploying the connector. The branch aligned runtime and package versions, added `Literal`-backed enums, bounded product-system cutoff to 0–1, and replaced generic process-exchange dictionaries with a closed Pydantic model that is converted back to ordinary dictionaries before existing handlers execute.

All 63 OpenLCA-MCP tests passed. The new source manifest at commit `b316008` reduced shared interface-drift tools from eight to four and schema-constraint drift from six tools to two. Drift was resolved for `analyze_contributions`, `get_entity_by_name`, `get_inventory_results`, and `search_flows`; no new drift was introduced. Remaining differences concern source-only functionality, expanded product-system controls, connector-default representation, and generic comparison-data objects. No deployed connector or live openLCA backend was changed, and the connector health probe remained unavailable with HTTP 502.

## 1. Motivation

Tool schemas are executable contracts for AI agents. Weak or ambiguous schemas shift validation work into prompts and model inference, where failures can be difficult to distinguish from model capability limitations.

The initial audit identified several gaps where source descriptions communicated constraints that generated JSON Schemas did not enforce. Examples included:

- `search_flows.flow_type` described a bounded set but accepted any string;
- `get_entity_by_name.model_type` had a known entity list but no generated enum;
- `get_inventory_results.direction` accepted an unconstrained string;
- `analyze_contributions.contribution_type` was described as process-or-flow but not machine constrained;
- `export_results.kind` and `format` were plain strings;
- `create_product_system.cutoff` lacked a machine-readable 0–1 bound;
- `create_process.exchanges` was generated as generic dictionaries rather than explicit exchange objects;
- package and runtime version metadata disagreed.

The remediation question was:

> How much source-to-connector contract drift can be reduced through local schema hardening without changing handlers, deploying a server, or contacting openLCA?

## 2. Source branches and manifests

### Before

- Source commit: `4865b2b997f32352bbc01988fee3fb74a1733db1`
- Package version: `0.4.1`
- Runtime version: `0.4.0`
- FastMCP tools: 25
- Connector snapshot: 24 tools, captured July 26, 2026

### After

- Branch: `research/schema-contract-hardening`
- Source commit: `b31600823cdcfc8509b9f66b889997c1d97965cd`
- Package version: `0.4.1`
- Runtime version: `0.4.1`
- FastMCP tools: 25
- Connector snapshot: unchanged

The same connector-visible snapshot was used for before/after comparison. This prevents deployed-surface variation from contaminating the remediation measurement.

## 3. Remediation changes

### 3.1 Version alignment

`src.__version__` was changed from `0.4.0` to `0.4.1`, matching `pyproject.toml`.

### 3.2 Literal-backed enums

Machine-readable enums were added for:

- `search_flows.flow_type`
- `get_entity_by_name.model_type`
- `get_inventory_results.direction`
- `analyze_contributions.contribution_type`
- `export_results.kind`
- `export_results.format`
- `create_product_system.default_providers`
- `create_product_system.preferred_type`

### 3.3 Numeric range

`create_product_system.cutoff` now uses an annotated 0–1 range.

### 3.4 Typed process exchanges

A `ProcessExchange` Pydantic model now defines:

- `flow_id`
- `amount`
- `is_input`
- `is_quantitative_reference`
- `provider_id`
- `formula`
- `unit_id`
- `flow_property_id`

Unknown exchange fields are rejected through `extra="forbid"`.

The public tool function accepts `list[ProcessExchange]`, while the bridge converts each object with `model_dump(exclude_none=True)` before calling the unchanged handler. This preserves handler compatibility while exposing a closed JSON Schema.

## 4. Verification

The source branch added contract tests for:

- package/runtime version identity;
- every new enum;
- cutoff bounds;
- explicit and closed exchange properties;
- required exchange fields;
- conversion of Pydantic exchange objects to handler dictionaries.

OpenLCA-MCP test results:

- Tests collected: 63
- Tests passed: 63
- Live openLCA backend required: no
- Deployed connector modified: no

## 5. Before/after results

| Metric | Before | After |
|---|---:|---:|
| Source version metadata consistent | False | True |
| Shared tools with interface drift | 8 | 4 |
| Tools with schema-constraint drift | 6 | 2 |
| Shared tools with parameter-name drift | 1 | 1 |
| Source-only tools | 1 | 1 |

### Resolved tools

- `analyze_contributions`
- `get_entity_by_name`
- `get_inventory_results`
- `search_flows`

### No introduced drift

No previously aligned shared tool became drifted under the remediation branch.

## 6. Remaining drift

### `check_result_consistency`

Remains source-only. This is a deployment-surface difference, not a schema-generation defect.

### `create_product_system`

Local source still exposes:

- `cutoff`
- `default_providers`
- `preferred_type`

The connector-visible schema does not. This reflects local source being ahead of the connector surface.

### `create_process`

The hardened source exchange schema is now explicit and closed, but it includes richer fields than the connector snapshot, including formula, unit, and flow-property controls. Description-default representation also differs.

### `create_product_flow`

The local description default is explicit as an empty string, while the connector schema marks it optional without exposing the same default.

### `export_results`

Enum drift was resolved. A smaller object-schema difference remains for `data`: local source permits additional properties explicitly, while the connector snapshot exposes a generic object.

## 7. Interpretation

The remediation reduced avoidable contract ambiguity but did not try to force current source to imitate an older or unknown connector deployment.

This distinction matters:

- **Schema-generation defects** should be fixed in source.
- **Intentional new capabilities** should remain versioned and documented.
- **Deployment lag** should be resolved through deployment/version management, not by deleting source features.
- **Hidden infrastructure parameters** such as `connection` require a deliberate client-surface policy.

The remaining drift is therefore not one homogeneous defect class.

## 8. Implications for scientific-agent evaluation

### 8.1 Stronger schemas reduce model ambiguity

Enums and nested object definitions reduce the number of structurally valid but semantically impossible calls.

### 8.2 Benchmarks must pin manifest commits

A model evaluated against `4865b2b` and one evaluated against `b316008` are not operating under identical contracts even when tool names remain unchanged.

### 8.3 Schema hardening is not deployment validation

The branch passed source-level tests, but the deployed connector was not updated and the openLCA backend remained unhealthy.

### 8.4 Before/after model testing is now possible

Because exact source descriptions and generated schemas exist for both commits, a schema-only model ablation can isolate the effect of contract hardening without involving the deployed connector.

That experiment should be reported separately from source-to-deployment drift.

## 9. Recommendations

1. Merge the schema-hardening branch after review.
2. Publish a generated manifest with every OpenLCA-MCP release.
3. Add manifest-diff checks to CI.
4. Expose deployed server version metadata.
5. Capture authenticated deployed `tools/list` after connector recovery.
6. Decide whether richer `create_process` fields should be deployed or normalized away.
7. Deploy `check_result_consistency` or explicitly mark it source-only.
8. Run a paired before/after schema-only model ablation.
9. Restore backend health before any live execution benchmark.
10. Validate generated schemas through sandboxed tool calls after deployment.

## 10. Reproducibility

### OpenLCA-MCP source branch

- Branch: `research/schema-contract-hardening`
- Commit: `b316008`
- Test file: `tests/test_tool_schema_contracts.py`

### Research artifacts

- `manifests/openlca_mcp_fastmcp_source_4865b2b.json`
- `manifests/openlca_mcp_fastmcp_source_b316008.json`
- `manifests/openlca_mcp_schema_drift_summary.json`
- `manifests/openlca_mcp_schema_drift_hardened_summary.json`
- `results/public/openlca_mcp_schema_drift.csv`
- `results/public/openlca_mcp_schema_drift_hardened.csv`
- `results/public/openlca_mcp_schema_hardening_delta.csv`
- `results/public/openlca_mcp_schema_hardening_delta.md`

### Scripts

- `scripts/export_openlca_mcp_fastmcp_manifest.py`
- `scripts/compare_openlca_mcp_manifests.py`
- `scripts/build_openlca_mcp_hardening_report.py`

## 11. Limitations

- The connector-visible snapshot is not a fresh authenticated direct `tools/list` payload.
- The deployed connector version remains unknown.
- The connector health probe returned HTTP 502.
- No live tool behavior was compared.
- Source-level tests cannot establish connector deployment correctness.
- Remaining differences may be intentional, stale, or deployment-specific.
- The study measures interface contracts, not end-to-end LCA accuracy.

## 12. AI-use disclosure

AI assistants supported schema analysis, code generation, test design, comparison tooling, and editorial revision. The author remains responsible for source changes, contract interpretation, testing decisions, and publication claims.

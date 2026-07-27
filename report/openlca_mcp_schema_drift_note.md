# OpenLCA-MCP Source-to-Connector Schema Drift

## A versioned interface audit for scientific agent tooling

**Author:** Ernest Boakye Danquah, SDAI Labs

**Status:** Preliminary technical note; not peer reviewed

**Audit date:** July 26, 2026

## Abstract

Scientific agents depend on tool schemas as executable contracts. A model may select the correct conceptual operation but still fail when tool names, parameters, defaults, constraints, or deployment versions differ from the schemas used during evaluation or development. This note audits drift between a local OpenLCA-MCP source checkout and the OpenLCA-MCP connector surface visible to the active ChatGPT conversation.

The local source at commit `4865b2b` generates 25 FastMCP tools. The connector exposes 24 tool names. All connector-visible names are present locally, while `check_result_consistency` exists only in local source. Twenty-three source tools include an optional internal `connection` parameter that is hidden from the connector-visible client surface. One shared tool, `create_product_system`, adds three client-visible parameters in source: `cutoff`, `default_providers`, and `preferred_type`. Six shared tools differ in schema constraints, including enums and nested exchange definitions. Local version metadata is internally inconsistent: `pyproject.toml` reports 0.4.1 while `src.__version__` reports 0.4.0. Live functional comparison was unavailable because the connector health probe returned HTTP 502.

The audit demonstrates why benchmark schemas, source schemas, and deployed connector schemas must be versioned separately. Interface drift can change measured tool-calling accuracy independently of model capability.

## 1. Motivation

An MCP tool schema controls:

- which tools an agent can see;
- which parameters it may provide;
- which values are required;
- which enums and ranges are valid;
- whether a tool is read-only or mutating;
- and how the runtime validates a proposed call.

A benchmark built against one schema version can become misleading when the deployed connector changes. Apparent model failures may instead be:

- renamed or missing tools;
- newly added parameters;
- stricter or looser schemas;
- hidden routing parameters;
- different defaults;
- or connector deployments that lag source.

This study treats the tool manifest itself as a versioned research artifact.

## 2. Snapshot sources

### 2.1 Local FastMCP-generated source manifest

Repository:

`https://github.com/SDAI-institute/openlca-mcp`

Local source commit:

`4865b2b997f32352bbc01988fee3fb74a1733db1`

The source checkout was imported through its own Python environment, and `FastMCP.list_tools()` was used to export actual generated input and output schemas. Importing the application registered tools but did not contact the openLCA IPC backend.

Primary artifact:

`manifests/openlca_mcp_fastmcp_source_4865b2b.json`

A static AST-derived cross-check is also preserved:

`manifests/openlca_mcp_source_4865b2b.json`

### 2.2 Connector-visible manifest

The connector-visible snapshot was captured from the tool schemas exposed to the active ChatGPT conversation by:

`api_tool.list_resources(paths=["openlca-mcp"])`

Artifact:

`manifests/openlca_mcp_connector_visible_2026-07-26.json`

The deployed connector version was not exposed. A direct authenticated `tools/list` fetch was not performed because execution safety controls prevented loading a local authentication token into the command runner.

### 2.3 Live execution status

The connector schema remained available, but:

`health_check(count_entities=true)`

returned an HTTP 502 upstream or external-service error. Therefore, this study compares interfaces only. It does not compare live tool behavior or database results.

## 3. Inventory results

| Property | Local source | Connector-visible |
|---|---:|---:|
| Total tools | 25 | 24 |
| Shared names | 24 | 24 |
| Source-only names | 1 | 0 |
| Read-only tools | 16 | 15 |
| Read-only stateful compute | 3 | 3 |
| Database-write tools | 3 | 3 |
| File-write tools | 1 | 1 |
| Result-store cleanup tools | 2 | 2 |

Source-only tool:

`check_result_consistency`

Connector-only tools:

None.

## 4. Version drift

The local source checkout reports two different versions:

| Version source | Value |
|---|---|
| `pyproject.toml` | `0.4.1` |
| `src.__version__` | `0.4.0` |

This can affect:

- server initialization metadata;
- package indexes and wheels;
- telemetry labels;
- bug reports;
- connector compatibility checks;
- and reproducibility statements.

The deployed connector version is unknown, so it cannot currently be mapped confidently to either local version value.

## 5. Tool-name drift

### 5.1 Source-only tool

`check_result_consistency` appears in local source but not in the connector-visible surface.

The tool checks whether process contributions sum to the reported impact total within tolerance. Its absence matters for reliability research because it is directly relevant to detecting partially computed or inconsistent results.

### 5.2 Connector-only tools

No connector-only tool names were observed.

## 6. Parameter-surface drift

### 6.1 Internal connection routing

Twenty-three local source tools expose an optional `connection` parameter. The connector-visible schemas hide it.

This is likely an intentional client-surface decision rather than an error: identity and connection selection may be resolved by connector infrastructure. Nevertheless, it means local generated schemas should not be used directly as user-visible benchmark schemas without normalization.

### 6.2 Expanded product-system creation

Local source adds three client-visible parameters to `create_product_system`:

- `cutoff`
- `default_providers`
- `preferred_type`

The connector-visible schema exposes only:

- `process_id`
- `process_name`

A model evaluated against the source schema may produce a call the deployed connector rejects.

## 7. Constraint drift

Six shared tools differ in generated constraints.

### `analyze_contributions`

The connector constrains `contribution_type` to:

- `process`
- `flow`

Local FastMCP source exposes it as an unconstrained string.

### `create_process`

The connector exposes a structured exchange schema requiring:

- `flow_id`
- `amount`
- `is_input`

Local FastMCP generation sees `list[dict[str, Any]]`, producing a generic object schema. The local description mentions additional fields such as formulas and unit/property identifiers, but those semantics are not encoded in the generated input schema.

### `export_results`

The connector constrains:

- `kind` to `impacts | comparison`
- `format` to `csv | excel`

Local source exposes plain strings.

### `get_entity_by_name`

The connector constrains `model_type` to six entity types. Local source exposes a plain string.

### `get_inventory_results`

The connector constrains `direction` to:

- `input`
- `output`
- `both`

Local source exposes a plain string.

### `search_flows`

The connector constrains `flow_type` to:

- `PRODUCT_FLOW`
- `ELEMENTARY_FLOW`
- `WASTE_FLOW`

Local source exposes a nullable plain string.

## 8. Default drift

The local source explicitly defaults descriptions to an empty string for:

- `create_process`
- `create_product_flow`

The connector schema marks those fields optional without exposing an explicit default.

This is a smaller difference than missing tools or parameters, but it can still affect generated calls and contract tests.

## 9. Risk classification

The manifests classify tools into operational categories:

### Read-only

Search, lookup, result reading, contributions, comparison, and visualization.

### Read-only stateful compute

- `calculate_impacts`
- `run_monte_carlo`
- `run_scenario_analysis`

These are registered as read-only but can create temporary calculation state or expensive computations.

### Database write

- `create_product_flow`
- `create_process`
- `create_product_system`

### File write

- `export_results`

### Result-store cleanup

- `dispose_result`
- `dispose_all_results`

This classification should be retained when selecting tools for local-model evaluation. Read-only and mutating tools should not be mixed without explicit safety policies.

## 10. Research implications

### 10.1 Schema drift can masquerade as model failure

A model might correctly produce `check_result_consistency`, `cutoff`, or `preferred_type` against local source but fail against the deployed connector.

Conversely, a model may depend on connector enums that local generated schemas do not communicate.

### 10.2 Source schemas are not automatically deployment schemas

Importing current source and calling `FastMCP.list_tools()` does not prove that the deployed connector is running that commit.

### 10.3 Descriptions are not substitutes for schemas

The local `create_process` description supports richer exchange concepts than its generated JSON Schema encodes. Models and validators may behave differently depending on whether they rely on prose or schema constraints.

### 10.4 Health and schema availability are separate

The connector can expose a schema while its openLCA backend is unreachable. Benchmarks should report manifest availability and execution availability separately.

## 11. Recommendations

1. Synchronize `pyproject.toml` and `src.__version__`.
2. Expose the deployed server version through connector metadata or a version tool.
3. Generate and publish a manifest artifact for every release.
4. Add source-to-deployed `tools/list` contract tests in CI.
5. Decide whether `connection` is an internal infrastructure concern or public tool argument, then document that policy.
6. Use `Literal` or Pydantic models where enums and nested exchange constraints should be machine-enforced.
7. Deploy or explicitly exclude `check_result_consistency` so source and connector behavior are intentional.
8. Version read-only, write, file-output, and cleanup tool groups separately for evaluation.
9. Keep benchmark task schemas pinned to a manifest hash.
10. Refuse live-execution claims when only the manifest is available.

## 12. Next benchmark phase

The next DomainToolBench layer should use a versioned read-only OpenLCA subset derived from the generated manifest. It should initially avoid database-write and file-write tools.

Recommended first subset:

- `search_flows`
- `search_processes`
- `search_impact_methods`
- `get_entity_by_name`
- `find_providers`
- `calculate_impacts`
- `get_inventory_results`
- `get_total_requirements`
- `analyze_contributions`
- `check_result_consistency`
- `compare_systems`
- `dispose_result`

Live execution should remain disabled until the backend health check succeeds.

## 13. Reproducibility

Artifacts:

- `manifests/openlca_mcp_fastmcp_source_4865b2b.json`
- `manifests/openlca_mcp_source_4865b2b.json`
- `manifests/openlca_mcp_connector_visible_2026-07-26.json`
- `manifests/openlca_mcp_schema_drift_summary.json`
- `results/public/openlca_mcp_schema_drift.csv`
- `results/public/openlca_mcp_schema_drift.md`

Scripts:

- `scripts/export_openlca_mcp_fastmcp_manifest.py`
- `scripts/export_openlca_mcp_source_manifest.py`
- `scripts/export_openlca_mcp_connector_snapshot.py`
- `scripts/compare_openlca_mcp_manifests.py`

## 14. Limitations

- The connector-visible snapshot was captured from the active connector schema, not a fresh authenticated direct `tools/list` response.
- The deployed version is unknown.
- The health probe failed, so live semantics were not tested.
- The local source checkout contained an untracked coverage file, but the exported manifest used committed source at `4865b2b`.
- Risk classifications combine MCP annotations with semantic interpretation.
- Descriptions in the connector snapshot are concise representations of the connector schema.
- Interface equality does not establish behavioral equality.

## 15. AI-use disclosure

AI assistants supported manifest export code, schema comparison, debugging, and editorial revision. The author remains responsible for source selection, schema verification, interpretation, and publication decisions.

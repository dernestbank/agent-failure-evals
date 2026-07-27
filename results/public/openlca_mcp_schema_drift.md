# OpenLCA-MCP Source-to-Connector Schema Drift

## Snapshot identity

- Local source commit: `4865b2b`
- Local package version from `pyproject.toml`: `0.4.1`
- Local runtime version from `src.__version__`: `0.4.0`
- Local version metadata consistent: **False**
- Connector-visible deployed version: **unknown**
- Connector schema provenance: ChatGPT connector tool schema capture on 2026-07-26
- Connector health probe: **failed with HTTP 502 upstream/external-service error**

## Inventory

- Local FastMCP-generated tools: **25**
- Connector-visible tools: **24**
- Shared names: **24**
- Source-only tools: `check_result_consistency`
- Connector-only tools: `none`
- Source tools with internal `connection` routing parameter: **23**
- Shared tools with client-visible parameter-name drift: **1**
- Tools with schema/constraint drift: **6**

## Drift summary

| Tool | Status | Source-only client params | Connector-only params | Constraint/default drift |
|---|---|---|---|---|
| `analyze_contributions` | shared_interface_drift | none | none | contribution_type:source={"type":"string"};connector={"enum":["process","flow"],"type":"string"} |
| `check_result_consistency` | source_only | abs_tol;rel_tol;result_id | none | none |
| `create_process` | shared_interface_drift | none | none | description:source=''; connector=unspecified<br>exchanges:source={"items":{"additionalProperties":true,"type":"object"},"type":"array"};connector={"items":{"properties":{"amount":{"type":"number"},"flow_id":{"type":"string"},"is_input":{"type":"boolean"},"is_quantitative_reference":{"type":"boolean"},"provider_id":{"type":"string"}},"required":["flow_id","amount","is_input"],"type":"object"},"type":"array"} |
| `create_product_flow` | shared_interface_drift | none | none | description:source=''; connector=unspecified |
| `create_product_system` | shared_interface_drift | cutoff;default_providers;preferred_type | none | none |
| `export_results` | shared_interface_drift | none | none | data:source={"additionalProperties":true,"type":"object"};connector={"type":"object"} | format:source={"type":"string"};connector={"enum":["csv","excel"],"type":"string"} | kind:source={"type":"string"};connector={"enum":["impacts","comparison"],"type":"string"} |
| `get_entity_by_name` | shared_interface_drift | none | none | model_type:source={"type":"string"};connector={"enum":["Flow","Process","ImpactMethod","ProductSystem","FlowProperty","Unit"],"type":"string"} |
| `get_inventory_results` | shared_interface_drift | none | none | direction:source={"type":"string"};connector={"enum":["input","output","both"],"type":"string"} |
| `search_flows` | shared_interface_drift | none | none | flow_type:source={"type":"string"};connector={"enum":["PRODUCT_FLOW","ELEMENTARY_FLOW","WASTE_FLOW"],"type":"string"} |

## Interpretation

1. The local source is ahead of the connector-visible surface: it adds `check_result_consistency` and additional `create_product_system` options.
2. The connector hides the local `connection` routing parameter from the user-visible tool surface.
3. Several connector schemas expose stricter enums or nested exchange fields than the local Python annotations generate, indicating deployed-version drift or schema-generation differences.
4. Local version metadata is internally inconsistent (`0.4.1` package metadata versus `0.4.0` runtime constant).
5. Live behavior could not be compared because the connector health probe returned HTTP 502.
6. The source and connector manifests remain separate artifacts and are not silently merged.

These findings describe interface drift, not functional correctness or deployment safety.

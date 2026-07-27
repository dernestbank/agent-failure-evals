# OpenLCA-MCP Schema Hardening Delta

- Before source commit: `4865b2b`
- After source commit: `b316008`
- Deployed connector snapshot: connector-visible capture from 2026-07-26
- Live backend status: unavailable; connector health probe returned HTTP 502

## Metric changes

| Metric | Before | After |
|---|---:|---:|
| source version metadata consistent | False | True |
| shared tools with interface drift | 8 | 4 |
| tools with schema-constraint drift | 6 | 2 |
| shared tools with parameter-name drift | 1 | 1 |
| source-only tools | 1 | 1 |

## Tool-level changes

- Resolved drift: `analyze_contributions, get_entity_by_name, get_inventory_results, search_flows`
- Remaining drift: `check_result_consistency, create_process, create_product_flow, create_product_system, export_results`
- Introduced drift: `none`

| Tool | Change | Before | After |
|---|---|---|---|
| `analyze_contributions` | resolved | shared_interface_drift | shared_no_client_surface_drift |
| `check_result_consistency` | remaining | source_only | source_only |
| `create_process` | remaining | shared_interface_drift | shared_interface_drift |
| `create_product_flow` | remaining | shared_interface_drift | shared_interface_drift |
| `create_product_system` | remaining | shared_interface_drift | shared_interface_drift |
| `export_results` | remaining | shared_interface_drift | shared_interface_drift |
| `get_entity_by_name` | resolved | shared_interface_drift | shared_no_client_surface_drift |
| `get_inventory_results` | resolved | shared_interface_drift | shared_no_client_surface_drift |
| `search_flows` | resolved | shared_interface_drift | shared_no_client_surface_drift |

## Interpretation

- The hardening branch aligns runtime and package versions at 0.4.1.
- Literal annotations resolved enum drift for contribution type, entity type, inventory direction, and flow type.
- A typed Pydantic exchange model made process-exchange inputs explicit and closed.
- Remaining drift is intentional or deployment-related: source-only consistency tooling, expanded product-system options, description defaults, and generic comparison-data objects.
- No deployed connector or live backend was changed by this branch.

These results measure schema contracts only, not live functional correctness.

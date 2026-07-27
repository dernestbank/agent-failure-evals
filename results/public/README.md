# Public Aggregate Results

This directory contains sanitized aggregate outputs from the approved v0.2.0 experiment matrix.

## Included

- `main_model_matrix.csv` — frozen v1 metrics for all approved model-condition pairs
- `main_model_matrix.md` — Markdown rendering of the same matrix
- `condition_comparison.csv` — condition-level comparison table
- `sensitivity_excluding_ambiguous.csv` — post-audit sensitivity metrics
- `sensitivity_excluding_ambiguous.md` — readable sensitivity table
- `manual_audit_summary.md` — preliminary audit counts and ambiguity finding
- `manifest.json` — approved experiment IDs and release metadata
- `domain_tool_calling_baselines.csv` / `.md` — curated-catalog DomainToolBench model baselines
- `domain_catalog_ablation.csv` / `.md` — curated versus full-catalog comparison
- `domain_tool_retrieval_top3.csv` / `.md` — automatic top-3 retrieval diagnostics
- `domain_retrieval_ablation.csv` / `.md` — curated, full-catalog, and top-3 model comparison
- `domain_router_ablation.csv` / `.md` — single-stage, zero-shot-router, and four-example-router comparison
- `domain_gate_stability_runs.csv` — per-seed matched single-stage and binary-gate metrics
- `domain_gate_stability_aggregate.csv` — model-condition means and seed variability
- `domain_gate_stability_tasks.csv` — sanitized task-level gate and behavior outcomes
- `domain_gate_stability.md` — readable stability-study summary
- `domain_retrieval_threshold_sweep.csv` / `.md` — exploratory no-tool threshold trade-off
- `domain_tool_guard_ablation.csv` / `.md` — deterministic guard ablation on frozen proposals
- `domain_tool_guard_stability_runs.csv` — per-seed fresh proposal and guard metrics
- `domain_tool_guard_stability_aggregate.csv` — model-policy means and stability metrics
- `domain_tool_guard_stability_tasks.csv` — sanitized task-level proposal and guard outcomes
- `domain_tool_guard_stability.md` — readable repeated-study summary
- `openlca_mcp_schema_drift.csv` / `.md` — local-source versus connector-visible contract audit
- `openlca_mcp_schema_drift_hardened.csv` / `.md` — hardened source versus connector audit
- `openlca_mcp_schema_hardening_delta.csv` / `.md` — before/after remediation comparison
- `openlca_schema_hardening_model_runs.csv` — per-seed before/after OpenLCA model metrics
- `openlca_schema_hardening_model_aggregate.csv` — model-surface aggregate metrics
- `openlca_schema_hardening_model_tasks.csv` — paired task-level before/after transitions
- `openlca_schema_hardening_model_ablation.md` — readable first-pass model ablation
- `openlca_schema_replay_control_aggregate.csv` — same-schema replay-adjusted metrics
- `openlca_schema_replay_control_tasks.csv` — task-level before/after/replay comparison
- `openlca_schema_replay_control.md` — readable replay-control interpretation

## Excluded

The public aggregate directory intentionally excludes:

- API credentials
- `.env`
- Absolute local file paths
- Raw model responses
- Detailed audit worksheets
- Local process logs
- Personal application material

Raw traces remain ignored in the working repository until Ernest Boakye Danquah completes human review and approves a separate research-data release.

## Interpretation

The frozen FailTrace v1 matrix includes all 15 scenarios. The sensitivity analysis excludes two scenarios identified post hoc as annotation-ambiguous. Both result layers must be reported together.

DomainToolBench results use a separate 15-task seed with provisional normalized scientific tool schemas. Curated-catalog, full-catalog, top-3 retrieval, zero-shot-router, and four-example-router results must not be mixed without naming both the catalog and intervention condition. GPT-OSS accuracy metrics apply only to 12 scored records because three tasks returned no visible structured content.

Router results are single-run intervention ablations. Improvements in behavior accuracy may coincide with worse safe no-call behavior or more false calls; all dimensions must be reported together.

The binary-gate stability study uses a separate eight-task balanced subset, three seeds, and temperature 0.2. Those results must not be merged with the 15-task zero-temperature baselines without naming the task set and sampling condition.

The ToolCallGuard stability study uses the 15-task top-three retrieval set, three seeds, temperature 0.2, and deterministic paired transformations. The 0.60 retrieval threshold was selected post hoc on the current seed. Guard improvements describe filtering and validation, not improved model reasoning.

The OpenLCA-MCP schema audit compares a local FastMCP-generated source manifest at commit `4865b2b` with the connector-visible schema captured on July 26, 2026. The connector health probe failed with HTTP 502, and no live behavior comparison was made. Source and connector manifests remain separate.

The schema-hardening delta compares source commits `4865b2b` and `b316008` against the same pinned connector snapshot. It measures source contract remediation only; the deployed connector and live backend were not changed.

The OpenLCA source-schema model ablation uses 20 identical intents, three local models, three seeds, and temperature 0.2. The 360-run before/after matrix is interpreted together with a separate 180-run replay of the unchanged before surface. Replay-adjusted deltas describe contract-level proposal changes only; no call was executed in openLCA, repeated seeds are not independent, and the deployed connector was not evaluated.

All results are preliminary, not peer reviewed, and apply only to the tested prompts, model identifiers, providers, catalog conditions, schemas, source commits, and controlled tasks.

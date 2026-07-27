---
title: OpenLCA-MCP Enum-Only Schema Ablation Log
status: running
study_id: openlca-enum-only-ablation
started: 2026-07-26
last_updated: 2026-07-26T22:30:18-04:00
repository_branch: experiment/provider-matrix
base_source_commit: 4865b2b997f32352bbc01988fee3fb74a1733db1
parent_study_commit: f60acaa
---

# OpenLCA-MCP Enum-Only Schema Ablation Log

## Research question

Do machine-enforced enums alone improve local-model OpenLCA tool-call proposals when all other source-schema fields and task semantics are held fixed?

## Motivation

The preceding full hardening study changed multiple contracts together. Replay-adjusted gains were retained for Qwen 3 and Gemma 3, with direct mechanisms involving:

- `get_entity_by_name.model_type`;
- `search_flows.flow_type`;
- `get_inventory_results.direction`.

This follow-up isolates enum constraints from range, nested-object, version, and other schema changes.

## Synthetic intervention

Base manifest:

- `manifests/openlca_mcp_fastmcp_source_4865b2b.json`
- Source commit: `4865b2b`

Enum-only variant adds enums to exactly four properties:

1. `analyze_contributions.contribution_type`
2. `get_entity_by_name.model_type`
3. `get_inventory_results.direction`
4. `search_flows.flow_type`

No other tool schema, description, default, required list, or task semantic may change.

The variant is synthetic. It is not a source commit, deployed server version, or connector snapshot.

## Frozen design

- Tasks: 20 identical OpenLCA intents per condition.
- Conditions: unchanged control and enum-only synthetic variant.
- Models: Qwen Coder 1.5B, Gemma 3 4B, Qwen 3 8B.
- Seeds: 101, 202, 303, 404.
- Temperature: 0.2.
- Runtime: local Ollama, one model at a time.
- Planned experiments: 24.
- Planned task runs: 480.
- Live tool execution: none.

### Counterbalanced order

- Seeds 101 and 303: control first, enum-only second.
- Seeds 202 and 404: enum-only first, control second.

The paired control and intervention are collected in the same run window to reduce time-order confounding.

## Groups to report

- All task-seed pairs.
- Expected-tool schema changed.
- Distractor-only schema changed.
- Schema-identical.
- Control-first versus enum-first order.

## Primary hypotheses

1. Qwen 3 improves on `olca-exact-entity-001` and `olca-search-flows-001`.
2. Gemma improves on `olca-inventory-output-001`.
3. Qwen Coder 1.5B does not materially improve because routing weakness dominates schema guidance.
4. Schema-identical tasks show no systematic net gain.
5. Direction of the effect is similar under both condition orders.

## Metrics

- Exact call-sequence accuracy.
- Behavior accuracy.
- Tool-selection accuracy.
- Required-argument recall.
- Argument precision.
- False-tool-call rate.
- Result, behavior, and call identity.
- Paired improvements and regressions.
- Order-stratified deltas.
- Completion reliability and infrastructure failures.

## Change control

- The variant builder must prove exactly four tools changed.
- Task IDs, prompts, behavior labels, expected calls, and valid alternatives must be identical.
- The runner must acquire an atomic lock before writing any record.
- If a duplicate or partial contaminated run occurs, all affected experiment directories will be deleted and rerun from zero.
- No prompt or scoring changes are allowed after the first model call.
- Failed records will remain preserved and counted.

## Interpretation constraints

- Four enums are changed together; this is enum-only but not per-enum.
- Four seeds on the same twenty intents are not independent samples.
- The study evaluates proposals, not openLCA execution or scientific correctness.
- The synthetic variant is not deployment evidence.
- A positive result must be reported with order effects and task-level mechanisms.

## Planned artifacts

- `manifests/openlca_mcp_fastmcp_source_4865b2b_enum_only_v0.json`
- `tasks/domain_tool_calling_openlca_source_4865b2b_enum_only_v0.jsonl`
- `results/public/openlca_enum_only_ablation.md`
- `results/public/openlca_enum_only_aggregate.csv`
- `results/public/openlca_enum_only_order_effects.csv`
- `results/public/openlca_enum_only_tasks.csv`
- `results/public/openlca_enum_only_failures.json`

## Pre-inference checklist

- [x] Build enum-only manifest and benchmark
- [x] Verify only four tool contracts changed
- [x] Verify task semantics are identical
- [x] Verify expected-tool and distractor groups
- [x] Freeze runner and analysis
- [x] Pass Ruff, strict mypy, compilation, and focused tests
- [x] Confirm no active runner or stale lock
- [x] Launch one counterbalanced matrix

## Freeze checkpoint

- Variant changed tools: `analyze_contributions`, `get_entity_by_name`, `get_inventory_results`, `search_flows`.
- Task semantics: 20/20 aligned.
- Expected-tool-changed tasks: 6.
- Any-schema-exposure-changed tasks: 15.
- Ruff formatting and lint: passed.
- Strict mypy across 75 modules: passed.
- Compilation: passed.
- Focused tests: 8 passed.
- First model call made: no.

## Launch provenance

- Launch time: 2026-07-26T22:28:36-04:00.
- Parent interpreter PID: 79504.
- Lock owner PID: 85420.
- Lock path: `results/processed/openlca_enum_only_matrix.lock`.
- First accepted condition: Qwen Coder 1.5B seed 101 control.
- Initial verified progress: 13/20 records.
- Concurrent duplicate runner detected: no.
- Launch command retried after connector timeout: no.

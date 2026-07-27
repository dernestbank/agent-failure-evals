---
title: OpenLCA-MCP Schema Hardening Model Ablation Log
status: active
study_id: openlca-schema-hardening-model-ablation
started: 2026-07-26
last_updated: 2026-07-26T21:46:13-04:00
repository_branch: experiment/provider-matrix
before_source_commit: 4865b2b997f32352bbc01988fee3fb74a1733db1
after_source_commit: b31600823cdcfc8509b9f66b889997c1d97965cd
---

# OpenLCA-MCP Schema Hardening Model Ablation Log

## Research question

Does strengthening generated OpenLCA-MCP JSON Schemas change tool-calling behavior when task semantics, prompts, expected calls, model identity, seed, temperature, and runtime are otherwise held fixed?

## Schema intervention

The `after` surface changes only generated source contracts introduced on OpenLCA-MCP branch `research/schema-contract-hardening`:

- package/runtime version alignment at 0.4.1;
- `Literal`-backed enums for contribution type, entity type, inventory direction, and flow type;
- a bounded 0–1 product-system cutoff;
- a closed Pydantic process-exchange object;
- enum-backed export and product-system options.

The deployed connector and live openLCA backend were not changed.

## Frozen design

- Benchmark before: `tasks/domain_tool_calling_openlca_source_v0.jsonl`
- Benchmark after: `tasks/domain_tool_calling_openlca_source_b316008_v0.jsonl`
- Task semantics: 20 identical intents per surface
- Models: `qwen2.5-coder:1.5b`, `gemma3:4b`, `qwen3:8b`
- Seeds: 101, 202, 303
- Temperature: 0.2
- Runtime: local Ollama, one model at a time
- Planned experiments: 18
- Planned task runs: 360
- Execution: schema-level proposal generation only; no openLCA tool call was executed

### Schema exposure groups

- 15/20 tasks attach at least one tool whose schema differs across source commits.
- 6/20 tasks change the schema of a tool in the expected call sequence.
- 9/20 tasks change only a distractor tool schema.
- 5/20 tasks attach identical tool schemas.

## Provenance incident and remediation

An initial matrix launch was accidentally started twice after a connector timeout. Both processes wrote toward the same experiment IDs. The duplication was detected before analysis.

Actions taken:

1. Stopped both active runners.
2. Deleted every partial `openlca-schema-*` experiment directory.
3. Added an atomic lock at `results/processed/openlca_schema_hardening_matrix.lock`.
4. Restarted the full matrix from zero through a single background launcher.
5. Verified one lock owner and one Python runner before accepting results.

No potentially contaminated record was retained.

## Completed matrix

Completion time: before 2026-07-26T21:15:43-04:00.

- Experiments completed: 18/18
- Task records present: 360/360
- Scored records: 360
- Infrastructure failures: 0
- Lock released normally: yes
- Active model after completion: none

## Initial aggregate results

| Model | Exact before | Exact after | Delta | Expected-tool-changed before | Expected-tool-changed after | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Qwen Coder 1.5B | 6.7% | 6.7% | 0.0 pp | 0.0% | 0.0% | 0.0 pp |
| Gemma 3 4B | 10.0% | 20.0% | +10.0 pp | 0.0% | 16.7% | +16.7 pp |
| Qwen 3 8B | 48.3% | 60.0% | +11.7 pp | 16.7% | 50.0% | +33.3 pp |

Other observations:

- Qwen Coder 1.5B: 2 paired improvements and 2 regressions.
- Gemma 3 4B: 6 paired improvements and 0 regressions.
- Qwen 3 8B: 7 paired improvements and 0 regressions.
- All three surfaces achieved 100% completion reliability.

## Methodological caveat discovered after analysis

Four improvements occurred on tasks whose attached schemas were identical between `before` and `after`:

- Gemma 3 improved on `olca-health-fast-001` in all three seeds.
- Qwen 3 improved on `olca-health-fast-001` in seed 202.

Because those prompts were schema-identical, identical seeds and temperature did not guarantee identical replay under the tested Ollama/GPU environment. The aggregate before/after gain therefore cannot be attributed entirely to schema hardening without estimating same-schema replay variance.

## Required control before final interpretation

Run a same-schema replay control:

- replay the `before` benchmark under the same three models, seeds, temperature, and runtime;
- compare original-before versus repeated-before at task and aggregate levels;
- estimate background exact-call transition rates on identical prompts;
- compare schema-hardening transitions against replay transitions, especially on the six expected-tool-changed tasks;
- report schema effects as suggestive unless they exceed same-schema replay variation.

## Current interpretation status

Preliminary only. The current data support that Gemma 3 and Qwen 3 performed better on the hardened surface in this run, but a deterministic causal attribution to schema hardening is not yet justified.

## Output artifacts

- `results/public/openlca_schema_hardening_model_ablation.md`
- `results/public/openlca_schema_hardening_model_aggregate.csv`
- `results/public/openlca_schema_hardening_model_runs.csv`
- `results/public/openlca_schema_hardening_model_tasks.csv`
- `results/public/openlca_schema_hardening_model_failures.json`
- `results/processed/openlca_schema_hardening_matrix_plan.json`

## Replay control implementation and launch

Freeze gate completed before inference:

- Ruff formatting and linting: passed.
- Strict mypy across 70 source, script, and test modules: passed.
- Source/script/test compilation: passed.
- Seven focused replay and benchmark tests: passed.
- Atomic replay lock: tested against a concurrent writer.

Replay design:

- Benchmark: unchanged `4865b2b` before surface.
- Models: Qwen Coder 1.5B, Gemma 3 4B, Qwen 3 8B.
- Seeds: 101, 202, 303.
- Temperature: 0.2.
- Planned replay task runs: 180.
- Experiment IDs: `openlca-schema-replay-before-<model>-seed<seed>`.

Launch provenance:

- Start time: 2026-07-26T21:29:42-04:00.
- Lock owner: Python PID 59176.
- Parent interpreter: PID 55620.
- Duplicate launch guards rejected subsequent starts.
- First condition completed before logging; seed 202 was active.

## Replay completion

- Replay experiments completed: 9/9.
- Replay task runs completed: 180/180.
- Infrastructure failures: 0.
- Lock released normally: yes.
- Model left loaded: none.

### Replay identity

| Model | Exact-status agreement | Full-result identity |
|---|---:|---:|
| Qwen Coder 1.5B | 100.0% | 95.0% |
| Gemma 3 4B | 96.7% | 96.7% |
| Qwen 3 8B | 98.3% | 98.3% |

The expected-tool-changed subset had 100% full-result identity between original-before and replay-before for every model.

### Replay-adjusted findings

| Model | Schema delta | Replay delta | Replay-adjusted delta | Expected-tool schema delta | Expected-tool replay delta |
|---|---:|---:|---:|---:|---:|
| Qwen Coder 1.5B | 0.0 pp | 0.0 pp | 0.0 pp | 0.0 pp | 0.0 pp |
| Gemma 3 4B | +10.0 pp | +3.3 pp | +6.7 pp | +16.7 pp | 0.0 pp |
| Qwen 3 8B | +11.7 pp | +1.7 pp | +10.0 pp | +33.3 pp | 0.0 pp |

### Audited direct mechanisms

- Qwen 3 used enum-valid `Process` instead of lowercase `process` on all three seeds.
- Qwen 3 supplied `flow_type=PRODUCT_FLOW` on all three seeds only after hardening.
- Gemma reduced a redundant two-call inventory proposal to one direction-correct call on all three seeds.
- The schema-identical health-check improvement appeared in the replay and was classified as runtime variation.

## Final interpretation status

The evidence is consistent with direct schema benefits for Qwen 3 and Gemma on specific contract-sensitive tasks. Qwen Coder 1.5B did not benefit. The result remains preliminary because there are only six expected-tool-changed task intents, repeated seeds are not independent, and no call was executed in openLCA.

## Next actions

- [x] Implement locked same-schema replay runner
- [x] Add replay analysis and paired transition tables
- [x] Run 180 replay task calls
- [x] Audit replay discrepancies
- [x] Revise technical interpretation
- [ ] Update public manifest, report, white paper, and Course-notes
- [ ] Pass release gate and push model-ablation milestone

# Machine-Enforced Tool Schemas Improved Some Local-Model Calls, but Not All Models

## A paired OpenLCA-MCP schema-hardening ablation with same-schema replay control

**Author:** Ernest Boakye Danquah, SDAI Labs

**Status:** Preliminary technical note; not peer reviewed
**Study date:** July 26, 2026

## Abstract

This study evaluates whether strengthening machine-readable OpenLCA-MCP tool schemas changes local language-model tool calling when task semantics are held fixed. Twenty identical OpenLCA intents were rendered against two local source manifests: commit `4865b2b` before contract hardening and commit `b316008` after hardening. The intervention added machine-enforced enums, a bounded product-system cutoff, a closed process-exchange schema, and consistent package/runtime version metadata. Qwen 2.5 Coder 1.5B, Gemma 3 4B, and Qwen 3 8B were each tested with seeds 101, 202, and 303 at temperature 0.2 through Ollama, yielding 360 before/after task runs with no infrastructure failures.

The hardened surface did not improve Qwen Coder 1.5B. Gemma 3 exact-call accuracy increased from 10.0% to 20.0%, while Qwen 3 increased from 48.3% to 60.0%. Because some improvements occurred on schema-identical prompts, a second 180-run replay of the unchanged before surface was conducted. Replay-adjusted gains were +6.7 percentage points for Gemma and +10.0 points for Qwen 3 overall. On the six tasks whose expected-call tool schema changed, Gemma retained a +16.7-point gain and Qwen 3 a +33.3-point gain, while the replay control showed zero gain on that subset.

Raw-output review identified direct contract mechanisms. Qwen 3 changed `model_type` from invalid lowercase `process` to enum-valid `Process` and began supplying `flow_type=PRODUCT_FLOW`. Gemma removed a redundant inventory call and retained the requested `direction=output` call. These changes were identical across all three seeds and absent from the unchanged-schema replay. The findings support machine-readable schemas as a useful intervention for some models and parameters, but not as a substitute for routing competence, live execution validation, or larger held-out evaluation.

## 1. Research question

> When user requests, expected calls, model identity, seed, temperature, and runtime are held fixed, do stronger generated tool schemas improve local-model tool-call proposals?

The study concerns **proposal quality at the tool-contract layer**. It does not evaluate whether openLCA successfully executes the proposed calls or whether returned scientific results are correct.

## 2. Source intervention

### 2.1 Before surface

- OpenLCA-MCP source commit: `4865b2b997f32352bbc01988fee3fb74a1733db1`
- Package metadata version: 0.4.1
- Runtime version constant: 0.4.0
- FastMCP-generated tools: 25
- Schema-constraint drift against the pinned connector-visible snapshot: six tools

### 2.2 After surface

- OpenLCA-MCP source commit: `b31600823cdcfc8509b9f66b889997c1d97965cd`
- Branch: `research/schema-contract-hardening`
- Package/runtime versions: 0.4.1 / 0.4.1
- FastMCP-generated tools: 25
- Source tests: 63 passed
- Schema-constraint drift against the same pinned connector snapshot: two tools

The source hardening added:

- `Literal` enums for contribution type, entity type, inventory direction, flow type, export kind/format, and product-system options;
- a 0–1 product-system cutoff constraint;
- a closed Pydantic process-exchange object;
- consistent package and runtime version metadata.

No deployed connector or live openLCA backend was changed.

## 3. Benchmark design

### 3.1 Tasks

Twenty common OpenLCA intents were rendered against both source manifests.

The surfaces preserve identical:

- task IDs;
- user requests;
- expected behaviors;
- expected call sequences;
- valid alternatives;
- task order.

Only attached tool contracts differ.

### 3.2 Schema exposure groups

- **Expected-tool changed:** 6 tasks where a tool in the expected call sequence changed schema.
- **Distractor-only changed:** 9 tasks where only a non-target attached tool changed schema.
- **Schema-identical:** 5 tasks with identical attached schemas.

### 3.3 Models and sampling

| Model | Runtime | Seeds | Temperature |
|---|---|---|---:|
| Qwen 2.5 Coder 1.5B | Ollama | 101, 202, 303 | 0.2 |
| Gemma 3 4B | Ollama | 101, 202, 303 | 0.2 |
| Qwen 3 8B | Ollama | 101, 202, 303 | 0.2 |

The before/after matrix contained:

```text
3 models × 3 seeds × 2 source surfaces × 20 tasks = 360 task runs
```

All 360 records produced parseable scored outputs.

## 4. Run integrity and incident handling

An initial background launch was accidentally duplicated after a connector timeout. The duplicate was detected before analysis. Every partial `openlca-schema-*` experiment directory was deleted, an atomic lock was added, and the complete matrix was restarted from zero under one process.

The accepted matrix had:

- one lock owner;
- one sequential runner;
- no concurrent writers;
- no infrastructure failures;
- normal lock release;
- no model loaded after completion.

Potentially contaminated records were not retained.

## 5. Initial before/after results

| Model | Exact before | Exact after | Delta | Expected-tool changed before | Expected-tool changed after | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Qwen Coder 1.5B | 6.7% | 6.7% | 0.0 pp | 0.0% | 0.0% | 0.0 pp |
| Gemma 3 4B | 10.0% | 20.0% | +10.0 pp | 0.0% | 16.7% | +16.7 pp |
| Qwen 3 8B | 48.3% | 60.0% | +11.7 pp | 16.7% | 50.0% | +33.3 pp |

Paired exact-call transitions:

| Model | Improved | Regressed |
|---|---:|---:|
| Qwen Coder 1.5B | 2 | 2 |
| Gemma 3 4B | 6 | 0 |
| Qwen 3 8B | 7 | 0 |

## 6. Same-schema replay control

### 6.1 Motivation

Four before/after improvements occurred on schema-identical tasks. Identical prompts and seeds therefore did not produce perfectly deterministic replay under the tested Ollama/GPU environment.

A second run of the unchanged before surface was conducted with the same models, seeds, temperature, task order, and runtime:

```text
3 models × 3 seeds × 20 tasks = 180 replay task runs
```

The replay completed all 180 runs with zero infrastructure failures.

### 6.2 Replay identity

| Model | Exact-status agreement | Full-result identity |
|---|---:|---:|
| Qwen Coder 1.5B | 100.0% | 95.0% |
| Gemma 3 4B | 96.7% | 96.7% |
| Qwen 3 8B | 98.3% | 98.3% |

On the **expected-tool-changed subset**, original-before and replay-before full outputs were identical for all three models.

### 6.3 Replay-adjusted results

| Model | Schema delta | Replay delta | Replay-adjusted delta | Expected-tool schema delta | Expected-tool replay delta |
|---|---:|---:|---:|---:|---:|
| Qwen Coder 1.5B | 0.0 pp | 0.0 pp | 0.0 pp | 0.0 pp | 0.0 pp |
| Gemma 3 4B | +10.0 pp | +3.3 pp | **+6.7 pp** | **+16.7 pp** | 0.0 pp |
| Qwen 3 8B | +11.7 pp | +1.7 pp | **+10.0 pp** | **+33.3 pp** | 0.0 pp |

The replay-adjusted quantity is descriptive, not a causal estimator with independent observations. Tasks recur across seeds and the benchmark is small.

## 7. Direct contract mechanisms

### 7.1 Qwen 3: entity-type enum

Request: exact lookup of a process.

Before and replay:

```json
{"model_type": "process", "name": "Polyethylene terephthalate production"}
```

After:

```json
{"model_type": "Process", "name": "Polyethylene terephthalate production"}
```

The hardened `Literal` enum made the expected capitalization explicit. The corrected result occurred in all three seeds, while before and replay outputs were identical in all three seeds.

### 7.2 Qwen 3: flow-type enum

Request: search product flows for steel, hot, rolled.

Before and replay omitted the requested flow-type filter. After hardening, all three seeds produced:

```json
{
  "keywords": ["steel", "hot", "rolled"],
  "max_results": 10,
  "flow_type": "PRODUCT_FLOW"
}
```

### 7.3 Gemma 3: inventory direction contract

Request: return output inventory flows for `res-001`.

Before and replay emitted two calls: one without `direction`, followed by the requested output-filtered call. After hardening, all three seeds emitted only:

```json
{
  "result_id": "res-001",
  "direction": "output"
}
```

Gemma's top-level behavior label remained `clarify`, so the intervention improved exact call sequence and argument fidelity without fully repairing behavior classification.

## 8. Runtime-variation example

On `olca-health-fast-001`, the attached schemas were identical.

For Gemma seed 202:

- Original before: `test_connection` followed by `health_check`.
- Hardened after: only `health_check(count_entities=false)`.
- Before replay: only `health_check(count_entities=false)`.

The apparent hardening improvement was reproduced by the unchanged-schema replay and is therefore treated as runtime/inference variation rather than a schema effect.

## 9. Interpretation

### Supported

- Stronger generated schemas can improve exact call arguments and call count for some local models.
- Enum constraints had consistent, interpretable effects for Qwen 3 across all tested seeds.
- The inventory-direction schema reduced Gemma's redundant call sequence across all tested seeds.
- The 1.5B coder did not benefit at the benchmark level; schema improvements cannot compensate for severe routing weakness.
- Same-schema replay is necessary when local inference is not perfectly deterministic.

### Not supported

- The study does not establish statistical significance.
- It does not establish general model superiority.
- It does not show that calls execute successfully in openLCA.
- It does not evaluate the deployed connector.
- It does not show that stronger schemas fix behavior classification, sequencing, or abstention generally.

## 10. Limitations

- Twenty intents are too few for broad inference.
- Only six task intents directly changed the expected-call tool schema.
- The same tasks were repeated across seeds and are not independent samples.
- Exact-match scoring may miss valid unannotated alternatives.
- The after surface includes multiple simultaneous schema changes rather than one isolated constraint per experiment.
- No live openLCA tool execution or scientific-result validation was performed.
- The connector-visible deployed version and exact descriptions remain unknown.

## 11. Next experiments

1. **Single-constraint ablations:** enum-only, range-only, and nested-object-only surfaces.
2. **Held-out OpenLCA intents:** evaluate unseen requests and hard negatives.
3. **Live sandbox execution:** validate that accepted calls execute and produce expected result shapes.
4. **Schema simplification:** compare verbose generated schemas with compact agent-facing contracts.
5. **Guard interaction:** test hardened schemas with ToolCallGuard and execution feedback.
6. **Deployment manifest capture:** compare local source with a fresh authenticated deployed `tools/list` snapshot.

## 12. Reproducibility

Primary assets:

- `tasks/domain_tool_calling_openlca_source_v0.jsonl`
- `tasks/domain_tool_calling_openlca_source_b316008_v0.jsonl`
- `scripts/run_openlca_schema_hardening_matrix.py`
- `scripts/build_openlca_schema_hardening_model_report.py`
- `scripts/run_openlca_schema_replay_control.py`
- `scripts/build_openlca_schema_replay_report.py`
- `results/public/openlca_schema_hardening_model_ablation.md`
- `results/public/openlca_schema_replay_control.md`
- `docs/experiment_logs/openlca_schema_hardening_model_ablation_log.md`

Raw model outputs remain excluded from the public repository pending privacy and release review.

## 13. AI-use disclosure

AI assistants supported code generation, debugging, experiment orchestration, audit queries, and editorial revision. The author remains responsible for benchmark design, source review, ground-truth approval, interpretation, and publication decisions.

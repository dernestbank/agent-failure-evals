# Deterministic ToolCallGuard Improved Execution Safety Without Changing the Model

## A paired stability study for small local scientific language models

**Author:** Ernest Boakye Danquah, SDAI Labs

**Status:** Preliminary technical note; not peer reviewed

**Study date:** July 26, 2026

## Abstract

Small language models can produce structurally valid function calls that remain unsafe or scientifically unsupported. Common failures include irrelevant tools, fabricated identifiers, omitted requested parameters, out-of-range values, surplus calls, and plausible arguments that were not grounded in the user request. This study evaluates a deterministic ToolCallGuard layered after model generation and top-three tool retrieval.

Three local Ollama models—Qwen 3 8B, Gemma 3 4B, and Qwen 2.5 Coder 1.5B—generated proposals for the same 15-task provisional DomainToolBench seed at temperature 0.2 across seeds 101, 202, and 303. The resulting 135 model proposals were transformed under two deterministic policies: strict blocking and sanitize-and-preserve. No extra model inference was used for the guard.

Sanitization preserved every already exact proposal and captured every unsafe proposal across all three models. It raised exact-call accuracy from 80.0% to 93.3% for Qwen 3, from 48.9% to 93.3% for Gemma 3, and from 11.1% to 73.3% for the 1.5B coder. False tool calls fell to zero and safe no-call accuracy reached 100% for all models. These gains reflect deterministic validation and filtering, not improved model reasoning. Residual errors came from missing retrieved tools, absent model calls, and incomplete multi-tool reasoning that a guard cannot safely invent.

## 1. Motivation

A language model is not an execution policy. Even when it returns valid JSON, an agent may still:

- call an irrelevant tool;
- invent an identifier or parameter;
- silently replace a requested value;
- omit a required or explicitly requested field;
- submit a value outside a valid range;
- add extra tools or calls;
- proceed despite missing information;
- or produce a call that is syntactically valid but unsupported by the request.

Prompting and model-generated routing did not provide monotonic safety gains in earlier DomainToolBench experiments. This study tests a different hypothesis:

> Hard execution boundaries should be enforced by deterministic software rather than another unconstrained model decision.

## 2. Research questions

1. Can deterministic validation capture unsafe proposals without rejecting already exact proposals?
2. Does sanitizing invalid or surplus content recover valid core calls more effectively than blocking the full proposal?
3. Are improvements stable across multiple model seeds?
4. Which residual failures remain outside the guard’s safe correction boundary?
5. How does a deterministic guard compare conceptually with a model-generated binary gate?

## 3. Experimental design

### 3.1 Models

- `qwen3:8b`
- `gemma3:4b`
- `qwen2.5-coder:1.5b`

All models ran locally through Ollama.

### 3.2 Tasks

The study used the 15-task provisional DomainToolBench top-three retrieval benchmark. Tasks cover:

- life-cycle assessment;
- green-hydrogen techno-economic analysis;
- process simulation;
- cross-domain calls;
- one-tool and multi-tool sequences;
- missing-information clarification;
- and no-tool abstention.

The tool schemas are normalized research interfaces and are not yet the versioned live SDAI MCP manifests.

### 3.3 Sampling

- Seeds: `101`, `202`, `303`
- Temperature: `0.2`
- Tasks per model-seed run: `15`
- Model proposal runs: `135`
- Paired guard transformations: `270`
- Infrastructure failures: `0`

Each model produced one proposal per task and seed. Both guard policies were then applied to the same proposal, creating a paired comparison without additional model calls.

### 3.4 Retrieval threshold

The guard used a top-one embedding-score threshold of `0.60`. A post-hoc sweep over the current seed showed that 0.60 separated the two abstention tasks from all 13 relevant-tool tasks. This threshold was selected after inspecting the current scores and must not be described as preregistered, held-out, or generally validated.

### 3.5 Guard checks

The deterministic layer checks:

- retrieval score against the exploratory no-tool threshold;
- tool membership in the retrieved catalog;
- whether the request supports invoking the tool;
- required arguments;
- explicitly requested arguments;
- JSON types;
- enum membership;
- numeric ranges;
- conditional cross-argument ranges;
- identifier and value grounding in the request;
- unsolicited optional arguments;
- surplus calls;
- and duplicate calls.

The revision used for the final analysis was:

`v0.2-explicit-invalid-block-numeric-coercion`

This revision added two safety rules:

1. If an explicitly requested value is invalid, the call is blocked rather than executed after removing that value.
2. A grounded numeric string or number word may be canonically converted to the schema’s numeric type.

## 4. Policies

### 4.1 Model only

The original model proposal is scored without deterministic intervention.

### 4.2 Strict block

Any guard violation blocks the complete proposal and returns a clarification outcome.

This maximizes conservatism but may reject a valid core call because of one harmless surplus field.

### 4.3 Sanitize and preserve

The guard:

- removes unsupported optional arguments;
- removes invalid or irrelevant surplus calls;
- canonicalizes grounded numeric representations;
- preserves valid calls;
- recalculates `call` versus `multi_call` from the surviving sequence;
- and blocks the request if no safe grounded call remains.

It never creates a new tool call, identifier, or scientific value.

## 5. Results

| Model | Policy | Behavior | Exact calls | Tool selection | Argument recall | Argument precision | Safe no-call | False calls | Exact preservation | Unsafe capture |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen 3 8B | Model only | 93.3% | 80.0% | 91.1% | 96.7% | 86.7% | 75.0% | 6.7% | 100% | 0% |
| Qwen 3 8B | Strict | 93.3% | 86.7% | 91.1% | 90.0% | 88.9% | 100% | 0% | 100% | 100% |
| Qwen 3 8B | Sanitize | **100%** | **93.3%** | **97.8%** | 96.7% | **95.6%** | **100%** | **0%** | **100%** | **100%** |
| Gemma 3 4B | Model only | 66.7% | 48.9% | 71.1% | 95.2% | 60.7% | 0% | 26.7% | 100% | 0% |
| Gemma 3 4B | Strict | 75.6% | 75.6% | 75.6% | 75.6% | 75.6% | 100% | 0% | 100% | 100% |
| Gemma 3 4B | Sanitize | **100%** | **93.3%** | **97.8%** | **96.7%** | **100%** | **100%** | **0%** | **100%** | **100%** |
| Qwen Coder 1.5B | Model only | 26.7% | 11.1% | 53.3% | 76.7% | 30.9% | 8.3% | 24.4% | 100% | 0% |
| Qwen Coder 1.5B | Strict | 35.6% | 35.6% | 35.6% | 35.6% | 35.6% | 100% | 0% | 100% | 100% |
| Qwen Coder 1.5B | Sanitize | **80.0%** | **73.3%** | **80.0%** | 78.9% | **84.4%** | **100%** | **0%** | **100%** | **100%** |

### 5.1 Exact-call preservation

Neither strict nor sanitize produced a false positive on any proposal that was already exact. Exact preservation was 100% for every model and policy.

This is essential: a safety layer that frequently breaks correct calls would not be operationally useful.

### 5.2 Unsafe proposal capture

After the explicit-invalid-input fix, both deterministic policies captured every unsafe proposal in the 135-proposal study.

The guard blocked or transformed proposals containing:

- calls on abstention tasks;
- fabricated identifiers;
- missing required arguments;
- invalid capacity factors;
- wrong JSON types;
- ungrounded parameters;
- irrelevant tools;
- unsolicited optional arguments;
- and surplus calls.

### 5.3 Strict versus sanitize

Strict blocking removed all false calls but discarded many partially correct proposals. This was especially costly for the 1.5B model, where strict exact-call accuracy reached only 35.6%.

Sanitization preserved valid core calls and recovered much more utility:

- Qwen 3: 93.3% exact calls;
- Gemma 3: 93.3%;
- Qwen Coder 1.5B: 73.3%.

The result supports layered filtering when the transformations are narrow, deterministic, and fully logged.

## 6. Residual failures

### 6.1 Retrieval ceiling

Qwen 3 and Gemma 3 failed only the TEA comparison task after sanitization. The top-three retriever omitted `compare_tea_scenarios`, so the correct call sequence could not be constructed from the available catalog.

This demonstrates:

> Retrieval recall is an upper bound on end-to-end call accuracy.

The guard correctly refused to invent the absent tool.

### 6.2 Missing model reasoning

The 1.5B model sometimes returned `clarify` on tasks with enough information. A deterministic guard cannot safely invent calls that the model omitted.

It also produced incomplete cross-domain sequences. The guard removed unsupported calls but did not create the missing second domain call.

### 6.3 Multi-tool semantic gaps

The TEA sequence task remained non-exact because the retriever and proposals used result-fetching calls rather than the annotated comparison operation. Validation can reject invalid content, but it cannot infer an unprovided scientific workflow step without becoming another planner.

## 7. Comparison with the binary model gate

The previous binary call-gate study used another model decision to choose `call_required` versus `no_call`. That intervention:

- opened on every no-call task for the 1.5B model;
- opened on 75% of no-call tasks for Gemma;
- and made Qwen 3 less accurate, less safe, and slower than its single-stage baseline.

The deterministic guard differs fundamentally:

- decisions are rule-based and inspectable;
- exact calls are preserved;
- violations are enumerated;
- no extra model inference is required;
- and the software can enforce non-negotiable execution constraints.

The evidence favors deterministic validation for hard execution boundaries and models for bounded language interpretation.

## 8. Architectural implications

A safer small-model scientific agent should separate responsibilities:

1. **Retriever:** narrows the candidate tool catalog and exposes a no-tool option.
2. **Model:** proposes behavior, tools, and arguments.
3. **ToolCallGuard:** validates grounding, schemas, values, and call structure.
4. **Executor:** runs only approved calls in a sandbox.
5. **EvidenceGuard:** verifies that execution evidence supports the final claim.
6. **Human escalation:** handles unresolved ambiguity or consequential actions.

The guard is not a substitute for model improvement. It is a containment and validation layer.

## 9. Limitations

- The benchmark contains only 15 provisional tasks.
- The threshold was selected post hoc on the current seed.
- Three seeds do not establish broad statistical reliability.
- Guard transformations reuse the same proposal and are not independent model runs.
- Grounding rules use manually designed aliases and request matching.
- Tool schemas are provisional and not yet the live versioned MCP manifests.
- No live scientific tool execution was performed.
- Sanitization may undercount semantically valid alternatives not included in annotations.
- Exact-call recovery reflects filtering, not improved reasoning.
- The study does not establish deployment safety.

## 10. Next experiments

1. Build separate calibration and held-out threshold sets.
2. Expand no-tool and hard-negative tasks.
3. Export and version the live openLCA-MCP manifest.
4. Validate calls against a sandboxed live executor.
5. Add deterministic unit and database-identifier resolution.
6. Test schema drift and tool-version changes.
7. Evaluate adversarial argument injection.
8. Add execution feedback with bounded repair.
9. Compare guard-aware fine-tuning with post-hoc filtering.
10. Measure latency, memory, and energy overhead end to end.

## 11. Reproducibility

Relevant files:

- `src/agent_failure_evals/tool_call_guard.py`
- `src/agent_failure_evals/tool_calling_guard_experiment.py`
- `scripts/build_retrieval_threshold_sweep.py`
- `scripts/apply_tool_call_guard_ablation.py`
- `scripts/run_tool_guard_stability_matrix.py`
- `scripts/recompute_tool_guard_outcomes.py`
- `scripts/build_tool_guard_stability_report.py`
- `tasks/domain_tool_calling_top3_mxbai_v0.jsonl`
- `results/public/domain_retrieval_threshold_sweep.md`
- `results/public/domain_tool_guard_ablation.md`
- `results/public/domain_tool_guard_stability.md`

Raw proposal traces remain excluded from the public aggregate release pending human review and data-release approval.

## 12. AI-use disclosure

AI assistants supported code generation, debugging, experiment orchestration, documentation, and editorial revision. The author remains responsible for benchmark design, rule selection, ground-truth review, interpretation, and publication decisions.

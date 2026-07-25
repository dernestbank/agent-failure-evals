# False Success in Tool-Using Scientific Agents

## A Controlled Multi-Model Pilot of Self-Checking and Independent Verification

**SDAI Labs Technical Report v0.1**
**Author:** Ernest Boakye Danquah
**Date:** July 2026
**Status:** Preliminary, not peer reviewed

## Abstract

Tool-using language-model agents can produce polished scientific answers even when required inputs are missing, tools fail, outputs are partial, units conflict, or evidence contradicts a draft conclusion. This pilot introduces a 15-scenario benchmark for measuring false-success claims: reporting a workflow as completed when explicit completion criteria were not met. Four model configurations were evaluated under three conditions—a natural baseline, same-model self-check, and independent verification—producing 180 scored records. A 20% stratified audit identified two annotation-ambiguous scenarios, motivating a transparent post-audit sensitivity analysis on the remaining 13 scenarios. In that sensitivity analysis, the pooled baseline false-success rate was 1/36 (2.8%); self-checking and verification each produced 0/36 observed false successes. Same-model self-checking did not improve pooled status accuracy, while independent verification increased it from 80.8% to 82.7%. The only unambiguous false success occurred with local Gemma 3 4B on a partial-output task and was corrected by both oversight conditions. The study is small and controlled; results should be interpreted as a benchmark and engineering demonstration rather than evidence of general model safety.

## 1. Motivation

Scientific agents increasingly connect language models to databases, simulators, calculation engines, code, and reporting tools. A tool call can return successfully at the transport layer while the scientific workflow remains incomplete. Conversely, a model may be able to repair a missing transformation from available evidence, making workflow-completion labels difficult to define.

The central risk studied here is **false success**: a model reports `completed` even though the observable trace does not satisfy the benchmark's completion criteria. This differs from ordinary answer error. A false-success claim can suppress escalation, conceal missing evidence, and cause downstream systems or people to treat an unsupported result as final.

This work is related to recent research on automated behavioral evaluations, model-monitor blind spots, alignment auditing agents, AI control on difficult-to-grade tasks, and the gap between tool evidence and effective agent use.

## 2. Research questions

1. How often do tested models falsely claim that incomplete scientific workflows are complete?
2. Does same-model self-checking reduce false success?
3. Does an independent verifier outperform self-checking?
4. How reliably do local small models produce structured, auditable outputs?
5. Which apparent model failures are actually benchmark-design or infrastructure failures?

## 3. Experimental design

### 3.1 Benchmark

The frozen v1 benchmark contains 15 controlled scientific-workflow scenarios:

- 4 valid completed workflows
- 4 workflows requiring `cannot_complete`
- 7 incomplete or failed workflows

Failure categories include:

- Missing required input
- Invalid entity
- Tool failure
- Contradictory instruction
- Unit mismatch
- Incomplete product system
- Partial output
- Evidence/conclusion mismatch

Each scenario includes:

- User request
- Observable tool trace
- Expected status
- Required evidence identifiers
- Explicit completion criteria

### 3.2 Models

The completed primary matrix includes:

| Tier | Provider | Model |
|---|---|---|
| Local | Ollama | `qwen3:8b` |
| Local | Ollama | `gemma3:4b` |
| Free hosted | OpenRouter | `openai/gpt-oss-20b:free` |
| Free hosted | OpenRouter | `google/gemma-4-26b-a4b-it:free` |

Paid OpenAI and Anthropic-through-OpenRouter models were configured but not executed because the supplied accounts returned quota or payment-required errors. No paid-model results are inferred or fabricated.

### 3.3 Oversight conditions

**Baseline.** A scientific-workflow assistant receives the task and observable tool trace and returns a structured result.

**Same-model self-check.** The original model receives its first answer plus explicit completion criteria and may revise its status.

**Independent verifier.** A fresh model context receives the task, trace, candidate answer, and completion criteria. It does not receive private reasoning.

### 3.4 Output schema

Every response contains:

- Status: `completed`, `incomplete`, or `cannot_complete`
- Answer
- Evidence identifiers
- Assumptions
- Tool errors
- Confidence
- Human-review flag

### 3.5 Metrics

Primary metrics:

- Status accuracy
- False-success rate
- Failure-detection rate
- True-completion rate
- Appropriate-abstention rate

Secondary metrics:

- Evidence completeness
- Unsupported evidence
- Human-review escalation
- Latency
- Output tokens
- Infrastructure and structured-output failures

False-success confidence intervals use the Wilson score interval.

## 4. Engineering findings before the main analysis

The experiment required several provider-robustness fixes:

1. A first baseline prompt was too audit-oriented and made the task artificially easy. Those results were retained as pilot data but excluded from the approved matrix.
2. One free hosted model intermittently returned `{}`. A structured-output repair loop was added.
3. Hosted Gemma represented tool errors as objects rather than strings. The schema was normalized without discarding content.
4. Local Gemma sometimes wrapped the result inside another JSON object. Recursive result extraction was added.
5. Concurrent Ollama model use caused HTTP 500 errors and Windows paging-file pressure. Local models were rerun sequentially with retry/backoff and explicit JSON-schema constraints.
6. One missing Gemma verifier record was repaired surgically while preserving valid baseline and self-check records. The repair was logged.

These are findings about scientific-agent infrastructure, not merely incidental debugging. Structured-output support alone did not guarantee schema-valid or complete responses.

## 5. Frozen v1 results

Across 15 scenarios, each model produced 45 condition records. All four approved experiments ultimately contained complete condition records and no unresolved infrastructure failures.

### 5.1 Status accuracy and false success

| Model | Baseline accuracy | Self-check accuracy | Verifier accuracy | Baseline false success | Self-check false success | Verifier false success |
|---|---:|---:|---:|---:|---:|---:|
| Qwen 3 8B | 86.7% | 80.0% | 86.7% | 0.0% | 9.1% | 0.0% |
| Gemma 3 4B | 73.3% | 73.3% | 80.0% | 9.1% | 0.0% | 0.0% |
| GPT-OSS 20B free | 73.3% | 80.0% | 73.3% | 9.1% | 9.1% | 18.2% |
| Gemma 4 26B free | 80.0% | 80.0% | 80.0% | 9.1% | 9.1% | 9.1% |

These frozen results are sensitive to two task-wording ambiguities identified during manual review and should not be used alone as the headline conclusion.

## 6. Manual audit

A reproducible 20% stratified sample selected 36 of the 180 records, with three records from every model-condition pair.

Preliminary review found:

- 36 records reviewed
- 4 records associated with two annotation-ambiguous tasks
- 100% agreement with automated labels among the remaining 32 records
- Human-author confirmation still required before external publication

### 6.1 Annotation ambiguities

**Evidence/conclusion mismatch.** The task asked the model to determine which option had lower impact. Numeric evidence was sufficient to correct an erroneous draft conclusion, so `completed` and `incomplete` interpretations were both defensible.

**Unit mismatch.** The task asked for a per-kilogram result while the trace supplied a per-tonne value and reported that the tool had not converted it. A model could still perform the arithmetic conversion itself, conflating tool-workflow completion with answer capability.

These scenarios will be rewritten in benchmark v1.1. The v1 frozen results remain preserved.

## 7. Post-audit sensitivity analysis

The two ambiguous tasks were excluded post hoc, leaving 13 scenarios per model and condition. This exclusion was not preregistered and is reported as a sensitivity analysis, not a replacement for the frozen v1 result.

### 7.1 Model-level results

| Model | Condition | Accuracy | False success | Failure detection | True completion | Appropriate abstention |
|---|---|---:|---:|---:|---:|---:|
| Qwen 3 8B | Baseline | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% |
| Qwen 3 8B | Self-check | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% |
| Qwen 3 8B | Verifier | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% |
| Gemma 3 4B | Baseline | 69.2% | 11.1% | 88.9% | 100.0% | 25.0% |
| Gemma 3 4B | Self-check | 69.2% | 0.0% | 100.0% | 100.0% | 0.0% |
| Gemma 3 4B | Verifier | 76.9% | 0.0% | 100.0% | 100.0% | 25.0% |
| GPT-OSS 20B free | Baseline | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |
| GPT-OSS 20B free | Self-check | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |
| GPT-OSS 20B free | Verifier | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |
| Gemma 4 26B free | Baseline | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |
| Gemma 4 26B free | Self-check | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |
| Gemma 4 26B free | Verifier | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% |

### 7.2 Pooled sensitivity results

Across four models:

- Baseline status accuracy: 42/52 (80.8%)
- Self-check status accuracy: 42/52 (80.8%)
- Verifier status accuracy: 43/52 (82.7%)
- Baseline false success: 1/36 (2.8%; 95% Wilson interval approximately 0.5%–14.2%)
- Self-check false success: 0/36 (upper 95% Wilson bound approximately 9.6%)
- Verifier false success: 0/36 (upper 95% Wilson bound approximately 9.6%)
- True completion: 16/16 for every condition
- Failure detection: 35/36 baseline, 36/36 self-check, and 36/36 verifier

The sample is too small to establish that either oversight method is generally superior. Zero observed failures does not imply zero underlying risk.

## 8. Interpretation

### 8.1 Self-checking is not monotonic improvement

In the frozen v1 data, self-checking sometimes made a correct answer worse. After ambiguous tasks were excluded, it removed the one observed Gemma 3 false success but did not improve pooled status accuracy. This supports evaluating self-checking empirically rather than assuming that an additional reflection prompt is always safer.

### 8.2 Independent verification showed a small accuracy gain

The independent verifier produced the highest pooled sensitivity accuracy, 82.7%, compared with 80.8% for baseline and self-check. The difference is one record and is not statistically persuasive at this sample size.

### 8.3 Most remaining errors involved status granularity

All models correctly completed valid workflows in the sensitivity set. Many errors were disagreements between `incomplete` and `cannot_complete`, not false completed claims. Operational systems may benefit from separating:

- Safety-critical completed versus not-completed detection
- Recoverability classification
- Human-escalation policy

### 8.4 Local models are viable research components

Ollama enabled complete, zero-marginal-cost local experiments and exact model-tag recording. Qwen 3 8B matched the hosted models' sensitivity accuracy on this benchmark. Local Gemma 3 4B was less accurate but demonstrated that oversight could correct an observed false-success case.

Latency comparisons are not controlled hardware benchmarks. They include local model loading, provider queues, repair attempts, and different token counts.

## 9. Limitations

1. Only 15 controlled scenarios were tested.
2. Two scenarios were annotation-ambiguous.
3. The sensitivity analysis was post hoc.
4. Each model-scenario-condition was run once; stochastic variance is unknown.
5. Mock traces do not capture full scientific software complexity.
6. The verifier reused the baseline trace and same model family rather than a fully independent model.
7. Models and hosted endpoints can change over time.
8. No paid frontier models were successfully executed.
9. The preliminary audit requires human-author confirmation.
10. No live openLCA, TEA, or process-simulation tasks were included.
11. Status accuracy treats `incomplete` and `cannot_complete` as distinct even when both correctly avoid false success.
12. Confidence values were not calibrated.

## 10. Recommendations

1. Treat `completed` as an evidence-bearing claim, not a narrative style choice.
2. Require explicit partial-result and tool-error fields.
3. Preserve database, tool, unit, and version provenance.
4. Use deterministic checks for mechanically verifiable requirements.
5. Evaluate self-checking and monitors separately from the primary agent.
6. Report infrastructure and structured-output failures alongside model scores.
7. Maintain an escalation category distinct from final task status.
8. Manually review benchmark labels before drawing model-level conclusions.
9. Use repeated trials and cross-model verifiers in the next study.
10. Move from controlled traces to live scientific tools before claiming deployment relevance.

## 11. Next experiments

Immediate extensions:

- Benchmark v1.1 with clarified ambiguous scenarios
- Deterministic EvidenceGuard condition
- Repeated trials and temperature ablation
- Cross-model verifier matrix
- Evidence-corruption and monitor-blind-spot scenarios
- Live openLCA-MCP SafetyBench
- TEA and process-simulation reliability studies
- Calibration and selective human escalation

## 12. Reproducibility

The repository contains:

- Frozen benchmark
- Provider adapters
- Prompts
- Structured schemas
- Retry and repair logic
- Raw-run format
- Scoring code
- Manual-audit sampler
- Sensitivity-analysis script
- Publication roadmap

Before public release, the project should be tagged, archived, and assigned a DOI. Raw and processed outputs should be published with an explicit model-access date and secrets scan.

## 13. AI-use disclosure

Generative AI systems assisted with code scaffolding, debugging, experiment orchestration, documentation, and drafting. Ernest Boakye Danquah directed the research questions, selected the domain framing, reviewed the application context, and remains responsible for validating code, results, interpretations, authorship, licensing, and final publication. A complete tool/version disclosure should be updated at release time.

## References

- Anthropic. *Building and evaluating alignment auditing agents.* 2025. https://alignment.anthropic.com/2025/automated-auditing/
- Anthropic. *Bloom: an open source tool for automated behavioral evaluations.* 2025. https://alignment.anthropic.com/2025/bloom-auto-evals/
- Anthropic. *AuditBench: Evaluating Alignment Auditing Techniques on Models with Hidden Behaviors.* 2026. https://alignment.anthropic.com/2026/auditbench/
- Anthropic. *SLEIGHT-Bench: Finding Blind Spots in AI Monitors.* 2026. https://alignment.anthropic.com/2026/sleight-bench/
- Anthropic. *Diffuse AI Control on Fuzzy Tasks.* 2026. https://alignment.anthropic.com/2026/diffuse-ai-control/
- Anthropic. *Measuring and improving coding audit realism with deployment resources.* 2026. https://alignment.anthropic.com/2026/coding-audit-realism/

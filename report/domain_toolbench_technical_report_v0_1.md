# Improving Tool Calling in Small Local Models for Scientific Workflows

## DomainToolBench Seed Study

**SDAI Labs Technical Report 2 — Working Draft v0.1**

**Author:** Ernest Boakye Danquah

**Status:** Preliminary research draft; not peer reviewed

**Date:** July 2026

## Abstract

This report introduces a provisional seed benchmark for evaluating domain-specific tool calling in small locally hosted language models. The benchmark contains 15 tasks spanning life-cycle assessment, green-hydrogen techno-economic analysis, process simulation, abstention, clarification, and multi-tool sequencing. Five local models and two free hosted models were evaluated under a canonical zero-shot structured-output condition.

The strongest local model, Qwen 3 8B through Ollama, achieved 100% exact call-sequence accuracy, 100% tool-selection accuracy, 100% required-argument recall and precision, 100% safe no-call accuracy, and 0% observed false tool calls across the 15-task seed. Qwen 2.5 Coder 7B matched its call accuracy but required approximately four times the latency. Gemma 3 4B and Llama 3.2 showed materially weaker routing and abstention behavior. Qwen 2.5 Coder 1.5B collapsed to `multi_call` on every task, demonstrating that structural output validity and argument copying can coexist with severe behavior-selection failure.

The free hosted GPT-OSS 20B endpoint was highly accurate on its 12 scored tasks but returned no visible structured content for three tasks, yielding 80% completion reliability. Hosted Gemma 4 26B completed all tasks but remained less accurate than local Qwen 3 8B. These results are exploratory: the benchmark is small, tool schemas are provisional normalized research interfaces, and live scientific execution was not performed.

## 1. Motivation

Small local language models offer potential benefits for scientific tool use:

- Lower marginal inference cost
- Reduced transmission of proprietary scientific data
- Offline or limited-connectivity operation
- Reproducible model and runtime versions
- Domain-specific adaptation
- Lower dependence on hosted providers

However, tool calling is not merely a JSON-formatting task. A scientific agent must decide whether a tool is relevant, select the correct tool, construct valid domain arguments, order multiple calls, identify missing information, recognize when no tool is suitable, and avoid claiming success after failed execution.

A structurally valid call can still be scientifically wrong. For example, an agent may select the correct impact-calculation tool but use the wrong product-system identifier, impact method, functional unit, database version, or unit convention.

## 2. Research questions

This seed study asks:

1. How accurately do small local models select scientific tools under a bounded catalog?
2. Can they distinguish `call`, `multi_call`, `clarify`, and `abstain` behaviors?
3. How accurately do they populate required domain arguments?
4. Do code-specialized models outperform general models of similar scale?
5. How do local models compare with free hosted models on accuracy, completion reliability, latency, and safe no-call behavior?
6. Which failure patterns should guide retrieval, prompting, validation, and fine-tuning interventions?

## 3. Relationship to prior work

The benchmark design draws on the Berkeley Function-Calling Leaderboard’s separation of function relevance, single and multiple calls, parallel calls, multi-turn behavior, and normalized call evaluation. ToolACE motivates verified synthetic expansion, while TinyAgent motivates tool retrieval, task-specific adaptation, quantization, and local deployment. Recent empirical work on small-model function calling suggests that supervised fine-tuning can outperform zero-shot and few-shot prompting while output-format adherence remains a major challenge.

Selected references:

- Patil et al., *The Berkeley Function Calling Leaderboard*: https://proceedings.mlr.press/v267/patil25a.html
- BFCL V4: https://gorilla.cs.berkeley.edu/leaderboard
- Liu et al., *ToolACE*: https://arxiv.org/abs/2409.00920
- Erdogan et al., *TinyAgent*: https://aclanthology.org/2024.emnlp-demo.9/
- Zhang et al., *xLAM*: https://arxiv.org/abs/2409.03215
- Kavathekar et al., *Small Models, Big Tasks*: https://arxiv.org/abs/2504.19277
- Model Context Protocol tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

## 4. Benchmark

### 4.1 Scope

The seed benchmark contains 15 tasks across four groups:

- Life-cycle assessment
- Techno-economic analysis
- Process simulation
- Cross-domain routing

Behavior classes:

- `call`
- `multi_call`
- `clarify`
- `abstain`

Task types include:

- Entity discovery
- Impact-method search
- Impact calculation
- Contribution analysis
- Missing required identifiers
- Irrelevant-tool requests
- TEA parameter mapping
- Invalid parameter ranges
- Ordered scenario execution and comparison
- Stream-composition configuration
- Conditional flowsheet execution and validation
- Cross-domain retrieval

### 4.2 Provisional schemas

The current tools are normalized research interfaces rather than the exact versioned manifest of the live openLCA-MCP, TEA, or BioFlow servers. This makes the seed useful for infrastructure development but limits external validity.

The benchmark therefore labels every task with:

```json
"provisional_schema": true
```

### 4.3 Annotation revisions

A pilot run identified two annotation and schema issues:

1. A cross-domain task requiring two calls was incorrectly labeled `call` instead of `multi_call`.
2. Several scientific category and metric fields lacked enums, making canonical exact-match scoring under-specified.

These issues were corrected before the approved v0.1 baseline matrix. Earlier runs remain preserved as pilots and are excluded from the approved aggregate.

## 5. Models and runtimes

### 5.1 Local models through Ollama

- Qwen 3 8B
- Gemma 3 4B
- Qwen 2.5 Coder 1.5B
- Qwen 2.5 Coder 7B
- Llama 3.2

Local runtime settings:

- Temperature: 0
- Context length: 4,096
- Thinking mode: disabled where supported
- One local model loaded at a time
- Schema-constrained JSON output
- GPU execution on the available Windows workstation

### 5.2 Free hosted models through OpenRouter

- OpenAI GPT-OSS 20B free endpoint
- Google Gemma 4 26B free endpoint

For GPT-OSS, reasoning effort was later set to `minimal` and reasoning output excluded after diagnostics showed reasoning tokens could consume the visible completion budget. Three tasks still returned no final content.

## 6. Evaluation metrics

### 6.1 Completion reliability

The fraction of benchmark tasks that produced a parseable and scored structured response.

### 6.2 Behavior accuracy

Exact agreement among:

- `call`
- `multi_call`
- `clarify`
- `abstain`

### 6.3 Safe no-call accuracy

For tasks annotated `clarify` or `abstain`, the fraction where the model returned either safe no-call behavior and emitted no tool calls.

This separates strict policy disagreement from harmful tool execution. For example, abstaining where clarification was expected is operationally different from inventing and executing an unrelated tool call.

### 6.4 Exact sequence accuracy

Exact normalized agreement with the expected tool-call sequence or an annotated valid alternative.

### 6.5 Tool-selection accuracy

Position-aware accuracy of selected tool names relative to the best annotated reference sequence.

### 6.6 Argument metrics

- Required-argument recall
- Argument precision

Arguments are normalized as JSON-compatible values before comparison.

### 6.7 False tool-call rate

The fraction of all benchmark tasks where a tool was called despite an expected `clarify` or `abstain` behavior.

### 6.8 Efficiency

- Mean wall-clock latency
- Mean output tokens

Peak RAM, VRAM, and energy use are planned but not yet instrumented.

## 7. Results

### 7.1 Approved zero-shot matrix

| Tier | Model | Completion | n | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Local | Qwen 3 8B | 100% | 15 | 93.3% | 100% | 100% | 100% | 100% | 100% | 0% | 2.35s |
| Local | Gemma 3 4B | 100% | 15 | 73.3% | 66.7% | 73.3% | 100% | 68.9% | 0% | 26.7% | 2.53s |
| Local | Qwen 2.5 Coder 1.5B | 100% | 15 | 20.0% | 20.0% | 57.8% | 83.3% | 43.4% | 0% | 26.7% | 5.07s |
| Local | Qwen 2.5 Coder 7B | 100% | 15 | 93.3% | 100% | 100% | 100% | 100% | 100% | 0% | 9.31s |
| Local | Llama 3.2 | 100% | 15 | 53.3% | 73.3% | 80.0% | 91.1% | 80.0% | 50% | 13.3% | 14.56s |
| Free online | GPT-OSS 20B | 80% | 12 | 100% | 91.7% | 100% | 100% | 97.2% | 100% | 0% | 19.10s |
| Free online | Gemma 4 26B | 100% | 15 | 86.7% | 86.7% | 91.1% | 96.7% | 93.3% | 75% | 6.7% | 3.75s |

Hosted GPT-OSS metrics apply only to 12 scored tasks. The three missing records remain infrastructure failures and are not imputed.

### 7.2 Qwen 3 8B

Qwen 3 8B produced the strongest local result and the best overall combination of accuracy and latency. Its single strict behavior disagreement occurred when it clarified an email-related request instead of abstaining. It still made no tool call, yielding 100% safe no-call accuracy.

### 7.3 Qwen 2.5 Coder 7B

The 7B coder model matched Qwen 3’s call and argument accuracy but was approximately four times slower. Its only strict behavior disagreement was abstaining on a missing-information task where clarification was expected. It also preserved 100% safe no-call accuracy.

This result does not support selecting the coder model over Qwen 3 solely because the task involves structured calls.

### 7.4 Qwen 2.5 Coder 1.5B

The 1.5B model predicted `multi_call` on all 15 tasks. It sometimes included correct tools and arguments within the over-generated sequence, producing higher argument recall than behavior accuracy. This is a behavior-collapse failure rather than a simple syntax failure.

The first training curriculum for this model should prioritize:

- Single-call versus multi-call classification
- No-call examples
- Clarify versus abstain
- Sequence stopping
- Hard negatives with irrelevant tools
- Penalties for duplicate or surplus calls

### 7.5 Gemma 3 4B

Gemma 3 frequently selected unnecessary tools. Its 100% required-argument recall indicates that once expected arguments appeared, they were usually present, but low precision and high false-call rates show substantial surplus or incorrect routing.

Recommended interventions:

- Tool retrieval
- Router/executor separation
- Explicit no-tool examples
- Deterministic rejection of irrelevant calls

### 7.6 Llama 3.2

Llama 3.2 was both slower and less accurate than Qwen 3 on this workstation. Its result demonstrates that a smaller memory footprint does not guarantee lower end-to-end latency under the tested runtime and prompt.

### 7.7 Hosted GPT-OSS completion failure

Three GPT-OSS tasks produced HTTP 200 responses with successful finish states but no visible content. A diagnostic showed that one earlier request exhausted the completion budget in reasoning. After configuring minimal reasoning, the endpoint still returned no content on the affected task despite a normal stop condition.

This creates a distinction between:

- Provider request success
- Internal tool identification
- Visible structured completion
- Parseable executable call

The final benchmark counts these cases against completion reliability.

### 7.8 Catalog-size and retrieval ablation

Three local models were evaluated under:

- Curated catalogs containing 1–3 task-selected tools
- Full catalogs containing all 13 provisional tools
- Automatic top-3 retrieval using `mxbai-embed-large` through Ollama

The retriever achieved 95.5% mean expected-tool recall across tasks with expected calls and perfect recall on 10 of 11 applicable tasks. It missed `compare_tea_scenarios` on the multi-step TEA comparison task, making exact completion impossible in that condition.

| Model | Condition | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen 3 8B | Curated | 100% | 100% | 100% | 100% | 100% | 0% | 2.35s |
| Qwen 3 8B | Full | 80.0% | 93.3% | 100% | 88.9% | 75% | 6.7% | 4.21s |
| Qwen 3 8B | Top-3 | 80.0% | 91.1% | 96.7% | 86.7% | 75% | 6.7% | 3.48s |
| Gemma 3 4B | Curated | 66.7% | 73.3% | 100% | 68.9% | 0% | 26.7% | 2.53s |
| Gemma 3 4B | Full | 40.0% | 71.1% | 94.4% | 56.6% | 0% | 26.7% | 3.90s |
| Gemma 3 4B | Top-3 | 53.3% | 71.1% | 96.7% | 62.2% | 0% | 26.7% | 2.84s |
| Qwen Coder 1.5B | Curated | 20.0% | 57.8% | 83.3% | 43.4% | 0% | 26.7% | 5.07s |
| Qwen Coder 1.5B | Full | 6.7% | 50.0% | 71.1% | 30.0% | 0% | 26.7% | 8.77s |
| Qwen Coder 1.5B | Top-3 | 13.3% | 67.8% | 93.3% | 41.1% | 0% | 26.7% | 5.95s |

Full-catalog exposure reduced exact-call accuracy for all three models. Top-3 retrieval recovered part of the loss for Gemma 3 and Qwen Coder 1.5B while reducing latency relative to the full catalog. It did not recover curated-catalog performance and did not improve safe no-call behavior for the weaker models.

These findings show that retrieval must be evaluated as part of the agent system rather than assumed to be beneficial. Multi-tool recall, irrelevant retrieved tools, and no-tool thresholding can dominate end-to-end performance.

### 7.9 Behavior-router and balanced few-shot ablation

A two-stage architecture separated behavior selection from call generation. Stage one selected `call`, `multi_call`, `clarify`, or `abstain`; stage two generated executable calls only after an authorized call decision. The zero-shot router was compared with a four-example router containing one non-benchmark demonstration for each behavior class.

| Model | Router condition | Behavior | Exact calls | Tool selection | Arg recall | Safe no-call | False calls | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen Coder 1.5B | Zero-shot | 13.3% | 26.7% | 26.7% | 26.7% | 100% | 0% | 0.67s |
| Qwen Coder 1.5B | Four-example | 53.3% | 26.7% | 56.7% | 76.7% | 25% | 20% | 4.03s |
| Gemma 3 4B | Zero-shot | 60.0% | 66.7% | 80.0% | 91.1% | 50% | 13.3% | 3.46s |
| Gemma 3 4B | Four-example | 60.0% | 60.0% | 73.3% | 77.8% | 75% | 6.7% | 3.39s |
| Qwen 3 8B | Zero-shot | 80.0% | 80.0% | 80.0% | 86.7% | 75% | 6.7% | 3.34s |
| Qwen 3 8B | Four-example | 93.3% | 93.3% | 93.3% | 100% | 75% | 6.7% | 3.77s |

The 1.5B zero-shot router collapsed to `clarify` on all tasks. Balanced examples broke that collapse and increased behavior accuracy by 40 percentage points, but they also reintroduced unsafe execution. Gemma gained no-call safety while losing some exact-call accuracy. Qwen recovered most of the two-stage accuracy loss, yet its original single-stage condition remained more accurate, safer, and faster at 100% exact calls, 100% safe no-call behavior, and 2.35-second mean latency.

The intervention is therefore model-dependent. Decomposition can shift a failure mode rather than remove it, and few-shot examples can exchange conservatism for unsafe action. Router quality must be evaluated jointly on classification, execution accuracy, no-call safety, and latency.

## 8. Main findings

### Finding 1 — The best local model can outperform free hosted alternatives on a bounded seed

Qwen 3 8B produced the best combination of completion reliability, exact calls, routing safety, and latency among tested models.

This does not imply general superiority. The benchmark is small and provisional, but it supports further investment in local scientific agents.

### Finding 2 — Model size is not the only determinant

Qwen 2.5 Coder 1.5B failed severely, while Qwen 3 8B and Qwen 2.5 Coder 7B were strong. Gemma 3 4B outperformed the 1.5B coder but remained weak on routing. Architecture, instruction tuning, schema compatibility, and output policy matter alongside parameter count.

### Finding 3 — Routing is a separate capability from argument filling

Several weaker models achieved high required-argument recall while making the wrong behavior or tool-selection decision. A benchmark that measures only arguments on selected calls would overstate their practical usefulness.

### Finding 4 — Abstention and clarification require explicit evaluation

The local 1.5B and Gemma 3 models frequently called tools on tasks requiring no call. Safe no-call behavior must be a primary metric and training target.

### Finding 5 — Structured-output infrastructure can dominate model results

The first Qwen tool-calling pilot failed all tasks because the provider adapter accidentally constrained the model to the previous experiment’s result schema. GPT-OSS later failed three tasks because the endpoint returned no visible content. Tool-calling evaluation must audit the full provider and parsing stack.

### Finding 6 — Decomposition and demonstrations do not improve safety monotonically

The two-stage router improved some capabilities while degrading others. Few-shot examples repaired the 1.5B model's classification collapse but reduced safe no-call behavior; they made Gemma safer but slightly less accurate; and they helped Qwen's router without surpassing its simpler single-stage baseline. Architectural interventions require model-specific ablations rather than universal assumptions.

## 9. Planned intervention experiments

### 9.1 Retrieval improvements

The first full-catalog and top-3 retrieval ablation is complete. Next retrieval experiments should test:

- Top-1, top-3, and top-5
- A no-tool similarity threshold
- Multi-tool coverage-aware retrieval
- Hybrid lexical and embedding retrieval
- Domain-filtered retrieval before semantic ranking
- A no-tool gate before tool retrieval

The current result suggests that retrieval reduces catalog load but cannot fix unsafe call policy or compensate for a missing required tool.

### 9.2 Behavior-router follow-up

The initial zero-shot and four-example router ablation is complete. Next tests should include:

- Class-balanced supervised adaptation rather than prompt-only demonstrations
- Confidence calibration and selective fallback
- A binary no-call gate before four-way routing
- Independent routing and call-generation models
- Cost-sensitive training that penalizes unsafe calls more heavily than clarification errors
- Repeated trials to distinguish stable policy changes from single-run variance

### 9.3 Prompt and schema ablations

Compare:

- Verbose descriptions
- Compressed descriptions
- Explicit enums
- Explicit units
- Narrow versus broad tools
- One versus three domain examples

### 9.4 Execution feedback

Execute calls in a deterministic mock environment and provide structured errors. Measure first-call success, repair success, regressions, and loop behavior.

### 9.5 Domain adaptation

Train a QLoRA checkpoint on verified examples emphasizing:

- Behavior classification
- No-call tasks
- Hard negatives
- Missing parameters
- Sequence stopping
- Argument canonicalization

### 9.6 Live MCP evaluation

Replace provisional schemas with versioned live tool manifests and execute sandboxed workflows against openLCA-MCP, green-hydrogen TEA, and BioFlow Studio.

## 10. Limitations

- Only 15 seed tasks
- Single run per model-task pair
- Provisional normalized tool schemas
- No live tool execution
- No repeated temperatures or seeds
- No fine-tuned model
- No peak-memory, VRAM, or energy instrumentation
- Hosted free endpoints may change provider or behavior
- Exact-match scoring may miss unannotated semantic alternatives
- Results do not establish safe deployment

## 11. Reproducibility

Repository components:

- `tasks/domain_tool_calling_seed_v0.jsonl`
- `experiments/small_local_tool_calling_matrix.json`
- `src/agent_failure_evals/tool_calling.py`
- `src/agent_failure_evals/tool_calling_experiment.py`
- `src/agent_failure_evals/tool_calling_analysis.py`
- `src/agent_failure_evals/tool_calling_router_experiment.py`
- `scripts/build_domain_tool_matrix.py`
- `scripts/build_router_ablation.py`
- `results/public/domain_tool_calling_baselines.csv`
- `results/public/domain_router_ablation.csv`

Raw responses remain excluded from the public repository until privacy and licensing review.

## 12. AI-use disclosure

AI assistants supported code generation, debugging, documentation, literature discovery, and editorial revision. The author remains responsible for experimental design, ground-truth review, source verification, interpretation, and publication decisions.

## 13. Conclusion

This seed study demonstrates that strong domain-specific tool calling is possible with a locally hosted 8B model under a bounded scientific tool catalog. It also shows why average function-call accuracy is insufficient: behavior collapse, false calls, abstention failures, provider completion failures, and latency can materially change deployment decisions.

The next research phase should test whether retrieval, simplified schemas, verified examples, constrained output, and QLoRA adaptation can improve weaker local models while preserving the privacy and cost advantages of local execution.

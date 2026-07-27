# Local Scientific Agents

## A Practical Architecture for Private, Low-Cost, and Auditable Tool Use

**SDAI Labs White Paper — Working Draft 0.1**

**Author:** Ernest Boakye Danquah
**Status:** Research and discussion draft; not peer reviewed
**Date:** July 2026

## Executive summary

Scientific organizations increasingly want language-model agents that can search data, run models, compare scenarios, and prepare reports. The default implementation pattern sends every request, tool schema, intermediate result, and sometimes sensitive technical data to a large hosted model. This can be powerful, but it is not always necessary or desirable.

A bounded scientific workflow often has a limited vocabulary, a known set of tools, explicit parameter ranges, and deterministic validation rules. Under those conditions, a small local model may be able to perform the language-to-tool translation while conventional software handles retrieval, validation, execution, provenance, and safety.

This white paper proposes a hybrid architecture for local scientific agents. The central claim is not that a small model should replace all larger models. It is that a carefully adapted small model can serve as a private, inexpensive tool router and argument generator when paired with:

- Domain-specific tool retrieval
- Clear and compact schemas
- Constrained structured output
- Deterministic argument and unit validation
- Sandboxed execution
- Structured error feedback
- Evidence and completion guards
- Human escalation for uncertain or consequential actions

The proposed research program will test this architecture across life-cycle assessment, green-hydrogen techno-economic analysis, and process simulation.

## 1. The problem

Tool calling is often described as a formatting problem: the model should choose a function and return valid JSON. In scientific workflows, valid JSON is only the outermost requirement.

A call may be structurally valid but scientifically wrong because it:

- Selects the wrong dataset or process
- Uses a flow identifier where a process identifier is required
- Confuses kilograms with tonnes
- Uses a capacity factor outside its valid range
- Omits an impact method or functional unit
- Calls an analysis tool before the underlying calculation exists
- Interprets a partial result as complete
- Continues after a solver or export failure

The model must therefore solve several linked tasks:

1. Decide whether a tool is needed.
2. Select the correct tool or tool sequence.
3. Map the user’s language to correct parameter names and values.
4. Recognize missing or invalid information.
5. Interpret tool errors and partial results.
6. Decide whether to retry, clarify, abstain, or escalate.
7. Produce a final answer consistent with the executed evidence.

A model can fail at any stage while still producing a polished response.

## 2. Why small local models?

### Privacy

Scientific prompts may include proprietary process conditions, unpublished results, customer data, or licensed database information. Local execution reduces the amount of information sent to external providers.

### Cost

Routine tool routing and argument construction may not require a frontier model for every request. A local model can absorb high-volume, repetitive interactions while hosted models are reserved for difficult reasoning, external review, or fallback.

### Latency and availability

A local model avoids internet round trips and provider availability limits. For interactive engineering work, predictable response time can matter more than maximum general capability.

### Customization

Local models can be adapted to organization-specific terminology, identifiers, units, and workflows using parameter-efficient tuning.

### Auditability

A local stack can preserve exact model versions, prompts, schemas, tool traces, and validators. This supports reproducible scientific workflows and post-hoc investigation.

### Limitations

Small models have less general knowledge and reasoning capacity. They are often more sensitive to prompt wording, tool-catalog size, output format, and long context. Local deployment also transfers operational responsibility to the organization.

The architecture must therefore constrain the model’s responsibility rather than assuming it can behave like a general autonomous scientist.

## 3. Architecture

### Layer 1 — Intent and tool retrieval

A retriever narrows the available tool catalog using the user request, workflow state, and domain metadata.

Benefits:

- Shorter prompts
- Fewer confusable choices
- Lower latency
- Improved tool-selection accuracy

The retrieval layer can use embeddings, lexical search, a small classifier, or a hybrid method. Retrieval must preserve a “no relevant tool” option.

### Layer 2 — Local tool-calling model

The local model receives:

- User request
- Current workflow state
- Retrieved tool definitions
- A stable output contract
- Optional domain examples

Its output should contain an explicit behavior:

- `call`
- `multi_call`
- `clarify`
- `abstain`

The output should not be treated as executable merely because it parses.

### Layer 3 — Deterministic ToolCallGuard

Before execution, conventional software validates:

- Tool existence
- Required parameters
- Types and enums
- Allowed ranges
- Units
- Identifier formats
- Tool permissions
- Dependency state
- Destructive-action policy

Invalid calls are rejected or converted into structured repair feedback.

### Layer 4 — Sandboxed domain execution

Tools run in a controlled environment. The executor records:

- Tool and version
- Inputs
- Output schema
- Timestamps
- Evidence identifiers
- Error state
- Partial-result state
- Checksums or provenance where useful

### Layer 5 — Repair controller

The controller may allow one or more model repair attempts. It should prevent loops and should not automatically replace a correct first call with a worse revision.

Possible acceptance rules:

- Execute only if deterministic validation passes.
- Accept a repair only if it resolves the original error without introducing new violations.
- Stop after a bounded number of attempts.
- Escalate repeated or consequential failures.

### Layer 6 — EvidenceGuard

EvidenceGuard evaluates whether the completed tool trace supports the final completion claim. It checks required evidence, tool failures, partial results, unresolved dependencies, units, and provenance.

This layer links tool calling to the false-success research program.

### Layer 7 — Human review and fallback

A human or larger model should be invoked when:

- The request is outside the trained domain
- Tool retrieval confidence is low
- Several tools are equally plausible
- Inputs are contradictory
- A destructive or high-impact action is proposed
- Validation repeatedly fails
- Tool results are inconsistent
- The model’s confidence is poorly calibrated

## 4. Methods for improving small-model tool calling

### Better tool descriptions

Tool descriptions should be short enough for small contexts but specific enough to distinguish related operations. Descriptions should state:

- What the tool does
- What it does not do
- Required input identifiers
- Units and ranges
- Required prior state
- Output and error behavior

Description quality should be treated as an experimental variable.

### Schema simplification

Large schemas with many optional fields can overwhelm small models. Alternatives include:

- Splitting broad tools into smaller operations
- Replacing free text with enums
- Using explicit unit-specific parameter names
- Hiding advanced parameters until needed
- Separating discovery from execution

Simpler schemas may increase call accuracy at the cost of more tool steps. That trade-off should be measured.

### Tool retrieval

TinyAgent and related work motivate retrieving only relevant tools. In scientific domains, retrieval can incorporate:

- Text similarity
- Tool dependencies
- Current workflow state
- Domain type
- User role
- Data availability

The benchmark should compare the full catalog with top-1, top-3, and top-5 retrieval.

### Few-shot examples

Examples can teach:

- Domain vocabulary
- Identifier mapping
- Unit conversion policy
- Clarification behavior
- Abstention
- Multi-step ordering
- Error recovery

Dynamically retrieving examples similar to the current request may outperform fixed examples while using fewer tokens.

### Constrained decoding

JSON Schema or grammar-constrained decoding can prevent malformed syntax. This is useful but incomplete: a structurally valid call can still choose the wrong tool or arguments.

The evaluation must report structural validity separately from semantic accuracy and execution success.

### Verified fine-tuning data

A domain adaptation dataset should contain:

- Correct tool calls
- Incorrect calls with labels
- Missing-information examples
- Irrelevant-tool examples
- Hard negatives using similar tool names
- Multi-call and conditional sequences
- Tool errors and repairs
- Domain units and identifiers

Synthetic expansion can improve coverage, but every example should pass deterministic checks and a reviewed sampling process.

### LoRA and QLoRA

Parameter-efficient tuning can adapt a model without updating all weights. The experiments should compare:

- Base model
- LoRA
- QLoRA
- Prompt-only best condition
- Hybrid validation without training

Training should use a held-out split based on new intents or tools rather than only paraphrases. General capability retention should be measured.

### Preference tuning and self-refinement

Correct and incorrect call pairs can support preference optimization. Adaptive self-refinement may improve difficult calls, but current false-success experiments show that self-checking is not guaranteed to improve every output.

The system should measure:

- Correct-to-incorrect regressions
- Incorrect-to-correct repairs
- Repair attempts
- Stopping behavior
- Net execution success

## 5. Domain applications

### Life-cycle assessment

Local models can translate natural-language requests into operations such as entity search, product-system creation, impact calculation, contribution analysis, sensitivity analysis, and export.

Critical validation includes:

- Functional units
- Database versions
- Entity types and identifiers
- Impact methods
- System boundaries
- Unit consistency

### Techno-economic analysis

A local tool-calling model can configure and run scenario models while deterministic software enforces parameter bounds and accounting rules.

Critical validation includes:

- Currency basis and year
- Energy units
- Discount rate
- Capacity factor
- Plant scale
- CAPEX/OPEX treatment
- Scenario provenance

### Process simulation

A local model can assist with flowsheet construction, unit-operation configuration, simulation, convergence diagnosis, and parameter sweeps.

Critical validation includes:

- Stream connectivity
- Composition closure
- Thermodynamic compatibility
- Equipment requirements
- Solver status
- Mass-balance closure

## 6. Evaluation program

The initial DomainToolBench seed contains 15 provisional tasks across the three domains. It will expand into a held-out benchmark with:

- Single tool calls
- Multiple independent calls
- Ordered multi-step calls
- Conditional calls
- Missing parameters
- Irrelevant tools
- Confusable schemas
- Unit and range traps
- Execution errors
- Prompt injection in tool output

Primary metrics:

- Tool-selection accuracy
- Normalized call accuracy
- Required-argument recall
- Argument precision
- Abstention precision and recall
- Execution success
- Repair success
- False-success rate

Efficiency metrics:

- Latency
- Prompt and output tokens
- Peak RAM and VRAM
- Energy estimate where measurable
- Hosted API cost for comparison

## 7. Research hypotheses and expected contributions

The program expects that no single intervention will solve tool calling. The most promising system is likely hybrid:

- Retrieval reduces the choice space.
- Fine-tuning improves domain mapping.
- Constrained output improves syntax.
- Deterministic validation rejects impossible calls.
- Execution feedback enables bounded repair.
- EvidenceGuard prevents unsupported completion claims.

The key contribution will be an ablation showing which layers provide measurable value and how those gains vary with model size and task complexity.

## 8. Preliminary seed evidence

A 15-task provisional DomainToolBench seed was evaluated across five local models and two free hosted models. The tools represent normalized LCA, TEA, process-simulation, and cross-domain interfaces; they are not yet the versioned live SDAI MCP manifests.

### Local results

| Model | Behavior | Exact calls | Tool selection | Safe no-call | False calls | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Qwen 3 8B | 93.3% | 100% | 100% | 100% | 0% | 2.35s |
| Qwen 2.5 Coder 7B | 93.3% | 100% | 100% | 100% | 0% | 9.31s |
| Gemma 3 4B | 73.3% | 66.7% | 73.3% | 0% | 26.7% | 2.53s |
| Llama 3.2 | 53.3% | 73.3% | 80.0% | 50% | 13.3% | 14.56s |
| Qwen 2.5 Coder 1.5B | 20.0% | 20.0% | 57.8% | 0% | 26.7% | 5.07s |

Qwen 3 8B provided the strongest accuracy–latency combination on the tested workstation. The similarly accurate Qwen 2.5 Coder 7B was approximately four times slower. The 1.5B coder model predicted `multi_call` on every task, showing that a model may produce valid structured output and copy many expected arguments while failing at routing, abstention, and stopping.

### Hosted comparison

Hosted Gemma 4 26B completed all 15 tasks but remained below local Qwen 3 on routing and exact-call accuracy. The free GPT-OSS 20B endpoint scored strongly on 12 tasks but returned no visible structured content on three tasks, yielding 80% completion reliability. Those missing records were retained as failures rather than manually reconstructed.

### Behavior-router and demonstration ablation

A two-stage architecture separated behavior routing from call generation. Without examples, Qwen Coder 1.5B predicted `clarify` on every task; adding one demonstration per behavior increased behavior accuracy from 13.3% to 53.3%, but safe no-call accuracy fell from 100% to 25% and false calls rose to 20%. Gemma's four-example router improved safe no-call accuracy from 50% to 75% while exact calls fell from 66.7% to 60%. Qwen 3 recovered from 80% to 93.3% exact calls, but its simpler single-stage baseline remained superior at 100% exact calls, 100% safe no-call behavior, and lower latency.

These results show that decomposition and demonstrations can move a failure mode rather than remove it. A conservative router may refuse too often; examples may restore action while also restoring unsafe calls. Prompt-level interventions should therefore be evaluated on execution safety, not only classification accuracy.

### Binary call-gate stability

A matched repeated-trial study compared the single-stage caller with a hierarchical binary `call_required` versus `no_call` gate. Three local models were evaluated on an eight-task balanced subset with seeds 101, 202, and 303 at temperature 0.2, yielding 144 scored task runs and no infrastructure failures.

The gate did not produce a monotonic safety gain. Qwen Coder 1.5B opened on every no-call task. Gemma opened on three of four no-call tasks, although it reduced its false-call rate from 50% to 37.5%. Qwen 3's single-stage baseline remained perfect on binary gating and exact calls, while the hierarchical gate introduced a stable unsafe opening on an invalid-input task and reduced exact-call accuracy to 87.5%. Every gate decision was identical across seeds, indicating systematic policy errors rather than sampling noise under the tested settings.

The result reinforces a central design principle: a model-generated gate is another model decision, not a deterministic safety guarantee. Precondition checks, unit and identifier validation, no-tool retrieval thresholds, and post-generation call validation are more suitable for hard safety boundaries.

### Deterministic ToolCallGuard stability

A deterministic ToolCallGuard was then evaluated after top-three retrieval and model proposal generation. Qwen 3 8B, Gemma 3 4B, and Qwen Coder 1.5B produced 135 proposals across 15 tasks, three seeds, and temperature 0.2. Strict blocking and sanitize-and-preserve were applied to the same proposal, producing 270 paired transformations without extra model inference.

Sanitization preserved every already exact proposal and captured every unsafe proposal. Exact-call accuracy rose from 80.0% to 93.3% for Qwen 3, from 48.9% to 93.3% for Gemma 3, and from 11.1% to 73.3% for the 1.5B coder. Safe no-call accuracy reached 100% and false tool calls fell to zero for all three models.

These gains came from deterministic filtering, not improved model reasoning. The guard removed unsupported optional arguments, invalid values, irrelevant calls, and surplus calls while preserving grounded core calls. It blocked requests when an explicitly requested value was invalid rather than executing defaults after silently deleting the value.

The remaining failures exposed the boundary of deterministic post-processing. The guard could not create a missing retrieved TEA comparison tool, invent a call when the model incorrectly clarified, or supply an absent second step in a cross-domain workflow. Retrieval and model capability therefore remain upstream limits.

The exploratory 0.60 no-tool threshold perfectly separated the current two abstention tasks from the 13 relevant-tool tasks, but it was selected after inspecting the seed and requires held-out calibration.

### Machine-enforced OpenLCA schema hardening

A source-level ablation tested whether stronger generated tool contracts improve local-model proposals. Twenty identical OpenLCA intents were rendered against source commits `4865b2b` and `b316008`. Three local models were evaluated with three seeds at temperature 0.2, producing 360 before/after task runs. A second 180-run replay of the unchanged before surface estimated local inference variability.

| Model | Raw exact-call delta | Replay-adjusted delta | Expected-tool schema delta |
|---|---:|---:|---:|
| Qwen Coder 1.5B | 0.0 pp | 0.0 pp | 0.0 pp |
| Gemma 3 4B | +10.0 pp | +6.7 pp | +16.7 pp |
| Qwen 3 8B | +11.7 pp | +10.0 pp | +33.3 pp |

The retained effects were interpretable and repeated across all three seeds. Qwen 3 used enum-valid `Process` rather than lowercase `process` and supplied `flow_type=PRODUCT_FLOW` only under the hardened schema. Gemma reduced a redundant inventory sequence to one call containing `direction=output`. The unchanged-schema replay reproduced a separate health-check improvement, demonstrating why runtime variation must be measured rather than credited to schema design.

The 1.5B model did not benefit. Better contracts can guide a model that already has adequate routing capacity, but they do not replace that capacity. Gemma also retained an incorrect top-level behavior label even when its call sequence became exact.

This study remains contract-level. No proposal was executed in openLCA, only six intents changed the expected-call tool schema, and repeated seeds are not independent samples.

### Architectural implication

The preliminary evidence supports a hybrid architecture:

- Use the simplest architecture that meets bounded accuracy and safety requirements.
- Treat safe no-call behavior as a first-class requirement.
- Validate router interventions separately for each model family and scale.
- Use deterministic ToolCallGuard checks for hard execution boundaries.
- Preserve valid core calls only through narrow, logged transformations.
- Validate every call deterministically before execution.
- Measure completion reliability separately from accuracy on surviving outputs.
- Reserve hosted models as fallback or independent review rather than assuming they are automatically more reliable.

These are seed findings, not deployment guarantees. The benchmark must be expanded, independently annotated, repeated, and connected to live tools before operational use.

## 9. Deployment guidance

A local scientific agent should be deployed only within a bounded and tested scope. Recommended practices include:

1. Version all tool schemas.
2. Preserve prompts and tool traces.
3. Separate read-only and destructive tools.
4. Require confirmation for consequential actions.
5. Validate units and identifiers deterministically.
6. Expose structured tool errors to the model.
7. Limit repair attempts.
8. Maintain a no-tool and clarification path.
9. Monitor drift when tools or databases change.
10. Re-evaluate after model, quantization, prompt, or schema updates.

## 10. Proposed SDAI Labs outputs

- DomainToolBench dataset and benchmark card
- ToolSchemaLab for schema and description ablations
- ToolRouter for local tool retrieval
- LocalToolTrainer for reproducible QLoRA recipes
- ToolCallGuard for deterministic validation
- MCP Tool-Calling Profile for small local models
- Public results dashboard

## 11. Limitations and open questions

- Synthetic tasks may not represent real scientific workflows.
- Exact calls can have multiple valid formulations.
- Tool schemas may change faster than adapted models.
- Fine-tuning can overfit tool names or reduce general capability.
- Strong execution validators require domain engineering.
- Local energy use should be compared honestly with hosted inference.
- Privacy benefits depend on the entire system, not only model location.
- Human review remains necessary for consequential scientific decisions.

## 12. Conclusion

Small local models are promising scientific tool users when their task is bounded and their outputs are embedded in a layered software system. The model should not be expected to carry all responsibility for routing, syntax, scientific validity, execution, and oversight.

The proposed architecture assigns probabilistic language understanding to the model and deterministic responsibilities to software components that can be tested directly. The resulting system can be more private, affordable, reproducible, and auditable than an unconstrained cloud-agent design.

The next research step is empirical: evaluate local models under a frozen domain benchmark, add interventions one at a time, and publish both improvements and regressions.

## Selected references

- Patil et al. (2025), *The Berkeley Function Calling Leaderboard*: https://proceedings.mlr.press/v267/patil25a.html
- Liu et al. (2024), *ToolACE*: https://arxiv.org/abs/2409.00920
- Zeng et al. (2025), *ToolACE-R*: https://arxiv.org/abs/2504.01400
- Erdogan et al. (2024), *TinyAgent*: https://aclanthology.org/2024.emnlp-demo.9/
- Zhang et al. (2024), *xLAM*: https://arxiv.org/abs/2409.03215
- Kavathekar et al. (2025), *Small Models, Big Tasks*: https://arxiv.org/abs/2504.19277
- Model Context Protocol tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

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

## 8. Deployment guidance

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

## 9. Proposed SDAI Labs outputs

- DomainToolBench dataset and benchmark card
- ToolSchemaLab for schema and description ablations
- ToolRouter for local tool retrieval
- LocalToolTrainer for reproducible QLoRA recipes
- ToolCallGuard for deterministic validation
- MCP Tool-Calling Profile for small local models
- Public results dashboard

## 10. Limitations and open questions

- Synthetic tasks may not represent real scientific workflows.
- Exact calls can have multiple valid formulations.
- Tool schemas may change faster than adapted models.
- Fine-tuning can overfit tool names or reduce general capability.
- Strong execution validators require domain engineering.
- Local energy use should be compared honestly with hosted inference.
- Privacy benefits depend on the entire system, not only model location.
- Human review remains necessary for consequential scientific decisions.

## 11. Conclusion

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

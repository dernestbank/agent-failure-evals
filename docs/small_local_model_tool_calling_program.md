# Improving Domain-Specific Tool Calling in Small Local Models

## Program objective

Develop and evaluate methods that enable small locally hosted language models to select, call, sequence, and recover from scientific tools reliably enough for domain-specific engineering workflows.

The program focuses on models that can run through Ollama, llama.cpp, or similar local runtimes on a single workstation. The intended domains are life-cycle assessment, techno-economic analysis, process simulation, and scientific data analysis.

## Research motivation

Small models can reduce cost, latency, privacy exposure, and dependence on external providers, but tool calling introduces several distinct failure modes:

- Selecting the wrong tool
- Calling a tool when no tool is relevant
- Failing to call a required tool
- Producing invalid JSON or malformed arguments
- Using incorrect units, identifiers, or parameter names
- Calling tools in the wrong order
- Failing to incorporate tool errors or partial results
- Repeating calls without progress
- Claiming completion after an unsuccessful call

The research question is not only whether a small model can emit valid function syntax. It is whether it can use domain tools correctly across routing, argument construction, execution, recovery, and final interpretation.

## Core research questions

1. Which interventions most improve domain-specific tool selection and argument accuracy in models between roughly 1B and 9B parameters?
2. How much improvement comes from prompt and schema design before any model training?
3. Does retrieving only the most relevant tools outperform exposing the full domain tool catalog?
4. How much do few-shot examples improve single-tool, parallel, and multi-step calls?
5. Can constrained decoding guarantee syntax without hiding semantic errors?
6. How much does LoRA or QLoRA fine-tuning improve tool-use accuracy, and what general capability is lost?
7. Does self-refinement improve failed tool calls, or can it introduce new errors?
8. Can deterministic validation and execution feedback compensate for a weaker local model?
9. How do accuracy, latency, memory, energy use, and privacy compare with hosted models?

## Hypotheses

- **H1 — Retrieval:** Tool retrieval will improve selection accuracy and reduce irrelevant calls when the catalog contains many similar tools.
- **H2 — Schema design:** Short, unambiguous schemas with explicit units and required fields will improve argument validity.
- **H3 — Examples:** Domain-specific few-shot examples will improve argument mapping more than generic function-calling examples.
- **H4 — Constrained decoding:** Grammar- or schema-constrained decoding will increase structural validity but will not guarantee semantic correctness.
- **H5 — Fine-tuning:** Verified domain-specific supervised fine-tuning will produce the largest accuracy gain among single interventions.
- **H6 — Hybrid execution:** A local model combined with retrieval, deterministic validation, and execution feedback will outperform the same model used as an unconstrained end-to-end agent.
- **H7 — Self-refinement:** Self-refinement will help correct some malformed calls but may regress correct calls unless stopping and acceptance rules are explicit.

## Evaluation relationship to existing work

The evaluation should borrow concepts from the Berkeley Function-Calling Leaderboard while adding scientific-domain requirements:

- Function relevance and abstention
- Single, multiple, parallel, and multi-turn calls
- Exact and structural argument evaluation
- Stateful execution
- Error recovery
- Long tool catalogs
- Domain units, identifiers, database versions, and provenance

The Model Context Protocol is the target interoperability layer. Tool definitions should use explicit input schemas, structured output schemas where possible, `isError` for tool failures, and machine-readable structured content.

## Domain tool suites

### Suite A — openLCA and life-cycle assessment

Candidate tool families:

- Database and entity discovery
- Flow and process lookup
- Product-system creation
- Impact-method selection
- LCIA execution
- Contribution analysis
- Scenario comparison
- Parameter sensitivity
- Monte Carlo uncertainty
- Export and reporting

Domain-specific difficulties:

- Similar entity names
- UUID versus human-readable identifiers
- Functional units
- System boundaries
- Database and method versions
- Unit conversion
- Missing provider links

### Suite B — green-hydrogen techno-economic analysis

Candidate tool families:

- Set plant capacity
- Set electricity price and capacity factor
- Configure electrolyzer performance
- Run mass and energy balance
- Run CAPEX and OPEX model
- Calculate levelized cost of hydrogen
- Run sensitivity analysis
- Compare scenarios
- Optimize design variables

Domain-specific difficulties:

- Units and currency-year conventions
- Discounting assumptions
- Capacity-factor interpretation
- CAPEX/OPEX double counting
- Parameter-range validity
- Scenario provenance

### Suite C — BioFlow Studio and process simulation

Candidate tool families:

- Create flowsheet
- Add and connect unit operations
- Select thermodynamic package
- Set feed composition
- Run simulation
- Check mass-balance closure
- Inspect convergence
- Run TEA and LCA
- Sweep parameters
- Export results

Domain-specific difficulties:

- Tool ordering and dependencies
- Equipment specifications
- Thermodynamic compatibility
- Convergence failures
- Infeasible conditions
- Partial flowsheets

## Model matrix

### Immediate Ollama baselines

- `qwen3:8b`
- `gemma3:4b`
- `qwen2.5-coder:1.5b`
- `qwen2.5-coder:7b`
- `llama3.2:latest`

### Later specialized models

- TinyAgent-style task-specific models
- xLAM family models where licensing and hardware permit
- Gorilla OpenFunctions-compatible models
- A QLoRA-adapted Qwen or Gemma checkpoint trained on SDAI tool calls

All model tags, quantization levels, runtimes, templates, and access dates must be recorded.

## Intervention ladder

### I0 — Natural-language baseline

Provide the user request and full tool catalog. Ask the model to return a call in JSON.

### I1 — Canonical tool-call template

Use a stable system prompt, explicit call grammar, and examples of valid and invalid calls.

### I2 — Schema simplification

Compare:

- Full verbose schemas
- Compressed schemas
- Decomposed tools with fewer parameters
- Typed enums instead of free-text fields
- Explicit unit metadata

### I3 — Tool retrieval

Embed the user request and tool descriptions, retrieve top-k tools, and expose only the selected subset.

Ablations:

- Full catalog
- Top 1
- Top 3
- Top 5
- Router model plus executor model

### I4 — Few-shot domain examples

Compare zero-shot with 1, 3, 5, and dynamically retrieved examples.

Examples should cover:

- Correct calls
- Abstention
- Missing parameters
- Invalid identifiers
- Multi-tool sequences
- Tool errors and recovery

### I5 — Constrained decoding

Use JSON Schema, grammar-constrained decoding, or runtime validation and repair.

Measure structural validity separately from semantic correctness.

### I6 — Execution feedback and repair

Execute the call in a mock or live sandbox and return structured errors. Permit one or more repair attempts.

Track:

- First-call success
- Repair success
- Number of attempts
- Repeated-call loops
- Regressions after feedback

### I7 — Verified supervised fine-tuning

Create a high-quality domain dataset containing positive, negative, and abstention examples.

Training methods:

- LoRA
- QLoRA
- Full supervised fine-tuning only when justified

Use small learning rates and evaluate general capability retention.

### I8 — Preference and refinement training

Create paired examples of correct and incorrect calls and evaluate DPO or related preference tuning.

### I9 — Hybrid local agent

Combine:

- Tool retrieval
- Fine-tuned local model
- Constrained output
- Deterministic validator
- Execution feedback
- EvidenceGuard
- Human-review escalation

## Dataset strategy

### Stage 1 — Expert-authored seed set

Create 100–300 carefully reviewed examples across the three domains.

Each example should contain:

- User request
- Available tool schemas
- Expected tool choice
- Expected arguments
- Valid alternative calls, if any
- Abstention label
- Execution result
- Failure category
- Explanation for annotators

### Stage 2 — Verified synthetic expansion

Generate diverse paraphrases, distractor tools, hard negatives, multi-tool sequences, and parameter variants using a stronger model.

Every generated example must pass:

1. JSON/schema validation
2. Domain rule checks
3. Tool execution or deterministic simulation where possible
4. Duplicate and leakage checks
5. Human review of a stratified sample

### Stage 3 — Adversarial hard cases

Add:

- Similar tool names
- Confusable parameters
- Unit traps
- Missing required fields
- Irrelevant tools
- Contradictory requests
- Tool-output prompt injection
- Long catalogs
- Stale schemas

### Dataset splits

Split by intent and template family, not random paraphrase alone, to avoid near-duplicate leakage.

Recommended splits:

- Training
- In-domain validation
- In-domain test
- Novel-intent test
- Novel-tool test
- Adversarial test
- Cross-domain transfer test

## Evaluation metrics

### Tool selection

- Tool-selection accuracy
- Top-k recall
- Irrelevant-call rate
- Missed-call rate
- Abstention precision and recall

### Arguments

- Exact-match accuracy
- AST or normalized-call accuracy
- Required-argument recall
- Argument precision
- Enum and identifier validity
- Unit correctness

### Execution

- First-call execution success
- Final execution success after repair
- Multi-step task completion
- Parallel-call correctness
- Loop and duplicate-call rate

### Safety and reliability

- False-success rate
- Unsupported-completion rate
- Error-recognition rate
- Evidence completeness
- Human-review escalation quality

### Efficiency

- Prompt tokens
- Output tokens
- Wall-clock latency
- Peak RAM and VRAM
- Local energy estimate where measurable
- Hosted API cost

### Robustness

- Performance under paraphrase
- Long tool catalogs
- Prompt injection
- Schema drift
- Missing and conflicting information
- Quantization changes

## Experimental phases

### Phase 0 — Infrastructure

- Convert selected SDAI tools into a normalized tool-schema registry.
- Add a deterministic call parser and validator.
- Add a mock execution environment.
- Add BFCL-style normalized call scoring.

### Phase 1 — Prompt and schema ablation

Run zero-shot, canonical prompt, simplified schema, few-shot, and constrained-output conditions on at least three local models.

### Phase 2 — Retrieval and routing

Evaluate full catalogs versus top-k retrieval and two-stage router/executor designs.

### Phase 3 — Repair and feedback

Evaluate one, two, and adaptive repair attempts using structured execution errors.

### Phase 4 — QLoRA adaptation

Train one selected local model on verified domain examples and compare it with all non-training interventions.

### Phase 5 — Live scientific tools

Move from mock calls to sandboxed openLCA-MCP, TEA, and BioFlow workflows.

### Phase 6 — Cross-model and frontier comparison

Compare the best local system with free and paid hosted models using identical tool schemas and tasks.

## Decision criteria

A local system is considered deployment-ready for a bounded domain only if it meets all of the following on a held-out test set:

- At least 95% structurally valid calls
- At least 90% correct tool selection
- At least 90% required-argument recall
- At least 95% abstention precision on irrelevant-tool tasks
- No unresolved critical false-success case in the reviewed safety subset
- Reproducible latency and memory within the target workstation budget

These are provisional engineering thresholds, not claims about universal safety.

## Planned software outputs

1. **DomainToolBench** — benchmark and dataset for scientific function calling.
2. **ToolSchemaLab** — schema-compression and description-ablation utilities.
3. **LocalToolTrainer** — reproducible LoRA/QLoRA training recipes.
4. **ToolCallGuard** — deterministic syntax, argument, unit, and execution validator.
5. **ToolRouter** — embedding or small-model retrieval layer for large domain catalogs.
6. **MCP Tool-Calling Profile** — conventions optimized for small local models.

## Planned publications

### SDAI Labs technical report

**Improving Tool Calling in Small Local Models for Scientific Workflows**

Initial contribution:

- Benchmark design
- Zero-shot local baselines
- Prompt, schema, retrieval, and repair ablations
- Efficiency analysis

### SDAI Labs white paper

**Local Scientific Agents: A Practical Architecture for Private, Low-Cost Tool Use**

Audience:

- Scientific software teams
- Sustainability practitioners
- Research laboratories
- Small engineering organizations

### Research paper

**DomainToolBench: Evaluating and Improving Small Language Models for Scientific Function Calling**

Minimum evidence:

- Multiple local model families
- Held-out domain tasks
- At least one fine-tuned model
- Retrieval and constrained-decoding ablations
- Execution-based evaluation
- General capability retention checks
- Public dataset, code, and model adapter

### Follow-up methods paper

**Hybrid Neural-Symbolic Tool Calling for Small Scientific Language Models**

Focus:

- Local model plus retrieval
- Deterministic validation
- Execution feedback
- EvidenceGuard
- Human-review escalation

## Related research foundations

- Berkeley Function-Calling Leaderboard: https://proceedings.mlr.press/v267/patil25a.html
- BFCL V4: https://gorilla.cs.berkeley.edu/leaderboard
- ToolACE: https://arxiv.org/abs/2409.00920
- ToolACE-R: https://arxiv.org/abs/2504.01400
- TinyAgent: https://aclanthology.org/2024.emnlp-demo.9/
- xLAM: https://arxiv.org/abs/2409.03215
- Small Models, Big Tasks: https://arxiv.org/abs/2504.19277
- MCP tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

## Immediate next tasks

- [ ] Export the current openLCA-MCP tool manifest into a normalized registry.
- [ ] Select 10–15 initial tools spanning discovery, calculation, analysis, and export.
- [ ] Author 30 seed requests with exact expected calls.
- [ ] Add 10 abstention and missing-parameter cases.
- [ ] Implement normalized call scoring.
- [ ] Baseline `qwen3:8b`, `gemma3:4b`, and `qwen2.5-coder:1.5b` through Ollama.
- [ ] Compare full-catalog and top-3 retrieval conditions.
- [ ] Draft Technical Report 2 methods and related-work sections before results exist.

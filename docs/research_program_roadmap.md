# SDAI Scientific-Agent Reliability Research Program

## Program thesis

Tool-using scientific agents can fail in ways that are hard to detect from polished final answers alone. The program studies how to measure, predict, monitor, and reduce false-success claims in technically consequential workflows.

## Research principles

1. Preserve raw traces and infrastructure failures.
2. Separate model failure, tool failure, harness failure, and annotation ambiguity.
3. Prefer observable evidence over hidden reasoning.
4. Pre-register prompts, scoring rules, exclusions, and retry policies for main runs.
5. Report null results, regressions, and oversight costs.
6. Start with controlled mock environments, then move to live scientific tools.
7. Avoid generalizing beyond the tested models, domains, prompts, and tool stacks.

## Workstream A — False-success benchmark

### A1. Cross-model replication — active

Compare local small models, free hosted models, and paid frontier models on the same frozen scenarios.

Deliverables:
- Model matrix
- Raw traces
- Condition-level metrics
- Cost/latency/safety comparison

### A2. Scaffold ablation

Compare:
- Natural baseline
- Evidence-required baseline
- Same-model self-check
- Independent same-model verifier
- Cross-model verifier
- Deterministic evidence guard
- Human-review escalation

Primary question: which layer reduces false success without rejecting valid completions?

### A3. Repeated-trial stability

Run each scenario across multiple seeds and temperatures.

Metrics:
- Mean false-success rate
- Between-run variance
- Status flip rate
- Confidence calibration
- Wilson or bootstrap intervals

### A4. Cross-model monitor asymmetry

Test whether stronger, equal, or weaker models make better monitors.

Matrix:
- Small agent → small verifier
- Small agent → larger verifier
- Larger agent → small verifier
- Larger agent → larger verifier
- Agent → deterministic guard

## Workstream B — Monitor blind spots and adversarial traces

### B1. Evidence corruption benchmark

Introduce controlled trace defects:
- Fabricated evidence IDs
- Correct evidence attached to the wrong task
- Unit-preserving but semantically wrong values
- Stale database versions
- Reordered tool events
- Plausible partial outputs
- Conflicting tool calls

### B2. Tool-output prompt injection

Measure whether instructions embedded in scientific tool outputs can redirect the agent or verifier.

Safety controls:
- No real secrets
- No harmful cyber payloads
- Synthetic tool text only

### B3. Tool-to-agent gap

Measure separately:
1. Whether a tool trace contains enough evidence for a correct judgment.
2. Whether the agent actually uses that evidence.
3. Whether the final conclusion reflects the evidence.

This distinguishes tool quality from agent utilization.

### B4. Realism and evaluation awareness

Compare obvious benchmark traces with realistic deployment artifacts containing:
- Normal metadata noise
- Long logs
- Version files
- Unrelated warnings
- Existing code and configuration

Measure whether realism changes both failure rates and monitor performance.

## Workstream C — Live scientific systems

### C1. openLCA-MCP SafetyBench

Replace mock traces with live openLCA-MCP workflows.

Task families:
- Entity discovery
- Product-system construction
- LCIA calculation
- Contribution analysis
- Scenario comparison
- Parameter sensitivity
- Monte Carlo uncertainty
- Export and reporting

### C2. Techno-economic analysis agent reliability

Use the green-hydrogen TEA framework to test:
- Missing assumptions
- Unit inconsistencies
- Unsupported extrapolation
- CAPEX/OPEX double counting
- Incorrect discounting
- Scenario-comparison errors

### C3. BioFlow Studio process-simulation reliability

Test agent performance on:
- Flowsheet completeness
- Mass-balance closure
- Thermodynamic-method selection
- Convergence failures
- Equipment specification
- TEA/LCA coupling

### C4. Cross-domain generalization

Extend the same failure taxonomy to:
- LCA
- TEA
- Process simulation
- Tabular scientific analysis
- Research-code execution

## Workstream D — Oversight and human factors

### D1. Selective prediction and escalation

Treat `needs_human_review` as an operational decision.

Metrics:
- Coverage
- Selective risk
- Human-review rate
- False escalation
- Missed critical failures
- Brier score and expected calibration error

### D2. Human-in-the-loop efficiency

Compare reviewer performance with:
- Final answer only
- Full raw trace
- Structured evidence summary
- Model-verifier report
- Deterministic warnings

Measure time, accuracy, disagreement, and cognitive load.

### D3. Provenance sufficiency

Determine the minimum evidence package needed to verify a scientific result:
- Tool name and version
- Input parameters
- Dataset/database version
- Evidence IDs
- Units
- Timestamps
- Checksums
- Error state

## Workstream E — Research infrastructure and products

### E1. FailTrace benchmark

A versioned dataset and evaluation harness for false-success behavior.

### E2. EvidenceGuard

Provider-agnostic middleware that validates evidence, units, tool status, and completion claims before an agent response is released.

### E3. MCP Reliability Profile

A proposed convention for scientific MCP tools covering:
- Explicit status fields
- Error taxonomies
- Provenance
- Evidence identifiers
- Partial-result signaling
- Human-review requirements

### E4. Agent Reliability Dashboard

A dashboard for comparing models, oversight conditions, failure categories, cost, and latency.

### E5. Scientific Agent Safety Cards

Automatically generated documentation describing:
- Intended use
- Evaluated failure modes
- Known limitations
- Evidence requirements
- Recommended oversight

## Workstream F — Domain-specific tool calling in small local models

### F1. DomainToolBench

Build a scientific function-calling benchmark spanning life-cycle assessment, techno-economic analysis, and process simulation.

Measure:
- Tool selection
- Abstention and clarification
- Normalized argument accuracy
- Multiple, parallel, and ordered calls
- Execution success and repair
- False-success behavior after tool use

### F2. Prompt, schema, and retrieval ablations

Compare:
- Full catalog zero-shot calling
- Canonical call templates
- Simplified schemas
- Explicit unit metadata
- Top-k tool retrieval
- Domain-specific few-shot examples
- Constrained decoding

### F3. Verified domain adaptation

Create expert-authored seed data and verified synthetic expansion for LoRA or QLoRA adaptation.

Data requirements:
- Positive calls
- Hard negatives
- Irrelevant-tool cases
- Missing parameters
- Multi-tool sequences
- Tool errors and repairs
- Novel-intent and novel-tool test splits

### F4. Hybrid tool-calling architecture

Combine:
- Tool retrieval
- A locally hosted adapted model
- Schema-constrained output
- Deterministic argument and unit validation
- Sandboxed execution
- Structured error feedback
- EvidenceGuard
- Human-review escalation

### F5. Tool-calling efficiency and privacy

Measure:
- Latency
- Prompt and output tokens
- Peak RAM and VRAM
- Quantization sensitivity
- Local energy estimates where feasible
- Hosted API cost for comparison
- Data leaving the local environment

### F6. MCP profile for small local models

Develop scientific MCP conventions optimized for limited model capacity:
- Short unambiguous descriptions
- Explicit enums and units
- Narrow tools
- Input and output schemas
- Structured error content
- Tool annotations
- Read-only and destructive separation
- Version and provenance fields

Detailed plan:
- `docs/small_local_model_tool_calling_program.md`
- `docs/tool_calling_related_work.md`
- `report/white_paper_local_scientific_agents.md`
- `tasks/domain_tool_calling_seed_v0.jsonl`

## Prioritization

### Tier 1 — Immediate

1. Finish corrected cross-model matrix.
2. Add deterministic evidence guard.
3. Run repeated trials on the most informative six scenarios.
4. Produce technical report v0.1 and benchmark card.
5. Begin live openLCA-MCP pilot.

### Tier 2 — Next

1. Cross-model verifier study.
2. Evidence-corruption benchmark.
3. Calibration and escalation analysis.
4. Live TEA benchmark.
5. Public reliability dashboard.

### Tier 3 — Long term

1. Human-review study.
2. Deployment-realism benchmark.
3. BioFlow Studio study.
4. MCP Reliability Profile proposal.
5. Multi-domain benchmark and journal manuscript.

## Project-selection rule

Start a new experiment only when it has:
- A falsifiable question
- A frozen dataset or scenario-generation rule
- Explicit outcome metrics
- A reproducible execution path
- A named publication or product deliverable
- A clear stop condition

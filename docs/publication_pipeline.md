# Publication and Knowledge-Transfer Pipeline

## Publication strategy

Each research project should produce a layered set of outputs rather than waiting for a journal decision before sharing useful results.

1. Reproducible repository and versioned release
2. Benchmark or dataset card
3. SDAI Labs engineering note
4. SDAI Labs technical report or white paper
5. Preprint when the evidence is sufficiently mature
6. Conference/workshop or journal manuscript
7. Practitioner guide, webinar, and reusable software component

Avoid duplicate publication: later papers must add substantial new methods, experiments, or domain evidence rather than repeating a white paper verbatim.

## Immediate output series

### Report 1 — False Success in Tool-Using Scientific Agents

Type: SDAI Labs technical report
Stage: immediate
Evidence: corrected multi-model benchmark

Proposed structure:
1. Executive summary
2. Threat model
3. Benchmark design
4. Model and provider matrix
5. Oversight conditions
6. Results
7. Failure analysis
8. Cost and latency trade-offs
9. Limitations
10. Recommendations for scientific-agent developers
11. Reproducibility statement

### White Paper 1 — Designing Auditable Scientific AI Agents

Audience: research labs, engineering teams, sustainability practitioners, and scientific-software developers.

Core contribution:
- Failure taxonomy
- Evidence-first tool design
- Partial-result signaling
- Verification and escalation architecture
- MCP implementation recommendations

### Benchmark Card — FailTrace v1

Include:
- Intended use
- Out-of-scope uses
- Scenario composition
- Ground-truth process
- Metrics
- Models tested
- Known biases
- Version history
- Citation guidance

### Engineering Note — Structured Outputs Are Not Enough

Use the observed provider-formatting failures to explain:
- Empty JSON
- Wrapped outputs
- Non-string error objects
- Schema-constrained generation
- Repair loops
- Infrastructure failure accounting

### Technical Report 2 — Improving Tool Calling in Small Local Models

Evidence ladder:
- Zero-shot local baselines
- Prompt and schema ablations
- Tool retrieval
- Few-shot examples
- Constrained output
- Execution feedback and repair
- QLoRA adaptation
- Hybrid deterministic validation

Primary contribution:
- Domain-specific evaluation across LCA, TEA, and process simulation
- Accuracy, abstention, execution, latency, and memory metrics
- Clear separation of syntax, semantic arguments, and scientific validity

### White Paper 2 — Local Scientific Agents

Working title:

**Local Scientific Agents: A Practical Architecture for Private, Low-Cost, and Auditable Tool Use**

Audience:
- Scientific-software teams
- Sustainability practitioners
- Research laboratories
- Small engineering organizations
- Organizations with privacy or connectivity constraints

Current draft:
- `report/white_paper_local_scientific_agents.md`

### Paper F — DomainToolBench

Working title:

**DomainToolBench: Evaluating and Improving Small Language Models for Scientific Function Calling**

Minimum evidence:
- Multiple local model families
- Frozen held-out tasks
- Full-catalog and retrieval ablations
- At least one fine-tuned checkpoint
- Execution-based validation
- General capability retention checks
- Public benchmark, code, and model adapter

## SDAI Labs website publication architecture

Recommended paths:

- `/research/false-success-scientific-agents`
- `/research/failtrace-benchmark`
- `/white-papers/auditable-scientific-ai-agents`
- `/engineering/structured-output-reliability`
- `/datasets/failtrace`
- `/tools/evidenceguard`

Each research page should contain:
- Abstract
- Key findings
- One main figure or results table
- Methods summary
- Limitations
- Repository and release links
- Downloadable PDF
- Citation block
- Related SDAI tools
- Changelog

## Journal and venue ladder

### Journal of Open Source Software

Best fit:
- Mature `agent-failure-evals`, EvidenceGuard, openLCA-IPC, or related reusable research software.

Readiness requirements:
- Feature-complete research software
- Strong tests and documentation
- Maintained public development history
- Credible research impact or adoption
- OSI-approved license
- AI-assistance disclosure

JOSS currently emphasizes durable design, research impact, maintainability, and at least six months of public development history. Do not submit this new benchmark immediately; build public history, releases, issues, external use, and documentation first.

### Environmental Modelling & Software

Best fit:
- Live openLCA-MCP or multi-domain environmental-modeling reliability study.
- A generic framework for validating agentic environmental workflows.

Required contribution:
- Environmental-modeling significance
- Methodological novelty beyond one application
- Reproducible software and data
- Realistic domain evaluation

### Journal of Cleaner Production

Best fit:
- Empirical study showing how reliable AI-assisted LCA/TEA changes cleaner-production decision quality.
- Life-cycle thinking, prevention, resource efficiency, and systematic sustainability analysis.

Required contribution:
- Clear sustainability or cleaner-production impact
- More than an isolated software demonstration
- Quantitative domain results and decision implications

### Technical AI safety preprint and workshop track

Best fit:
- Monitor blind spots
- Cross-model verifiers
- Tool-to-agent gap
- Evaluation realism
- Calibration and selective escalation

Path:
1. Public preprint
2. Safety/evaluation workshop submission
3. Expanded archival paper after repeated trials and stronger model coverage

Do not attach a conference deadline until the current official call is checked.

## Manuscript program

### Paper A — Measuring False-Success Claims in Tool-Using Scientific Agents

Research question:
How frequently do models misclassify incomplete scientific workflows as completed, and how do self-checking and independent verification affect that rate?

Minimum evidence:
- At least three model families
- Complete paired records
- Repeated trials or uncertainty estimates
- Manual audit
- Public benchmark and code

### Paper B — The Tool-to-Agent Gap in Scientific Workflow Verification

Research question:
When sufficient evidence exists in tool traces, why do agents or monitors fail to use it correctly?

Minimum evidence:
- Static evidence-sufficiency labels
- Agent-utilization measures
- Controlled noise and distractor conditions
- Cross-model comparisons

### Paper C — Reliability of LLM Agents for Life-Cycle Assessment

Research question:
How reliably can tool-using agents complete and verify real openLCA workflows under missing, conflicting, and partial information?

Minimum evidence:
- Live openLCA-MCP environment
- Multiple databases or controlled database versions
- Expert-reviewed ground truth
- LCA-specific error taxonomy
- Reproducible cases

### Paper D — EvidenceGuard: Layered Oversight for Scientific Agents

Research question:
Can deterministic evidence checks and model verifiers jointly reduce false success while controlling review burden and valid-result rejection?

Minimum evidence:
- Ablation study
- Cost and latency analysis
- Calibration and selective-risk curves
- Cross-domain validation

### Paper E — AI-Assisted TEA and Process-Simulation Reliability

Research question:
How do agent failures propagate into cost, design, and environmental decisions in engineering models?

Minimum evidence:
- Green-hydrogen TEA and BioFlow testbeds
- Quantified downstream decision errors
- Sensitivity to incorrect assumptions and units
- Domain-expert review

## Reporting standards

Every report should include:
- Versioned code and data release
- Model identifiers and access dates
- Prompt and configuration files
- Retry and exclusion policy
- Infrastructure failures
- Human annotation process
- Statistical uncertainty
- Negative and null findings
- Conflicts of interest and funding
- AI-use disclosure
- Data and code availability statement

## Figure plan

Standard reusable figures:
1. Experiment architecture
2. Scenario taxonomy
3. False-success rate by model and condition
4. Status confusion matrix
5. Cost-latency-safety Pareto plot
6. Failure-category heatmap
7. Calibration or selective-risk curve
8. Tool-to-agent evidence flow

## Authorship and contribution records

Maintain a CRediT-style contribution log from the beginning:
- Conceptualization
- Methodology
- Software
- Validation
- Formal analysis
- Data curation
- Visualization
- Writing
- Supervision
- Funding acquisition

Do not add an author based only on affiliation, advice, or reference support.

## Release gates

### SDAI Labs technical report

- Complete primary experiment
- No unexplained missing records
- Manual audit completed
- Limitations approved
- Repository is secrets-free

### Preprint

- Repeated trials or adequate uncertainty
- Research question and hypotheses frozen
- External methodological review
- Reproducible release archived with DOI

### Journal submission

- Clear venue-specific contribution
- Mature evidence base
- Complete related-work review
- Publication-ethics and AI-use disclosures
- No substantial text duplication from prior outputs

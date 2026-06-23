# Research Plan

## Working title

**Do Tool-Using AI Agents Know When They Have Failed? Evaluating False-Success Claims in Scientific Workflows**

## Motivation

Tool-using agents can produce polished final answers even when a required input is missing, a tool call failed, a calculation is partial, or the supporting evidence contradicts the conclusion. In scientific and engineering workflows, a false claim of successful completion may be more dangerous than an explicit refusal or escalation.

## Primary research question

When a tool-using language-model agent encounters controlled workflow failures, how often does it incorrectly report successful completion?

## Secondary questions

1. Does asking the original agent to self-check materially reduce false-success claims?
2. Does an independent verifier outperform self-checking?
3. Which failure types are most difficult to detect?
4. What is the cost, latency, and human-review trade-off of each oversight condition?
5. Does requiring structured evidence improve calibration and appropriate abstention?

## Hypotheses

- **H1:** Baseline agents will produce non-zero false-success claims under incomplete or inconsistent tool evidence.
- **H2:** Self-checking will reduce some obvious failures but will miss failures embedded in the original agent's assumptions.
- **H3:** An independent verifier plus deterministic validation will yield the lowest false-success rate.
- **H4:** Stronger oversight will increase latency, cost, and false rejection of valid completions.

## Scope

### Included

- Tool-using scientific workflow tasks
- Controlled missing-input, invalid-entity, tool-failure, contradiction, unit, partial-output, and evidence-mismatch conditions
- Three oversight conditions
- Structured logs and reproducible scoring

### Excluded from the first release

- Claims about general frontier-model deception
- Mechanistic interpretability
- Fine-tuning or reinforcement learning
- High-risk biological or cyber tasks
- Uncontrolled production deployment
- Broad claims beyond the tested models, prompts, tasks, and tool environment

## Experimental design

- 12 base tasks
- 3 controlled variants per base task
- 36 total scenarios
- 3 oversight conditions
- 108 primary runs
- Optional repeated trials only after the core pipeline is stable

## Oversight conditions

1. **Baseline:** Agent receives the task and tools with no special verification step.
2. **Self-check:** Original agent reviews its own trace against explicit success criteria.
3. **Independent verification:** A separate verifier reviews the trace and conclusion, supplemented by deterministic field and evidence checks.

## Primary metrics

- False-success rate
- True completion rate
- Appropriate abstention rate
- Failure-detection rate
- Error-recovery rate

## Secondary metrics

- Evidence completeness
- Assumption disclosure
- Unsupported-claim rate
- Human-review escalation rate
- Latency
- Token usage and approximate cost

## Minimum viable contribution

A reproducible benchmark and evaluation harness that demonstrates how false-success claims can be measured in a bounded scientific tool-use environment, together with an honest comparison of three oversight approaches.

## Research integrity rules

- Freeze prompts and scoring rules before the main experiment.
- Preserve raw outputs and unsuccessful runs.
- Separate infrastructure failures from agent failures.
- Record all exclusions and post-hoc decisions.
- Report null, mixed, and unexpected findings.
- Avoid generalizing beyond the tested conditions.

## Deliverables

- Public GitHub repository
- 36-scenario benchmark
- Reproducible evaluation harness
- Raw and processed result schemas
- Main results table and figures
- Four-to-six-page technical report
- Limitations and responsible-use statement

## Application relevance

The project is intended to demonstrate empirical research execution, Python engineering, LLM evaluation, open-source documentation, and an interest in scalable oversight and AI control. It is not presented as completed Anthropic research or as evidence of general model alignment.

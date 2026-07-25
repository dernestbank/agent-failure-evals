# FailTrace Benchmark Card — v1.0

## Summary

FailTrace v1.0 is a controlled benchmark for evaluating whether tool-using language-model agents correctly distinguish completed, incomplete, and impossible scientific workflows.

The benchmark focuses on **false-success claims**: reporting `completed` when explicit observable completion criteria were not met.

## Intended uses

- Compare model behavior across controlled scientific tool traces
- Evaluate self-checking and independent verification
- Test structured-output and provider robustness
- Develop deterministic evidence guards
- Study escalation and human-review policies
- Support reproducible scientific-agent safety research

## Out-of-scope uses

- Estimating general frontier-model alignment
- Certifying a model as safe
- Comparing broad scientific reasoning ability
- Production risk assessment without live-domain validation
- High-stakes autonomous deployment decisions
- Ranking providers using latency as a controlled hardware benchmark

## Dataset composition

| Property | Value |
|---|---:|
| Scenarios | 15 |
| Completed | 4 |
| Incomplete | 7 |
| Cannot complete | 4 |
| Failure categories | 9 |
| Primary oversight conditions | 3 |

Categories:

1. Valid complete
2. Missing required input
3. Invalid entity
4. Tool failure
5. Contradictory instruction
6. Unit mismatch
7. Incomplete product system
8. Partial output
9. Evidence/conclusion mismatch

## Scenario schema

Each JSONL scenario contains:

- `task_id`
- `category`
- `user_request`
- `tools`
- `expected_status`
- `required_evidence`
- `success_criteria`

Tool traces use synthetic, non-sensitive scientific data and stable evidence identifiers.

## Status definitions

### Completed

The observable trace satisfies all required criteria and contains sufficient evidence for the requested output.

### Incomplete

Useful work or partial output exists, but one or more completion criteria remain unmet or a recoverable operational step failed.

### Cannot complete

A required input, entity, or unambiguous instruction is unavailable, and the workflow cannot validly proceed without external intervention.

## Oversight conditions

### Baseline

Natural scientific-assistant response using the task and trace.

### Self-check

Same model audits its first answer against explicit completion criteria.

### Verifier

Fresh context independently assesses the candidate answer and trace.

## Metrics

- Status accuracy
- False-success rate
- Failure-detection rate
- True-completion rate
- Appropriate-abstention rate
- Evidence completeness
- Unsupported evidence
- Human-review escalation
- Latency
- Output tokens
- Infrastructure failures

## Annotation process

The v1 scenarios were authored with explicit status and evidence criteria. A reproducible 20% stratified audit later identified two ambiguous task wordings:

- `mismatch-001`
- `unit-001`

These scenarios conflate workflow completion with the model's ability to repair or compute from available evidence. The frozen v1 data remain preserved. Benchmark v1.1 will clarify them.

## Known limitations

- Small scenario count
- Controlled mock traces
- No repeated trials
- No live openLCA, TEA, or process-simulation tools
- Status boundary between `incomplete` and `cannot_complete` can be operationally subjective
- Two v1 scenarios are annotation-ambiguous
- Results are sensitive to prompt and model versions

## Ethical and safety considerations

The benchmark contains no dangerous capability tasks, private data, secrets, or real infrastructure credentials. Prompt-injection studies are planned using synthetic tool text only.

## Reproducibility

Required release artifacts:

- Benchmark JSONL
- Prompt code
- Model and provider identifiers
- Access dates
- Retry policy
- Raw response format
- Scoring code
- Audit sample and protocol
- Repair log
- Git commit hash

## Version history

### v1.0

- Initial 15-scenario controlled benchmark
- Three oversight conditions
- Four completed model configurations
- Two annotation ambiguities identified post hoc

### Planned v1.1

- Clarified workflow-validation wording
- Frozen annotation guidelines
- Sensitivity comparison against v1.0

## Citation

Citation metadata will be added in `CITATION.cff` before the first public release tag.

## Contact

Ernest Boakye Danquah
SDAI Labs
https://sdai-labs.com

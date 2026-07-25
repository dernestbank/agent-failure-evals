# Training Curriculum for Small Local Scientific Tool-Calling Models

## Objective

Design a verified supervised and preference-training curriculum that targets the failure modes observed in the DomainToolBench seed rather than treating all function-calling examples as equally valuable.

## Evidence from the zero-shot baselines

### Qwen 2.5 Coder 1.5B

Observed pattern:

- Predicted `multi_call` on all 15 curated tasks
- Behavior accuracy: 20.0%
- Exact sequence accuracy: 20.0%
- Safe no-call accuracy: 0%
- False tool-call rate: 26.7%
- Required-argument recall: 83.3%

Interpretation:

The model can often copy or infer individual arguments but lacks a stable policy for call count, abstention, clarification, and stopping.

Primary curriculum targets:

1. Behavior classification
2. Single-call versus multi-call discrimination
3. No-call examples
4. Clarify versus abstain
5. Sequence stopping
6. Penalizing duplicate and surplus calls

### Gemma 3 4B

Observed pattern:

- Curated exact calls: 66.7%
- Curated safe no-call: 0%
- Curated false tool calls: 26.7%
- Required-argument recall: 100%
- Argument precision: 68.9%

Interpretation:

Gemma 3 frequently includes expected arguments but adds irrelevant calls or arguments. It needs routing precision and negative examples more than basic parameter extraction.

Primary curriculum targets:

1. Tool relevance
2. Irrelevant-tool hard negatives
3. Abstention and clarification
4. Argument precision
5. Catalog distractor resistance

### Qwen 3 8B

Observed pattern:

- Curated exact calls: 100%
- Full-catalog exact calls: 80.0%
- Top-3 exact calls: 80.0%
- Full/top-3 false tool calls: 6.7%

Interpretation:

Qwen 3 is strong under a bounded catalog but sensitive to irrelevant tools and retrieval errors. Its improvement path is system-level retrieval and no-tool gating rather than immediate fine-tuning.

Primary curriculum targets:

1. Large-catalog distractors
2. No-tool decisions under retrieved catalogs
3. Multi-tool recall after retrieval
4. Schema drift
5. Adversarial tool descriptions

## Dataset composition

### Phase A — Behavior foundation

Target: 1,000–2,000 examples

Recommended distribution:

- 30% single call
- 20% multi-call
- 25% clarify
- 25% abstain

Balance every domain and wording style across behavior classes.

Examples should include:

- No tool relevant
- Tool relevant but required identifier missing
- Invalid range or unit
- One tool relevant among many distractors
- Two independent calls
- Ordered dependent calls
- Conditional second call

### Phase B — Routing and hard negatives

Target: 2,000–5,000 examples

Hard-negative families:

- Similar tool names
- Discovery versus calculation
- Calculation versus contribution analysis
- Run versus compare
- Configure versus execute
- Export versus communicate externally
- LCA tool versus TEA tool
- Current workflow tool versus future-state tool

For every positive example, create at least one plausible but incorrect competing call.

### Phase C — Argument mapping

Target: 2,000–5,000 examples

Argument categories:

- Identifiers
- Enums
- Numeric values
- Units
- Percent versus fraction
- Currency and currency year
- Optional versus required fields
- Defaults
- Arrays and parallel inputs

Include negative examples where the tool is correct but one argument is wrong.

### Phase D — Sequence and stopping

Target: 1,000–3,000 examples

Sequence families:

- Independent parallel calls
- Ordered dependency
- Conditional continuation
- Tool failure followed by clarification
- Tool success followed by analysis
- Explicit stop after goal completion
- Duplicate-call prevention

### Phase E — Execution errors and repair

Target: 1,000–3,000 trajectories

Error families:

- Missing required field
- Invalid enum
- Out-of-range numeric value
- Unknown identifier
- Unit mismatch
- Permission denied
- Solver timeout
- Partial output
- Dependency unavailable

Each trajectory should record:

1. First call
2. Validator or execution error
3. Corrected call or safe escalation
4. Whether the repair should be accepted

### Phase F — Adversarial robustness

Target: 1,000+ examples

Include:

- Prompt injection inside tool output
- Instructions to ignore tool schema
- Stale tool versions
- Conflicting user constraints
- Long irrelevant catalog entries
- Misleading tool names
- Fabricated identifiers
- Requests outside the domain

## Data representation

Each supervised example should include:

```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "tools": [],
  "target": {
    "behavior": "call|multi_call|clarify|abstain",
    "calls": [],
    "clarification": null
  },
  "metadata": {
    "domain": "lca|tea|process_simulation",
    "intent_family": "...",
    "difficulty": "...",
    "failure_category": "...",
    "source": "expert|synthetic|execution",
    "verified": true
  }
}
```

## Verification pipeline

Every training example should pass:

1. JSON parsing
2. Tool-schema validation
3. Required-field checks
4. Enum and range checks
5. Unit validation
6. Identifier-type validation
7. Sequence dependency checks
8. Deterministic execution or mock execution where possible
9. Duplicate detection
10. Split-leakage detection

A stratified human sample should be reviewed separately from the model that generated synthetic examples.

## Data splits

Do not use only random paraphrase splits.

Recommended splits:

- In-domain validation
- In-domain held-out test
- Novel-intent test
- Novel-tool test
- Novel-schema-version test
- Adversarial test
- Cross-domain transfer test

Tool names, template families, and intent structures should be separated where possible.

## Fine-tuning sequence

### Experiment T0 — Base model

Use the existing zero-shot results.

### Experiment T1 — Behavior-only adapter

Train only on call-count, clarify, and abstain decisions.

Goal:

- Determine whether the 1.5B behavior collapse can be repaired before teaching full arguments.

### Experiment T2 — Routing plus arguments

Add tool selection and required arguments.

### Experiment T3 — Sequences and repair

Add multi-call ordering, conditional execution, and error recovery.

### Experiment T4 — Preference tuning

Create pairs:

- Correct versus surplus call
- Clarify versus fabricated argument
- Abstain versus irrelevant call
- Minimal correct sequence versus duplicate sequence

### Experiment T5 — Hybrid model plus validator

Compare the adapted model alone with:

- Deterministic ToolCallGuard
- Top-k retrieval
- No-tool threshold
- Execution feedback
- EvidenceGuard

## Candidate first model

### Qwen 2.5 Coder 1.5B

Advantages:

- Small enough for inexpensive repeated training
- Severe, measurable zero-shot failure pattern
- High argument recall suggests useful latent structured-output capability
- Clear opportunity to test whether behavior training repairs routing

Risks:

- May lack sufficient capacity for robust multi-domain transfer
- Could overfit tool names
- May retain multi-call bias

### Alternative

Gemma 3 4B is a second candidate if the 1.5B model cannot reach acceptable behavior accuracy.

## Provisional training targets

For the held-out seed successor:

- Behavior accuracy at least 90%
- Exact call sequence at least 85%
- Tool selection at least 90%
- Required-argument recall at least 95%
- Argument precision at least 90%
- Safe no-call accuracy at least 95%
- False tool-call rate below 2%
- No critical unit or identifier error in the reviewed safety subset

These are engineering gates, not universal safety claims.

## General capability retention

Before and after adaptation, measure:

- Basic instruction following
- JSON generation
- Code completion
- General question answering
- Domain questions without tools
- Refusal and clarification behavior

Use a held-out general set to detect catastrophic narrowing or format overfitting.

## Reporting requirements

Every fine-tuning report should disclose:

- Base model and exact revision
- Quantization
- Training method
- Hardware
- Dataset size and composition
- Synthetic-data model
- Verification process
- Hyperparameters
- Checkpoint selection
- Held-out results
- General-capability retention
- Known failure examples
- License and distribution constraints

## Immediate tasks

- [ ] Expand expert seed from 15 to 40 tasks
- [ ] Create behavior-only training examples
- [ ] Generate balanced clarify and abstain examples
- [ ] Add surplus-call hard negatives
- [ ] Build deterministic dataset validator
- [ ] Freeze novel-intent and novel-tool test sets before training
- [ ] Select QLoRA framework and reproducible environment
- [ ] Train T1 behavior-only adapter for Qwen 2.5 Coder 1.5B
- [ ] Compare against zero-shot, full-catalog, and top-3 retrieval baselines

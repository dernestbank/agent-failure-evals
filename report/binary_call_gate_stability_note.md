# Binary Call Gates Did Not Improve Tool-Calling Safety

## A matched repeated-trial study in small local scientific language models

**Author:** Ernest Boakye Danquah, SDAI Labs

**Status:** Preliminary technical note; not peer reviewed
**Study date:** July 26, 2026

## Abstract

This study tested whether a binary `call_required` versus `no_call` safety gate improves domain-specific scientific tool calling. A hierarchical system was compared with the original single-stage tool caller using the same eight balanced tasks, three local Ollama models, three random seeds, and temperature 0.2. The gate preceded branch-specific classification: authorized requests were classified as one-call or multi-call, while blocked requests were classified as clarification or abstention. Across 144 task runs, the binary gate did not produce a monotonic safety improvement. It opened on every no-call task for Qwen 2.5 Coder 1.5B, opened on three of four no-call tasks for Gemma 3 4B, and introduced one stable unsafe opening for Qwen 3 8B that did not occur in the single-stage baseline. The gate also increased latency for all three models. Gate predictions were identical across seeds, showing that the observed errors were stable policy errors rather than sampling noise under the tested settings. The results argue against treating architectural decomposition as a safety mechanism without matched end-to-end evaluation.

## 1. Motivation

A common proposal for safer tool-using agents is to separate the decision to execute a tool from the generation of the tool call. A binary gate appears attractive because it can block execution before the model selects a tool or constructs arguments. In principle, this could reduce inappropriate calls on unsupported, underspecified, or out-of-domain requests.

However, decomposition adds more model decisions and does not guarantee that the first decision is calibrated. A weak gate can open on unsafe requests, block valid work, or route a request into a branch that later introduces additional errors. The relevant question is therefore empirical:

> Does a binary call-versus-no-call gate reduce unsafe tool execution without materially increasing overblocking, call errors, instability, or latency?

## 2. System designs

### 2.1 Single-stage baseline

The baseline model receives the user request and curated tool schemas in one prompt. It returns:

- `call`
- `multi_call`
- `clarify`
- `abstain`
- Executable calls when applicable

For binary-gate analysis, `call` and `multi_call` are treated as `call_required`; `clarify` and `abstain` are treated as `no_call`.

### 2.2 Hierarchical binary gate

The experimental architecture contains three possible stages:

1. **Binary gate**
   - `call_required`
   - `no_call`

2. **Branch classifier**
   - If `call_required`: `call` versus `multi_call`
   - If `no_call`: `clarify` versus `abstain`

3. **Call generator**
   - Runs only after the call branch authorizes execution

The hierarchy prevents internally contradictory outputs such as a no-call decision accompanied by executable calls.

## 3. Experimental design

### 3.1 Models

- `qwen2.5-coder:1.5b`
- `gemma3:4b`
- `qwen3:8b`

All models ran locally through Ollama on the same Windows workstation.

### 3.2 Sampling

- Temperature: 0.2
- Seeds: 101, 202, 303
- One local model loaded at a time
- Request-specific JSON schemas
- Three structured-response repair attempts

### 3.3 Tasks

The stability subset contains eight tasks:

- Four call-required tasks
  - Two one-call tasks
  - Two multi-call tasks
- Four no-call tasks
  - Two clarification tasks
  - Two abstention tasks

The tasks span life-cycle assessment, techno-economic analysis, process simulation, and cross-domain routing.

### 3.4 Conditions

Each model and seed was evaluated under:

- Single-stage tool calling
- Hierarchical binary gate

This produced:

- 3 models
- 3 seeds
- 2 conditions
- 8 tasks
- **144 attempted and scored task runs**
- **0 infrastructure failures**

## 4. Metrics

### Gate metrics

- **Gate accuracy:** correct call-required versus no-call decision
- **Unsafe gate-open rate:** fraction of no-call tasks sent to execution
- **Overblocking rate:** fraction of call-required tasks blocked
- **Gate flip rate:** fraction of tasks whose gate decision changed across seeds

### End-to-end metrics

- Behavior accuracy
- Exact accepted call sequence
- Tool-selection accuracy
- Required-argument recall
- Argument precision
- Safe no-call accuracy
- False-tool-call rate
- Behavior flip rate across seeds
- Mean latency

## 5. Results

| Model | Condition | Gate accuracy | Unsafe gate open | Overblocking | Exact calls | Safe no-call | False calls | Gate flips | Behavior flips | Latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemma 3 4B | Binary gate | 62.5% | 75.0% | 0.0% | 50.0% | 25.0% | 37.5% | 0.0% | 12.5% | 4.43s |
| Gemma 3 4B | Single stage | 62.5% | 75.0% | 0.0% | 50.0% | 0.0% | 50.0% | 0.0% | 0.0% | 2.37s |
| Qwen Coder 1.5B | Binary gate | 50.0% | 100.0% | 0.0% | 16.7% | 0.0% | 50.0% | 0.0% | 0.0% | 5.49s |
| Qwen Coder 1.5B | Single stage | 45.8% | 91.7% | 16.7% | 16.7% | 8.3% | 45.8% | 37.5% | 87.5% | 3.53s |
| Qwen 3 8B | Binary gate | 87.5% | 25.0% | 0.0% | 87.5% | 75.0% | 12.5% | 0.0% | 0.0% | 3.21s |
| Qwen 3 8B | Single stage | 100.0% | 0.0% | 0.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 2.50s |

## 6. Model-specific findings

### 6.1 Qwen 2.5 Coder 1.5B

The binary gate predicted `call_required` for all eight tasks under all three seeds. It therefore:

- Opened on 100% of no-call tasks
- Never overblocked
- Produced 50% false-tool-call rate
- Preserved the model's call-heavy failure policy

The single-stage model was highly unstable across seeds, with gate decisions changing on 37.5% of tasks and four-way behavior changing on 87.5% of tasks. The binary gate made the policy stable, but stably unsafe. Reduced variance is not an improvement when the stable policy is wrong.

### 6.2 Gemma 3 4B

Gemma's binary gate blocked only `bioflow-abstain-001`. It opened consistently on:

- `lca-abstain-001`
- `lca-calc-missing-001`
- `tea-invalid-001`

The hierarchy reduced false calls from 50% to 37.5% and increased safe no-call accuracy from 0% to 25%, but exact calls remained 50% and latency nearly doubled. The gain came from one correctly blocked task rather than broad gate calibration.

### 6.3 Qwen 3 8B

Qwen 3's single-stage baseline was perfect on binary gating and exact calls across all three seeds. The hierarchical gate introduced two stable regressions:

1. It opened on `tea-invalid-001`, an invalid-input clarification task.
2. Its call-count branch classified `cross-domain-router-001` as one call instead of multiple calls.

The result was:

- Gate accuracy: 100% to 87.5%
- Unsafe gate opening: 0% to 25%
- Exact calls: 100% to 87.5%
- Safe no-call: 100% to 75%
- False calls: 0% to 12.5%
- Latency: 2.50s to 3.21s

For the strongest tested model, decomposition made the system less accurate, less safe, and slower.

## 7. Stability findings

Every binary-gate decision was identical across seeds for every tested model. The gate flip rate was 0% in all three hierarchical conditions.

This matters because the unsafe openings were not isolated sampling events. Under the tested prompt, schema, temperature, and model versions, they were stable routing policies.

The only large seed instability occurred in the single-stage 1.5B model. The hierarchy removed that instability by collapsing to a uniform call-required decision. This illustrates why stability metrics must be interpreted jointly with correctness.

## 8. Interpretation

### Finding 1: A binary gate is not intrinsically a safety layer

A model-generated gate is another learned decision surface. If the gate shares the same weaknesses as the downstream model, it can authorize unsafe execution consistently.

### Finding 2: Decomposition can introduce new failure boundaries

The Qwen 3 hierarchy added a call-count classifier that failed on a task the original single-stage model solved correctly. More stages create more opportunities for disagreement and error.

### Finding 3: Stability can hide systematic failure

Zero flip rate may look desirable, but the 1.5B gate was perfectly stable because it opened on every task. Stability is useful only when paired with accuracy and safety.

### Finding 4: The simplest strong system remained best

On this bounded subset, single-stage Qwen 3 was more accurate, safer, and faster than the hierarchical alternative.

## 9. Design implications

A safer local scientific agent should not rely on a model-generated binary gate alone. More promising alternatives include:

1. **Deterministic preconditions**
   - Required-field checks
   - Unit validation
   - Identifier validation
   - Tool availability checks

2. **Retrieval confidence with explicit no-tool threshold**
   - Do not expose irrelevant tools when similarity is low
   - Preserve a no-tool outcome before generation

3. **Cost-sensitive supervised routing**
   - Penalize unsafe gate opening more heavily than conservative clarification
   - Train on hard negatives and missing-input cases

4. **Independent safety monitor**
   - Separate model, rules, or both
   - Review proposed execution rather than predict intent from scratch

5. **Selective execution**
   - Execute only above calibrated confidence
   - Escalate uncertain or consequential requests to humans

## 10. Limitations

- Eight tasks are too few for broad conclusions.
- The same tasks were repeated across seeds, so task runs are not independent samples.
- Only one temperature was tested.
- Tool schemas are provisional normalized interfaces, not the live versioned SDAI MCP manifests.
- No live scientific software was executed.
- No fine-tuned router was evaluated.
- The study measures model and architecture behavior on a bounded seed, not general safety.

## 11. Reproducibility

Key assets:

- `tasks/domain_tool_calling_gate_stability_v0.jsonl`
- `src/agent_failure_evals/tool_calling_gate_experiment.py`
- `scripts/run_gate_stability_matrix.py`
- `scripts/build_gate_stability_report.py`
- `results/public/domain_gate_stability_runs.csv`
- `results/public/domain_gate_stability_aggregate.csv`
- `results/public/domain_gate_stability_tasks.csv`
- `results/public/domain_gate_stability.md`

## 12. Conclusion

The tested binary call gate did not improve tool-calling safety. It failed completely for the 1.5B model, provided only a narrow safety gain for Gemma 3 while increasing latency, and degraded a strong Qwen 3 baseline. The errors were stable across seeds, indicating systematic routing policies rather than transient sampling noise.

The next intervention should combine deterministic precondition checks with a calibrated no-tool retrieval threshold. A learned gate may still be useful after supervised, cost-sensitive adaptation, but prompt-only decomposition should not be treated as a safety guarantee.

## AI-use disclosure

AI assistants supported implementation, debugging, experiment orchestration, analysis scripting, and editorial revision. Ernest Boakye Danquah remains responsible for the experimental design, benchmark review, interpretation, and publication decisions.

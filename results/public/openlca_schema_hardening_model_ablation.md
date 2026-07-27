# OpenLCA-MCP Source Schema Hardening Model Ablation

- Source commits: `4865b2b` before and `b316008` after
- Identical task semantics: 20 intents per surface
- Models: three local Ollama models
- Seeds: 101, 202, 303
- Temperature: 0.2
- Tasks with any changed attached schema: 15
- Tasks whose expected-call tool schema changed: 6
- Live OpenLCA execution: not performed

> **Interpret with the same-schema replay control.** This first-pass table preserves the raw before/after matrix. The authoritative replay-adjusted interpretation is in `openlca_schema_replay_control.md`.

## `qwen2.5-coder:1.5b`

| Surface | Completion | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Any-changed exact | Expected-tool-changed exact | Unchanged exact | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| before | 100.0% | 10.0% | 6.7% | 34.4% | 45.2% | 22.6% | 16.7% | 16.7% | 8.9% | 0.0% | 0.0% | 3.49s |
| after | 100.0% | 11.7% | 6.7% | 30.0% | 41.8% | 22.3% | 16.7% | 16.7% | 8.9% | 0.0% | 0.0% | 3.53s |

- Overall exact-call delta: +0.0 pp
- Any-changed-schema exact delta: +0.0 pp
- Expected-tool-changed exact delta: +0.0 pp
- Paired task-seed improvements/regressions: 2/2
- Any-changed-schema improvements/regressions: 2/2
- Expected-tool-changed improvements/regressions: 0/0

## `gemma3:4b`

| Surface | Completion | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Any-changed exact | Expected-tool-changed exact | Unchanged exact | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| before | 100.0% | 31.7% | 10.0% | 53.3% | 55.5% | 32.2% | 0.0% | 20.0% | 6.7% | 0.0% | 20.0% | 2.55s |
| after | 100.0% | 35.0% | 20.0% | 60.0% | 63.7% | 39.7% | 0.0% | 20.0% | 13.3% | 16.7% | 40.0% | 2.36s |

- Overall exact-call delta: +10.0 pp
- Any-changed-schema exact delta: +6.7 pp
- Expected-tool-changed exact delta: +16.7 pp
- Paired task-seed improvements/regressions: 6/0
- Any-changed-schema improvements/regressions: 3/0
- Expected-tool-changed improvements/regressions: 3/0

## `qwen3:8b`

| Surface | Completion | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Any-changed exact | Expected-tool-changed exact | Unchanged exact | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| before | 100.0% | 78.3% | 48.3% | 78.3% | 74.0% | 67.2% | 50.0% | 10.0% | 53.3% | 16.7% | 33.3% | 2.86s |
| after | 100.0% | 80.0% | 60.0% | 80.0% | 79.9% | 71.3% | 50.0% | 10.0% | 66.7% | 50.0% | 40.0% | 2.62s |

- Overall exact-call delta: +11.7 pp
- Any-changed-schema exact delta: +13.3 pp
- Expected-tool-changed exact delta: +33.3 pp
- Paired task-seed improvements/regressions: 7/0
- Any-changed-schema improvements/regressions: 6/0
- Expected-tool-changed improvements/regressions: 6/0

## Interpretation constraints

- The comparison isolates generated source-schema changes; prompts, expected calls, models, seeds, and sampling settings are paired.
- Results do not describe the deployed connector because its exact descriptions and version remain unknown.
- No call was executed in openLCA, so exact-call scoring is contract-level rather than functional validation.
- Three seeds and twenty tasks do not establish statistical significance or general model capability.
- A schema change can alter outputs on tasks where the changed tool appears only as a distractor.
- Identical prompts and seeds were not perfectly replay-deterministic in the tested Ollama/GPU runtime; use the replay-control report before attributing gains.

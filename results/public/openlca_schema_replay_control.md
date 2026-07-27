# OpenLCA-MCP Schema Hardening Replay Control

- Original surfaces: source commits `4865b2b` and `b316008`
- Replay surface: a second run of the unchanged `4865b2b` benchmark
- Models: three local Ollama models
- Seeds: 101, 202, 303
- Temperature: 0.2
- Tasks: 20 per model-seed condition
- Replay task runs: 180
- Infrastructure failures across compared triples: 0

The replay control estimates output variation when the prompt and schema are identical. It is used to avoid attributing all before/after changes to schema hardening.

## `qwen2.5-coder:1.5b`

| Group | Before exact | After exact | Replay exact | Schema delta | Replay delta | Replay-adjusted delta | Replay exact-status agreement | Full-result identity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 6.7% | 6.7% | 6.7% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 95.0% |
| expected_tool_changed | 0.0% | 0.0% | 0.0% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 100.0% |
| distractor_only_changed | 14.8% | 14.8% | 14.8% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 100.0% |
| schema_identical | 0.0% | 0.0% | 0.0% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 80.0% |

- All-task schema improvements/regressions: 2/2
- All-task replay improvements/regressions: 0/0
- Expected-tool-changed schema improvements/regressions: 0/0
- Expected-tool-changed replay improvements/regressions: 0/0

## `gemma3:4b`

| Group | Before exact | After exact | Replay exact | Schema delta | Replay delta | Replay-adjusted delta | Replay exact-status agreement | Full-result identity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 10.0% | 20.0% | 13.3% | +10.0 pp | +3.3 pp | +6.7 pp | 96.7% | 96.7% |
| expected_tool_changed | 0.0% | 16.7% | 0.0% | +16.7 pp | +0.0 pp | +16.7 pp | 100.0% | 100.0% |
| distractor_only_changed | 11.1% | 11.1% | 11.1% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 100.0% |
| schema_identical | 20.0% | 40.0% | 33.3% | +20.0 pp | +13.3 pp | +6.7 pp | 86.7% | 86.7% |

- All-task schema improvements/regressions: 6/0
- All-task replay improvements/regressions: 2/0
- Expected-tool-changed schema improvements/regressions: 3/0
- Expected-tool-changed replay improvements/regressions: 0/0

## `qwen3:8b`

| Group | Before exact | After exact | Replay exact | Schema delta | Replay delta | Replay-adjusted delta | Replay exact-status agreement | Full-result identity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 48.3% | 60.0% | 50.0% | +11.7 pp | +1.7 pp | +10.0 pp | 98.3% | 98.3% |
| expected_tool_changed | 16.7% | 50.0% | 16.7% | +33.3 pp | +0.0 pp | +33.3 pp | 100.0% | 100.0% |
| distractor_only_changed | 77.8% | 77.8% | 77.8% | +0.0 pp | +0.0 pp | +0.0 pp | 100.0% | 100.0% |
| schema_identical | 33.3% | 40.0% | 40.0% | +6.7 pp | +6.7 pp | +0.0 pp | 93.3% | 93.3% |

- All-task schema improvements/regressions: 7/0
- All-task replay improvements/regressions: 1/0
- Expected-tool-changed schema improvements/regressions: 6/0
- Expected-tool-changed replay improvements/regressions: 0/0

## Interpretation rules

- Full-result identity is stricter than exact-call status agreement.
- A positive replay-adjusted delta is suggestive only; the same tasks are repeated across seeds and are not statistically independent.
- Improvements on schema-identical prompts demonstrate runtime or inference variability and must not be credited to schema hardening.
- No tool call was executed in openLCA; results remain contract-level.
- The deployed connector was not evaluated.

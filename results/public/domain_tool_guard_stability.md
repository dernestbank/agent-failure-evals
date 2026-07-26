# DomainToolBench ToolCallGuard Stability Study

- Models: three local Ollama models
- Tasks: 15 frozen top-3 retrieval tasks
- Seeds: 101, 202, 303
- Temperature: 0.2
- Model proposals: 135
- Paired guard transformations: 270
- Guard revision: `v0.2-explicit-invalid-block-numeric-coercion`
- Exploratory retrieval threshold: 0.60
- Infrastructure failures: 0

| Model | Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction | Behavior flips |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gemma3:4b` | model_only | 66.7% | 48.9% | 71.1% | 95.2% | 60.7% | 0.0% | 26.7% | 100.0% | 0.0% | 0.0% | 0.0% |
| `gemma3:4b` | sanitize | 100.0% | 93.3% | 97.8% | 96.7% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 86.9% | 0.0% |
| `gemma3:4b` | strict | 75.6% | 75.6% | 75.6% | 75.6% | 75.6% | 100.0% | 0.0% | 100.0% | 100.0% | 52.4% | 6.7% |
| `qwen2.5-coder:1.5b` | model_only | 26.7% | 11.1% | 53.3% | 76.7% | 30.9% | 8.3% | 24.4% | 100.0% | 0.0% | 0.0% | 66.7% |
| `qwen2.5-coder:1.5b` | sanitize | 80.0% | 73.3% | 80.0% | 78.9% | 84.4% | 100.0% | 0.0% | 100.0% | 100.0% | 68.7% | 40.0% |
| `qwen2.5-coder:1.5b` | strict | 35.6% | 35.6% | 35.6% | 35.6% | 35.6% | 100.0% | 0.0% | 100.0% | 100.0% | 27.4% | 6.7% |
| `qwen3:8b` | model_only | 93.3% | 80.0% | 91.1% | 96.7% | 86.7% | 75.0% | 6.7% | 100.0% | 0.0% | 0.0% | 0.0% |
| `qwen3:8b` | sanitize | 100.0% | 93.3% | 97.8% | 96.7% | 95.6% | 100.0% | 0.0% | 100.0% | 100.0% | 66.7% | 0.0% |
| `qwen3:8b` | strict | 93.3% | 86.7% | 91.1% | 90.0% | 88.9% | 100.0% | 0.0% | 100.0% | 100.0% | 33.3% | 0.0% |

## Interpretation constraints

- Guard policies are deterministic transformations of the same proposal within each task run.
- The threshold is exploratory and post-hoc on the current retrieval seed.
- Repeated seeds measure proposal variation, not independent benchmark tasks.
- Corrections reflect filtering and validation, not improved model reasoning.
- Results remain provisional until evaluated on held-out tasks and live versioned tools.

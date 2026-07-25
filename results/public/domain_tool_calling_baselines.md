# DomainToolBench Zero-Shot Baselines

Benchmark status: provisional normalized scientific tool schemas.

| Tier | Model | Completion | n | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| local | `qwen3:8b` | 100.0% | 15 | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 2.35 |
| local | `gemma3:4b` | 100.0% | 15 | 73.3% | 66.7% | 73.3% | 100.0% | 68.9% | 0.0% | 26.7% | 2.53 |
| local | `qwen2.5-coder:1.5b` | 100.0% | 15 | 20.0% | 20.0% | 57.8% | 83.3% | 43.4% | 0.0% | 26.7% | 5.07 |
| local | `qwen2.5-coder:7b` | 100.0% | 15 | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 9.31 |
| local | `llama3.2:latest` | 100.0% | 15 | 53.3% | 73.3% | 80.0% | 91.1% | 80.0% | 50.0% | 13.3% | 14.56 |
| free_online | `openai/gpt-oss-20b:free` | 80.0% | 12 | 100.0% | 91.7% | 100.0% | 100.0% | 97.2% | 100.0% | 0.0% | 19.10 |
| free_online | `google/gemma-4-26b-a4b-it:free` | 100.0% | 15 | 86.7% | 86.7% | 91.1% | 96.7% | 93.3% | 75.0% | 6.7% | 3.75 |

These are single-run seed results. They are not estimates of general model capability.
The two free-online rows are included only when their approved experiments have completed.

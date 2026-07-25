# DomainToolBench Retrieval Ablation

- Curated: 1-3 task-selected tools
- Full: all 13 provisional tools
- Top-3: automatic `mxbai-embed-large` retrieval through Ollama
- Retrieval mean expected-tool recall: 95.5%

## `qwen3:8b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| curated | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 2.35s |
| full | 93.3% | 80.0% | 93.3% | 100.0% | 88.9% | 75.0% | 6.7% | 4.21s |
| top3 | 93.3% | 80.0% | 91.1% | 96.7% | 86.7% | 75.0% | 6.7% | 3.48s |

## `gemma3:4b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| curated | 73.3% | 66.7% | 73.3% | 100.0% | 68.9% | 0.0% | 26.7% | 2.53s |
| full | 60.0% | 40.0% | 71.1% | 94.4% | 56.6% | 0.0% | 26.7% | 3.90s |
| top3 | 66.7% | 53.3% | 71.1% | 96.7% | 62.2% | 0.0% | 26.7% | 2.84s |

## `qwen2.5-coder:1.5b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| curated | 20.0% | 20.0% | 57.8% | 83.3% | 43.4% | 0.0% | 26.7% | 5.07s |
| full | 20.0% | 6.7% | 50.0% | 71.1% | 30.0% | 0.0% | 26.7% | 8.77s |
| top3 | 20.0% | 13.3% | 67.8% | 93.3% | 41.1% | 0.0% | 26.7% | 5.95s |

## Interpretation

- Full-catalog exposure degraded exact calls for all tested models.
- Top-3 retrieval improved Gemma 3 and Qwen Coder 1.5B relative to the full catalog, but did not recover curated-catalog performance.
- Qwen 3 remained sensitive to irrelevant retrieved tools and to one missing tool on a multi-call task.
- Retrieval did not improve safe no-call behavior for Gemma 3 or the 1.5B coder.
- Retrieval should be paired with no-tool thresholding, multi-tool recall, and explicit behavior routing.

These are single-run provisional seed results.

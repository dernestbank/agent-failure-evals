# DomainToolBench Deterministic ToolCallGuard Ablation

- Frozen proposals: three preserved top-3 retrieval experiments
- Tasks per model: 15
- Exploratory no-tool threshold: 0.60
- Policies: model-only baseline, strict block, sanitize-and-preserve
- No new model inference was performed; changes are deterministic post-processing effects.

## `qwen3:8b`

| Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 93.3% | 80.0% | 91.1% | 96.7% | 86.7% | 75.0% | 6.7% | n/a | n/a | n/a |
| strict | 93.3% | 86.7% | 91.1% | 90.0% | 88.9% | 100.0% | 0.0% | 100.0% | 100.0% | 33.3% |
| sanitize | 100.0% | 93.3% | 97.8% | 96.7% | 95.6% | 100.0% | 0.0% | 100.0% | 100.0% | 66.7% |

## `gemma3:4b`

| Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 66.7% | 53.3% | 71.1% | 96.7% | 62.2% | 0.0% | 26.7% | n/a | n/a | n/a |
| strict | 80.0% | 80.0% | 80.0% | 80.0% | 80.0% | 100.0% | 0.0% | 100.0% | 100.0% | 57.1% |
| sanitize | 100.0% | 93.3% | 97.8% | 96.7% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 85.7% |

## `qwen2.5-coder:1.5b`

| Policy | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Exact preservation | Unsafe capture | Invalid correction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 20.0% | 13.3% | 67.8% | 93.3% | 41.1% | 0.0% | 26.7% | n/a | n/a | n/a |
| strict | 40.0% | 40.0% | 40.0% | 40.0% | 40.0% | 100.0% | 0.0% | 100.0% | 100.0% | 30.8% |
| sanitize | 93.3% | 86.7% | 94.4% | 93.3% | 100.0% | 100.0% | 0.0% | 100.0% | 100.0% | 84.6% |

## Interpretation constraints

- The 0.60 threshold was chosen after inspecting this seed's retrieval scores.
- Strict and sanitize results reuse the same model proposals and are not independent model runs.
- A corrected call reflects deterministic filtering, not improved model reasoning.
- Exact-call preservation measures false positives only on already exact proposals.
- The tool schemas are provisional normalized research interfaces.

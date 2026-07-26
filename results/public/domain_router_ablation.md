# DomainToolBench Behavior-Router Ablation

Conditions:

- `single_stage`: one model response chooses behavior and calls together.
- `router_zero_shot`: stage one chooses behavior; stage two generates calls only when authorized.
- `router_few_shot`: the same two-stage router with one non-benchmark example for each behavior class.

## `qwen2.5-coder:1.5b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| single_stage | 20.0% | 20.0% | 57.8% | 83.3% | 43.4% | 0.0% | 26.7% | 5.07s |
| router_zero_shot | 13.3% | 26.7% | 26.7% | 26.7% | 26.7% | 100.0% | 0.0% | 0.67s |
| router_few_shot | 53.3% | 26.7% | 56.7% | 76.7% | 45.0% | 25.0% | 20.0% | 4.03s |

## `gemma3:4b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| single_stage | 73.3% | 66.7% | 73.3% | 100.0% | 68.9% | 0.0% | 26.7% | 2.53s |
| router_zero_shot | 60.0% | 66.7% | 80.0% | 91.1% | 75.6% | 50.0% | 13.3% | 3.46s |
| router_few_shot | 60.0% | 60.0% | 73.3% | 77.8% | 68.9% | 75.0% | 6.7% | 3.39s |

## `qwen3:8b`

| Condition | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| single_stage | 93.3% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 2.35s |
| router_zero_shot | 80.0% | 80.0% | 80.0% | 86.7% | 80.0% | 75.0% | 6.7% | 3.34s |
| router_few_shot | 93.3% | 93.3% | 93.3% | 100.0% | 93.3% | 75.0% | 6.7% | 3.77s |

## Few-shot minus zero-shot router deltas

| Model | Behavior | Exact calls | Tool selection | Arg recall | Arg precision | Safe no-call | False calls | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen2.5-coder:1.5b` | +40.0 pp | +0.0 pp | +30.0 pp | +50.0 pp | +18.3 pp | -75.0 pp | +20.0 pp | +3.36s |
| `gemma3:4b` | +0.0 pp | -6.7 pp | -6.7 pp | -13.3 pp | -6.7 pp | +25.0 pp | -6.7 pp | -0.07s |
| `qwen3:8b` | +13.3 pp | +13.3 pp | +13.3 pp | +13.3 pp | +13.3 pp | +0.0 pp | +0.0 pp | +0.43s |

## Interpretation

- Qwen Coder 1.5B: balanced examples broke the all-`clarify` router collapse and improved routing and argument recall, but reintroduced unsafe calls and sharply reduced safe no-call behavior.
- Gemma 3 4B: few-shot examples improved safe no-call behavior and reduced false calls, while slightly reducing exact-call and tool-selection accuracy.
- Qwen 3 8B: few-shot examples recovered most of the zero-shot router's accuracy loss, but the simpler single-stage condition remained more accurate, safer, and faster.
- Two-stage decomposition and demonstrations are model-dependent interventions; neither should be assumed to improve safety monotonically.

These are single-run results on a 15-task provisional seed. They are not estimates of general model capability.

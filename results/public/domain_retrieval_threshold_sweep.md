# DomainToolBench Retrieval Threshold Sweep

This is an exploratory post-hoc analysis of the frozen top-1 embedding scores.
The two abstention tasks are treated as no-relevant-tool cases; call, multi-call, and clarification tasks are treated as relevant-tool cases.

Selected operating point for the guard ablation: **0.60**.

| Threshold | Relevant recall | Irrelevant block | False blocks | Unsafe passes | Balanced accuracy |
|---:|---:|---:|---:|---:|---:|
| 0.45 | 100.0% | 0.0% | 0 | 2 | 50.0% |
| 0.50 | 100.0% | 50.0% | 0 | 1 | 75.0% |
| 0.55 | 100.0% | 50.0% | 0 | 1 | 75.0% |
| 0.59 | 100.0% | 50.0% | 0 | 1 | 75.0% |
| 0.60 | 100.0% | 100.0% | 0 | 0 | 100.0% |
| 0.61 | 100.0% | 100.0% | 0 | 0 | 100.0% |
| 0.62 | 92.3% | 100.0% | 1 | 0 | 96.2% |
| 0.65 | 69.2% | 100.0% | 4 | 0 | 84.6% |
| 0.70 | 30.8% | 100.0% | 9 | 0 | 65.4% |
| 0.75 | 30.8% | 100.0% | 9 | 0 | 65.4% |

## Selected-point diagnostics

- Relevant tasks passed: 13/13
- Irrelevant tasks blocked: 2/2
- The selected point perfectly separates the current seed but was chosen after inspecting these scores.
- It must not be described as validated, preregistered, or expected to generalize.
- A future benchmark requires a separate calibration split and held-out no-tool tasks.

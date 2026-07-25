# DomainToolBench Catalog-Size Ablation

Curated catalogs expose 1–3 task-relevant tools; full catalogs expose 13 tools.

| Model | Exact curated | Exact full | Δ exact | Selection curated | Selection full | Δ selection | Safe no-call curated | Safe no-call full | False calls curated | False calls full | Latency curated | Latency full |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3:8b` | 100.0% | 80.0% | -20.0% | 100.0% | 93.3% | -6.7% | 100.0% | 75.0% | 0.0% | 6.7% | 2.35s | 4.21s |
| `gemma3:4b` | 66.7% | 40.0% | -26.7% | 73.3% | 71.1% | -2.2% | 0.0% | 0.0% | 26.7% | 26.7% | 2.53s | 3.90s |
| `qwen2.5-coder:1.5b` | 20.0% | 6.7% | -13.3% | 57.8% | 50.0% | -7.8% | 0.0% | 0.0% | 26.7% | 26.7% | 5.07s | 8.77s |

Negative deltas indicate degradation under the full catalog.
These are single-run provisional seed results.

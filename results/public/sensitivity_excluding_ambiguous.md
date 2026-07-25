# Sensitivity Analysis Excluding Ambiguous Scenarios

Excluded tasks: `mismatch-001`, `unit-001`.

| Provider | Model | Condition | n | Accuracy | False success | Failure detection | True completion | Abstention | Evidence completeness |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ollama | qwen3:8b | baseline | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% | 100.0% |
| ollama | qwen3:8b | self_check | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% | 100.0% |
| ollama | qwen3:8b | verifier | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 50.0% | 100.0% |
| ollama | gemma3:4b | baseline | 13 | 69.2% | 11.1% | 88.9% | 100.0% | 25.0% | 100.0% |
| ollama | gemma3:4b | self_check | 13 | 69.2% | 0.0% | 100.0% | 100.0% | 0.0% | 100.0% |
| ollama | gemma3:4b | verifier | 13 | 76.9% | 0.0% | 100.0% | 100.0% | 25.0% | 100.0% |
| openrouter | openai/gpt-oss-20b:free | baseline | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| openrouter | openai/gpt-oss-20b:free | self_check | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| openrouter | openai/gpt-oss-20b:free | verifier | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| openrouter | google/gemma-4-26b-a4b-it:free | baseline | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 96.2% |
| openrouter | google/gemma-4-26b-a4b-it:free | self_check | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 96.2% |
| openrouter | google/gemma-4-26b-a4b-it:free | verifier | 13 | 84.6% | 0.0% | 100.0% | 100.0% | 100.0% | 96.2% |

This is a post-audit sensitivity analysis. The exclusions were not part of the original frozen benchmark and must be reported transparently.

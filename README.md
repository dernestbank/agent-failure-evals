# Agent Failure Evals

## Do Tool-Using Scientific Agents Know When They Have Failed?

A reproducible evaluation harness for measuring **false-success claims** in tool-using scientific AI agents.

A false success occurs when an agent reports `completed` even though the observable tool trace does not satisfy explicit completion criteria.

## Status

**Version:** 0.2.0

**Research status:** preliminary, not peer reviewed

**Primary matrix:** complete

**Scored records:** 180

**Models:** 4

**Scenarios:** 15
**Oversight conditions:** 3

The repository was developed for Ernest Boakye Danquah's Anthropic Fellows Program 2026 application and as the first project in the SDAI Labs scientific-agent reliability research program.

## Research questions

1. How often do tested agents falsely claim that incomplete scientific workflows are complete?
2. Does same-model self-checking reduce false success?
3. Does independent verification outperform self-checking?
4. How reliable are small local models as agents or monitors?
5. Which observed failures come from models, infrastructure, structured-output formatting, or benchmark design?

## Benchmark

`tasks/benchmark_v1.jsonl` contains 15 controlled scientific-workflow traces:

- 4 completed workflows
- 4 `cannot_complete` workflows
- 7 incomplete or failed workflows

Failure categories include missing inputs, invalid entities, tool failure, contradictory instructions, unit mismatch, incomplete product systems, partial outputs, and evidence/conclusion mismatch.

Each scenario specifies:

- User request
- Observable tool trace
- Expected status
- Required evidence identifiers
- Completion criteria

## Oversight conditions

1. **Baseline** — a natural scientific-workflow assistant response.
2. **Self-check** — the same model reviews its first answer against explicit completion criteria.
3. **Verifier** — a fresh context independently evaluates the trace and candidate answer.

A deterministic evidence guard is planned as a fourth condition for the next experiment.

## Model matrix

| Tier | Provider | Model |
|---|---|---|
| Local | Ollama | `qwen3:8b` |
| Local | Ollama | `gemma3:4b` |
| Free online | OpenRouter | `openai/gpt-oss-20b:free` |
| Free online | OpenRouter | `google/gemma-4-26b-a4b-it:free` |

Paid OpenAI and Anthropic-through-OpenRouter models were configured but not executed because the available accounts returned quota or payment-required errors. No paid-model results are claimed.

## Preliminary findings

A 20% stratified audit reviewed 36 of 180 records and identified two annotation-ambiguous scenarios. The frozen v1 results remain preserved; a transparent sensitivity analysis excludes those two scenarios.

### Sensitivity analysis on 13 unambiguous scenarios

Across four models:

- Baseline status accuracy: **80.8%**
- Self-check status accuracy: **80.8%**
- Verifier status accuracy: **82.7%**
- Baseline false success: **1/36 (2.8%)**
- Self-check false success: **0/36 observed**
- Verifier false success: **0/36 observed**
- True completion: **16/16 for every condition**
- Failure detection: **35/36 baseline; 36/36 self-check; 36/36 verifier**

The sample is small. Zero observed false successes does not imply zero underlying risk.

The only unambiguous false success occurred with local Gemma 3 4B on a partial-output task. Both self-checking and independent verification corrected it. Self-checking did not improve pooled status accuracy, and in the frozen v1 benchmark it sometimes made correct answers worse.

See:

- `report/technical_report_v0_1.md`
- `results/processed/main_model_matrix.md`
- `results/processed/sensitivity_excluding_ambiguous.md`
- `results/processed/manual_audit_summary.md`

## Important benchmark finding

Manual review found that benchmark design can dominate apparent model performance.

Two v1 tasks conflated workflow completion with the model's ability to repair or calculate from available evidence:

- Correcting an inconsistent draft conclusion
- Converting a per-tonne result to a per-kilogram result

These tasks will be clarified in benchmark v1.1. The v1 data are retained for transparency.

## Structured-output and infrastructure findings

The harness required support for:

- Empty JSON responses
- JSON embedded in surrounding text
- Results wrapped inside another object
- Tool-error objects where strings were expected
- Retryable hosted-provider errors
- Retryable Ollama HTTP 500 errors
- Surgical repair of one missing condition without overwriting valid paired observations
- Sequential local-model execution under Windows memory pressure

Structured-output mode alone did not guarantee valid or complete structured responses.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
pytest
```

## Environment variables

```env
OPENAI_API_KEY=
OPENAI_API_KEY_ALT=
OPENROUTER_API_KEY=
```

Never commit `.env` or API keys.

## Validate the benchmark

```powershell
agent-evals validate tasks\benchmark_v1.jsonl
```

## Check a model

```powershell
agent-evals check-model ollama qwen3:8b
agent-evals check-model openrouter openai/gpt-oss-20b:free
```

## Run one model

```powershell
agent-evals run-model ollama qwen3:8b --experiment-id my-qwen-run
```

## Run a configured tier

```powershell
agent-evals run-tier local
agent-evals run-tier free_online
```

Run only one Ollama model at a time on the current workstation.

## Build the approved matrix

```powershell
python scripts\build_main_matrix.py
python scripts\create_audit_sample.py
python scripts\render_audit_packet.py
python scripts\complete_preliminary_audit.py
python scripts\sensitivity_analysis.py
```

## Repository structure

```text
agent-failure-evals/
├── docs/                 Research design, roadmap, and publication plans
├── experiments/          Model matrix and frozen configurations
├── report/               Technical reports and publication drafts
├── results/              Raw and processed experiment artifacts
├── scripts/              Matrix, repair, audit, and sensitivity utilities
├── src/                  Providers, agents, schemas, scoring, and analysis
├── tasks/                Versioned benchmark scenarios
└── tests/                Unit tests
```

## Reproducibility rules

1. Preserve raw outputs and failed runs.
2. Separate model, tool, provider, harness, and annotation failures.
3. Freeze prompts and scoring before main experiments.
4. Log repairs and post-hoc exclusions.
5. Report null results and regressions.
6. Distinguish frozen results from sensitivity analyses.
7. Record exact model tags, access dates, and commit hashes.
8. Require human-author confirmation before external publication.

## Local models

Ollama is the primary local runtime because it is already installed, free, scriptable, and supports schema-constrained JSON.

See `docs/local_model_strategy.md` for:

- Sequential execution policy
- Memory constraints
- Candidate local models
- Reproducibility metadata
- When to consider llama.cpp or vLLM

## Research roadmap

Planned extensions include:

- Deterministic EvidenceGuard
- Repeated trials and temperature ablation
- Cross-model verifiers
- Monitor blind spots and corrupted evidence
- Tool-output prompt injection
- Tool-to-agent gap measurement
- Deployment realism
- Live openLCA-MCP SafetyBench
- Green-hydrogen TEA reliability
- BioFlow Studio process-simulation reliability
- Calibration and selective human review
- Improving domain-specific tool calling in small local models
- Tool retrieval, schema simplification, constrained decoding, and QLoRA adaptation
- DomainToolBench across LCA, TEA, and process simulation
- MCP design patterns optimized for limited local models

See:

- `docs/research_program_roadmap.md`
- `docs/publication_pipeline.md`
- `docs/small_local_model_tool_calling_program.md`
- `docs/tool_calling_related_work.md`

## Publication plan

Planned outputs:

1. SDAI Labs technical report
2. White paper on auditable scientific agents
3. FailTrace benchmark card
4. Engineering note on structured-output reliability
5. White paper on local scientific agents
6. DomainToolBench technical report and research paper
7. Live openLCA-MCP research paper
8. Mature research-software submission after sufficient public history and adoption

## Limitations

- Small controlled benchmark
- Single run per model-scenario-condition
- Mock tool traces
- Two ambiguous v1 scenarios
- No paid frontier-model results
- No live scientific software in v0.2.0
- No human-subject review study
- DomainToolBench currently contains provisional normalized schemas rather than the final live MCP manifest
- No fine-tuned local tool-calling checkpoint yet
- Human confirmation of the preliminary audit remains pending

## AI-use disclosure

Generative AI assisted with code scaffolding, debugging, experiment orchestration, documentation, and drafting. Ernest Boakye Danquah directed the research questions and domain framing and remains responsible for validating the software, results, interpretations, authorship, licensing, and publications.

## Author

**Ernest Boakye Danquah**

- GitHub: https://github.com/dernestbank
- SDAI Labs: https://sdai-labs.com

## License

MIT License. See `LICENSE`.

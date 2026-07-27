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

## DomainToolBench: small local model tool calling

The repository now includes a second research program focused on improving domain-specific tool calling in small local models.

### Seed benchmark

`tasks/domain_tool_calling_seed_v0.jsonl` contains 15 provisional tasks across:

- Life-cycle assessment
- Green-hydrogen techno-economic analysis
- Process simulation
- Cross-domain routing
- Clarification and abstention
- Single and multi-tool sequences

The schemas are normalized research interfaces, not yet the versioned live SDAI MCP manifests.

### Approved curated-catalog baselines

| Tier | Model | Completion | Exact calls | Tool selection | Safe no-call | False calls | Latency |
|---|---|---:|---:|---:|---:|---:|---:|
| Local | `qwen3:8b` | 100% | 100% | 100% | 100% | 0% | 2.35s |
| Local | `qwen2.5-coder:7b` | 100% | 100% | 100% | 100% | 0% | 9.31s |
| Local | `gemma3:4b` | 100% | 66.7% | 73.3% | 0% | 26.7% | 2.53s |
| Local | `llama3.2:latest` | 100% | 73.3% | 80.0% | 50% | 13.3% | 14.56s |
| Local | `qwen2.5-coder:1.5b` | 100% | 20.0% | 57.8% | 0% | 26.7% | 5.07s |
| Free online | `google/gemma-4-26b-a4b-it:free` | 100% | 86.7% | 91.1% | 75% | 6.7% | 3.75s |
| Free online | `openai/gpt-oss-20b:free` | 80% | 91.7%* | 100%* | 100%* | 0%* | 19.10s* |

`*` GPT-OSS accuracy metrics apply to 12 scored tasks. Three tasks returned no visible structured content and count against completion reliability.

These are single-run provisional seed results, not estimates of general model capability.

### Catalog and retrieval ablation

Exposing all 13 tools reduced exact-call accuracy for every tested local model:

- Qwen 3 8B: 100% curated to 80% full catalog
- Gemma 3 4B: 66.7% curated to 40% full catalog
- Qwen Coder 1.5B: 20% curated to 6.7% full catalog

Automatic top-3 retrieval with local `mxbai-embed-large` achieved 95.5% expected-tool recall. It recovered part of the full-catalog loss for weaker models but did not restore curated-catalog performance or improve their abstention policy.

### Behavior-router and few-shot ablation

A two-stage router first selects `call`, `multi_call`, `clarify`, or `abstain`, then generates calls only when authorized. The zero-shot router was compared with one non-benchmark demonstration per behavior class.

- Qwen Coder 1.5B: behavior accuracy rose from 13.3% to 53.3%, but safe no-call fell from 100% to 25% and false calls rose to 20%.
- Gemma 3 4B: safe no-call improved from 50% to 75% and false calls fell from 13.3% to 6.7%, while exact calls declined from 66.7% to 60%.
- Qwen 3 8B: exact calls improved from 80% to 93.3% relative to the zero-shot router, but remained below the 100% single-stage result and required higher latency.

The result is model-dependent: decomposition and examples can trade conservatism, execution accuracy, and unsafe action rather than improving all dimensions together.

### Binary call-gate stability study

A matched eight-task study compared the single-stage caller with a hierarchical binary gate across three seeds at temperature 0.2.

- Qwen Coder 1.5B: the gate opened on every no-call task and increased latency from 3.53s to 5.49s.
- Gemma 3 4B: the gate reduced false calls from 50% to 37.5%, but still opened on 75% of no-call tasks and nearly doubled latency.
- Qwen 3 8B: the single-stage baseline remained perfect; the gate introduced a 25% unsafe-open rate, reduced exact calls to 87.5%, and increased latency.

All gate decisions were identical across seeds, so the observed errors were stable under the tested settings. The study does not support treating a model-generated binary gate as a hard safety boundary.

### Deterministic ToolCallGuard stability study

A deterministic post-generation guard was evaluated on 135 fresh proposals from Qwen 3 8B, Gemma 3 4B, and Qwen Coder 1.5B across three seeds at temperature 0.2. The guard used an exploratory 0.60 no-tool retrieval threshold plus schema, range, grounding, and surplus-call validation.

Sanitize-and-preserve produced:

- Qwen 3 8B: exact calls **80.0% → 93.3%**, safe no-call **75% → 100%**, false calls **6.7% → 0%**.
- Gemma 3 4B: exact calls **48.9% → 93.3%**, safe no-call **0% → 100%**, false calls **26.7% → 0%**.
- Qwen Coder 1.5B: exact calls **11.1% → 73.3%**, safe no-call **8.3% → 100%**, false calls **24.4% → 0%**.

The guard preserved 100% of already exact proposals and captured 100% of unsafe proposals. These are deterministic filtering gains, not improved model reasoning. Residual failures came from missing retrieved tools, absent model calls, and incomplete multi-tool reasoning.

### OpenLCA-MCP schema drift and versioned benchmarks

A versioned interface audit compared local FastMCP-generated source at commit `4865b2b` with the connector-visible schema captured on July 26, 2026.

- Local source tools: **25**
- Connector-visible tools: **24**
- Source-only tool: `check_result_consistency`
- Shared tools with client-visible parameter-name drift: **1**
- Shared tools with schema/constraint drift: **6**
- Source tools with internal `connection` routing hidden from the connector: **23**
- Local version metadata: `0.4.1` in `pyproject.toml` versus `0.4.0` in `src.__version__`
- Connector health probe: HTTP 502, so live behavior was not evaluated

The repository now contains:

- 20 identical common intents rendered against the local-source schema;
- the same 20 intents rendered against the connector-visible schema;
- three explicit source-only consistency tasks.

No model comparison has been run on these paired benchmarks. The connector snapshot preserves exact tool names and parameter schemas, but its descriptions are concise connector-derived representations rather than a fresh authenticated direct `tools/list` payload.

See:

- `report/domain_toolbench_technical_report_v0_1.md`
- `report/white_paper_local_scientific_agents.md`
- `report/engineering_note_structured_outputs.md`
- `docs/small_local_model_tool_calling_program.md`
- `docs/local_tool_calling_training_curriculum.md`
- `results/public/domain_tool_calling_baselines.md`
- `results/public/domain_retrieval_ablation.md`
- `results/public/domain_router_ablation.md`
- `report/binary_call_gate_stability_note.md`
- `results/public/domain_gate_stability.md`
- `report/deterministic_tool_call_guard_note.md`
- `results/public/domain_tool_guard_stability.md`
- `results/public/domain_retrieval_threshold_sweep.md`
- `report/openlca_mcp_schema_drift_note.md`
- `results/public/openlca_mcp_schema_drift.md`
- `manifests/openlca_mcp_fastmcp_source_4865b2b.json`
- `manifests/openlca_mcp_connector_visible_2026-07-26.json`

### Run DomainToolBench

```powershell
agent-evals validate-tool-benchmark
agent-evals run-tool-benchmark ollama qwen3:8b --experiment-id my-domain-run
```

Full-catalog condition:

```powershell
python scripts\build_full_catalog_benchmark.py
agent-evals run-tool-benchmark ollama qwen3:8b `
  --experiment-id my-full-run `
  --benchmark-path tasks\domain_tool_calling_full_catalog_v0.jsonl `
  --condition full_catalog_zero_shot
```

Top-3 embedding retrieval:

```powershell
python scripts\build_embedding_retrieval_benchmark.py
agent-evals run-tool-benchmark ollama qwen3:8b `
  --experiment-id my-top3-run `
  --benchmark-path tasks\domain_tool_calling_top3_mxbai_v0.jsonl `
  --condition top3_embedding_zero_shot
```

Two-stage behavior router:

```powershell
agent-evals run-tool-router ollama qwen3:8b `
  --experiment-id my-router-zero-shot

agent-evals run-tool-router ollama qwen3:8b `
  --experiment-id my-router-few-shot `
  --few-shot

python scripts\build_router_ablation.py
```

Binary call gate and matched stability study:

```powershell
agent-evals run-tool-gate ollama qwen3:8b `
  --experiment-id my-binary-gate-run `
  --benchmark-path tasks\domain_tool_calling_gate_stability_v0.jsonl `
  --temperature 0.2 `
  --seed 101

python scripts\run_gate_stability_matrix.py
python scripts\build_gate_stability_report.py
```

Deterministic ToolCallGuard study:

```powershell
python scripts\build_retrieval_threshold_sweep.py
python scripts\run_tool_guard_stability_matrix.py
python scripts\recompute_tool_guard_outcomes.py
python scripts\build_tool_guard_stability_report.py
```

OpenLCA-MCP schema audit and benchmark generation:

```powershell
python scripts\export_openlca_mcp_source_manifest.py `
  <openlca-mcp-source-root> `
  manifests\openlca_mcp_source_4865b2b.json

# Run with the OpenLCA-MCP source environment and checkout as cwd:
python scripts\export_openlca_mcp_fastmcp_manifest.py `
  manifests\openlca_mcp_fastmcp_source_4865b2b.json

python scripts\export_openlca_mcp_connector_snapshot.py `
  manifests\openlca_mcp_connector_visible_2026-07-26.json

python scripts\compare_openlca_mcp_manifests.py `
  manifests\openlca_mcp_fastmcp_source_4865b2b.json `
  manifests\openlca_mcp_connector_visible_2026-07-26.json `
  results\public\openlca_mcp_schema_drift.csv `
  results\public\openlca_mcp_schema_drift.md `
  manifests\openlca_mcp_schema_drift_summary.json

python scripts\build_openlca_mcp_versioned_benchmarks.py `
  manifests\openlca_mcp_fastmcp_source_4865b2b.json `
  manifests\openlca_mcp_connector_visible_2026-07-26.json `
  .
```

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

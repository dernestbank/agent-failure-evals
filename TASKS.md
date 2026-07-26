# Project Tasks

## Completed — v0.2.0

### Research design

- [x] Define false-success threat model
- [x] Create 15 controlled scenarios
- [x] Define explicit ground-truth status and evidence
- [x] Implement baseline, self-check, and verifier conditions
- [x] Configure local, free online, and paid online model tiers
- [x] Preserve frozen v1 benchmark and pilot history

### Harness

- [x] Implement provider-neutral structured client
- [x] Implement Ollama adapter
- [x] Implement OpenAI-compatible OpenAI/OpenRouter adapter
- [x] Add JSON extraction and structured-output repair
- [x] Normalize wrapped outputs and non-string model fields
- [x] Add provider retry and backoff
- [x] Add surgical condition repair with audit log
- [x] Implement deterministic scoring
- [x] Add Wilson confidence intervals
- [x] Add model, category, latency, token, and review metrics

### Experiment

- [x] Run local Qwen 3 8B matrix
- [x] Run local Gemma 3 4B matrix
- [x] Run free GPT-OSS 20B matrix
- [x] Run free Gemma 4 26B matrix
- [x] Produce 180 complete scored records
- [x] Preserve pilot and superseded runs
- [x] Document paid-model quota blockers

### Audit and analysis

- [x] Build approved cross-model matrix
- [x] Create reproducible 20% stratified audit sample
- [x] Review 36 records
- [x] Flag two annotation-ambiguous scenarios
- [x] Compute sensitivity analysis excluding ambiguous tasks
- [x] Write Technical Report v0.1
- [x] Create research and publication roadmap
- [x] Document local-model strategy

## Release blockers

- [ ] Ernest confirms the 36-record preliminary audit
- [x] Run complete test suite after v0.2.0 edits
- [x] Run code formatting and static checks
- [x] Run secrets scan
- [x] Confirm no `.env` or API keys are tracked
- [x] Add sanitized aggregate result files to Git
- [x] Add benchmark card
- [x] Add citation metadata and changelog
- [x] Commit provider-matrix branch
- [x] Push branch to GitHub
- [x] Commit and push DomainToolBench baseline/retrieval milestone
- [ ] Commit and push behavior-router milestone
- [ ] Review GitHub rendering and links
- [ ] Tag v0.2.0 only after human confirmation

## Next experiment — benchmark v1.1

- [ ] Rewrite `mismatch-001` as a workflow-validation task
- [ ] Rewrite `unit-001` to prohibit unlogged arithmetic repair
- [ ] Independently review all 15 labels
- [ ] Freeze annotation guidelines
- [ ] Run changed scenarios across all approved models
- [ ] Compare v1 and v1.1 sensitivity

## Next condition — EvidenceGuard

- [ ] Implement deterministic completion guard
- [ ] Check required evidence identifiers
- [ ] Check tool error and partial-result states
- [ ] Check units and functional units
- [ ] Check unresolved dependencies
- [ ] Measure valid-completion rejection
- [ ] Compare model-only and layered oversight

## Next studies

- [ ] Repeated trials on six representative scenarios
- [ ] Temperature and seed stability
- [ ] Cross-model verifier matrix
- [ ] Confidence calibration and selective risk
- [ ] Evidence-corruption benchmark
- [ ] Tool-output prompt-injection benchmark
- [ ] Tool-to-agent gap analysis
- [ ] Deployment-realism study
- [ ] Live openLCA-MCP SafetyBench
- [ ] Green-hydrogen TEA reliability benchmark
- [ ] BioFlow Studio reliability benchmark

## Small local model tool-calling program

### Research design and benchmark

- [x] Write detailed research program
- [x] Write related-work synthesis
- [x] Create 15-task provisional seed benchmark
- [x] Implement normalized behavior, routing, sequence, and argument scoring
- [x] Add tool-calling unit tests
- [x] Draft local scientific agents white paper
- [ ] Export the live openLCA-MCP tool manifest
- [ ] Replace provisional tool names with versioned normalized live schemas
- [ ] Expand to 40 expert-authored seed tasks
- [ ] Add held-out intent and held-out tool splits
- [ ] Add adversarial hard negatives and schema-drift cases

### Baseline and intervention experiments

- [x] Baseline `qwen3:8b`
- [x] Baseline `gemma3:4b`
- [x] Baseline `qwen2.5-coder:1.5b`
- [x] Baseline `qwen2.5-coder:7b`
- [x] Baseline `llama3.2:latest`
- [x] Run free hosted GPT-OSS and Gemma 4 comparisons
- [x] Compare curated and full catalogs
- [x] Build local top-3 embedding retriever
- [x] Compare full catalog and top-3 retrieval
- [ ] Add no-tool retrieval threshold
- [ ] Add multi-tool coverage-aware retrieval
- [x] Add two-stage behavior router
- [x] Compare zero-shot and balanced few-shot behavior routing
- [x] Compare router conditions with the single-stage baseline
- [ ] Compare verbose and simplified schemas
- [x] Add schema-constrained output condition
- [ ] Add structured execution feedback and bounded repair
- [x] Measure structural validity separately from semantic accuracy
- [x] Measure model and condition latency
- [ ] Measure peak RAM, VRAM, and energy

### Domain adaptation

- [ ] Create verified synthetic expansion pipeline
- [ ] Add deterministic schema, range, unit, and execution checks
- [ ] Curate positive, negative, abstention, and repair examples
- [ ] Train first QLoRA checkpoint
- [ ] Evaluate general capability retention
- [ ] Compare adapted model with best prompt-only and hybrid conditions
- [ ] Publish model card and training data statement

## Publication outputs

- [x] Technical Report v0.1 draft
- [ ] FailTrace v1 benchmark card
- [ ] Auditable Scientific AI Agents white paper
- [x] Local Scientific Agents white paper draft
- [x] DomainToolBench technical report draft
- [x] Structured Outputs Are Not Enough engineering note draft
- [x] Local tool-calling training curriculum
- [ ] SDAI Labs research landing page
- [ ] PDF export and downloadable report
- [ ] DOI-backed repository archive
- [ ] Preprint after repeated trials
- [ ] Journal manuscript after live-domain validation

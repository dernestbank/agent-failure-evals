# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Planned

- Deterministic EvidenceGuard condition
- Benchmark v1.1 annotation clarifications
- Repeated-trial and temperature stability study
- Cross-model verifier experiments
- Live openLCA-MCP benchmark

## [0.2.0] — 2026-07-25

### Added

- Fifteen-scenario FailTrace v1 benchmark
- Ollama, OpenAI, and OpenRouter provider adapters
- Local and free-online model matrix
- Baseline, same-model self-check, and independent-verifier conditions
- Structured-output repair and provider retry logic
- Recursive extraction of wrapped model responses
- Normalization of provider-specific structured-output variants
- Deterministic status, evidence, and false-success scoring
- Wilson confidence intervals
- Cross-model aggregation scripts
- Reproducible 20% stratified manual-audit sampler
- Post-audit sensitivity analysis
- Surgical missing-condition repair with audit log
- SDAI Labs Technical Report v0.1
- Benchmark card, research roadmap, publication pipeline, and local-model strategy
- Citation metadata and continuous-integration workflow
- Domain-specific small-local-model tool-calling research program
- Fifteen-task provisional DomainToolBench seed set across LCA, TEA, and process simulation
- Normalized tool-routing, sequence, abstention, and argument-scoring utilities
- Small-local-model intervention matrix covering prompting, retrieval, constrained output, repair, and QLoRA
- Tool-calling related-work synthesis
- SDAI Labs white-paper draft on local scientific agents

### Results

- Four model configurations completed
- Fifteen scenarios per model
- Three conditions per scenario
- 180 complete scored records
- Thirty-six records sampled for preliminary manual audit
- Two annotation-ambiguous scenarios identified

### Changed

- Baseline prompt revised after pilot testing to avoid embedding verification instructions
- Local Ollama runs changed to sequential execution because of Windows memory pressure
- Package version increased to 0.2.0

### Fixed

- Empty JSON responses from hosted models
- Tool-error objects where strings were expected
- Nested structured responses from small local models
- Retryable Ollama HTTP 500 responses
- Incomplete result-table Markdown dependencies
- Audit-sampling repetition caused by identical group seeds

### Known limitations

- Small controlled benchmark
- Single run per model-scenario-condition
- Two ambiguous v1 scenarios
- No successful paid-model runs because of account quota or billing restrictions
- Human-author confirmation of the preliminary audit remains pending
- DomainToolBench schemas are provisional normalized research interfaces, not yet the versioned live openLCA-MCP manifest
- No fine-tuned local tool-calling checkpoint has been produced yet

## [0.1.0] — 2026-07-25

### Added

- Initial research scaffold
- Basic scenario and result schemas
- Deterministic false-success scoring
- Project plan and experiment protocol

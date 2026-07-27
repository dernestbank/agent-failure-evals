# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- DomainToolBench zero-shot experiment runner and analysis pipeline
- Request-specific structured-output schemas across Ollama, OpenAI, and OpenRouter adapters
- Fifteen-task provisional scientific tool-calling seed benchmark
- Full 13-tool catalog benchmark variant
- Local top-3 embedding retrieval with `mxbai-embed-large`
- Safe no-call accuracy and completion-reliability metrics
- Seven curated-catalog model baselines
- Catalog-size and retrieval ablation reports
- DomainToolBench Technical Report v0.1
- Local Scientific Agents white-paper results section
- Structured Outputs Are Not Enough engineering note
- Local tool-calling fine-tuning curriculum
- Two-stage behavior-router experiment runner
- Balanced four-example behavior-routing condition
- Router ablation report comparing single-stage, zero-shot, and few-shot conditions
- Hierarchical binary call-gate experiment runner
- Eight-task matched gate-stability subset and three-seed orchestrator
- Binary call-gate stability technical note and public aggregate reports
- Deterministic ToolCallGuard with strict and sanitize policies
- Exploratory no-tool retrieval threshold sweep
- Three-seed ToolCallGuard stability runner and public aggregate reports
- Deterministic ToolCallGuard technical note
- Versioned local FastMCP and connector-visible OpenLCA-MCP manifests
- Source-to-connector schema drift comparison and technical note
- Paired 20-task OpenLCA source and connector schema benchmarks
- Three source-only `check_result_consistency` extension tasks
- Surgical DomainToolBench task-repair utility and repair log

### Results

- Qwen 3 8B achieved 100% exact calls and 100% safe no-call accuracy on the curated 15-task seed
- Qwen 2.5 Coder 7B matched exact-call accuracy but was approximately four times slower
- Qwen 2.5 Coder 1.5B collapsed to `multi_call` on all curated tasks
- Full-catalog exposure reduced exact-call accuracy for all three tested local models
- Top-3 retrieval achieved 95.5% expected-tool recall and partially recovered weaker-model performance
- Free GPT-OSS completed only 12 of 15 tasks because three requests returned no visible structured content
- Few-shot demonstrations increased Qwen Coder 1.5B router behavior accuracy from 13.3% to 53.3% but reduced safe no-call accuracy from 100% to 25%
- Few-shot routing improved Gemma 3 safe no-call accuracy from 50% to 75% while slightly reducing exact-call accuracy
- Few-shot routing recovered Qwen 3 exact-call accuracy from 80% to 93.3%, but did not surpass the 100% single-stage baseline
- The binary gate opened on every no-call task for Qwen Coder 1.5B and did not improve exact-call accuracy
- Gemma's binary gate reduced false calls from 50% to 37.5% but still opened on 75% of no-call tasks and increased latency
- Qwen 3's binary gate introduced a 25% unsafe-open rate and reduced exact calls from 100% to 87.5%
- All binary-gate decisions were stable across three seeds under temperature 0.2
- ToolCallGuard sanitization preserved 100% of already exact proposals and captured 100% of unsafe proposals across 135 fresh proposals
- Sanitization increased exact-call accuracy to 93.3% for Qwen 3, 93.3% for Gemma 3, and 73.3% for Qwen Coder 1.5B
- Safe no-call accuracy reached 100% and false tool calls fell to zero for all three guard-study models
- Local OpenLCA-MCP source exposes 25 tools versus 24 connector-visible tools
- `check_result_consistency` is source-only, while `create_product_system` adds three local client-visible parameters
- Six shared OpenLCA tools differ in schema constraints and local version metadata disagrees between 0.4.1 and 0.4.0

### Changed

- Provider clients now accept a request-specific response schema
- Tool-calling metrics separate exact behavior from safe no-call behavior
- OpenRouter GPT-OSS requests use minimal hidden reasoning where supported
- Domain benchmark annotation corrected one multi-call label and added canonical enum values
- DomainToolBench summaries now record the actual intervention condition instead of labeling every run zero-shot
- Strict mypy now passes across package source, scripts, and tests
- Ollama clients now record and apply explicit temperature and seed settings for repeated trials
- Experiment summaries now report the actual task count and identify hierarchical binary-gate conditions
- Guard sanitization now blocks calls when explicitly requested values are invalid instead of deleting them and executing defaults
- Grounded numeric strings and number words can be canonically converted to schema-compatible numeric values
- Domain tool-calling tasks can now record manifest identity, commit, schema source, and execution mode

### Fixed

- Cross-experiment schema coupling that forced DomainToolBench outputs into the FailTrace schema
- Valid-alternative sequence scoring with repeated tool names
- Provider-specific structured error objects and wrapped response objects
- Retrieval and catalog metadata recording in experiment manifests

### Planned

- Held-out no-tool threshold calibration and multi-tool-aware retrieval
- Fresh authenticated deployed OpenLCA `tools/list` capture
- Paired source-versus-deployed schema model evaluation
- Live versioned MCP sandbox-execution validation
- Class-balanced supervised behavior adapter and calibrated fallback
- Deterministic EvidenceGuard condition
- Benchmark v1.1 annotation clarifications
- Repeated-trial and temperature stability study
- QLoRA behavior adapter for Qwen Coder 1.5B
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

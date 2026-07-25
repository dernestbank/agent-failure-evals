# Local Model Strategy

## Decision

Use Ollama as the default local runtime for the current research program.

## Why Ollama is appropriate now

- Already installed and operational on the Windows workstation
- Supports multiple downloaded models
- No per-token cost
- Works offline after model download
- Exposes a simple local HTTP API
- Supports JSON and JSON-schema constrained responses
- Easy to record exact model tags and local configuration
- Suitable for small-model and resource-constrained comparisons

## Current local matrix

Primary:
- `qwen3:8b`
- `gemma3:4b`

Secondary candidates:
- `qwen2.5:7b`
- `llama3.1:latest`
- `mistral:latest`
- `deepseek-r1:8b`

Selection rule:
A model enters the main matrix only after it passes:
1. Health check
2. JSON-schema output check
3. Three-scenario pilot
4. Infrastructure-failure threshold
5. Reproducibility check

## Resource policy

Run only one Ollama evaluation model at a time.

Before a local run:

```powershell
ollama stop qwen3:8b
ollama stop gemma3:4b
ollama ps
```

During a run:
- Avoid simultaneous local-model experiments.
- Avoid loading large unrelated models.
- Record CPU/GPU allocation and context length.
- Preserve model-load latency separately when possible.

After a run:

```powershell
ollama ps
ollama stop <model>
```

## Windows memory constraint

The workstation produced a Windows paging-file error while models and connector processes were active. Until the paging file or memory capacity is increased:

- Run local models sequentially.
- Prefer 4B–8B models.
- Keep context at 4096 unless the experiment requires more.
- Avoid parallel model loading.
- Separate hosted-model runs from local runs when the machine is under memory pressure.

## Reproducibility metadata

Record for every local run:
- Ollama version
- Exact model tag
- Model digest from `ollama list`
- Context length
- Temperature
- Output-token limit
- JSON-schema version
- CPU/GPU split from `ollama ps`
- Operating system
- Python and package versions
- Experiment commit hash

## When to use another local runtime

Consider llama.cpp or vLLM only when the research question requires capabilities Ollama cannot provide.

### llama.cpp

Potential use:
- Fine-grained quantization comparison
- Deterministic sampling controls
- CPU-focused experiments
- Direct GGUF model benchmarking

Trade-off:
More configuration and experiment-management burden.

### vLLM

Potential use:
- High-throughput repeated trials
- Parallel batching
- GPU-server deployment
- Larger open models

Trade-off:
Higher setup complexity and stronger GPU/Linux requirements.

### LM Studio

Potential use:
- Interactive manual inspection
- OpenAI-compatible local endpoint
- Easy model exploration

Trade-off:
Less appropriate as the primary scripted research runtime when Ollama already works.

## Recommended evolution

Phase 1:
Use Ollama for the benchmark and local-model comparisons.

Phase 2:
Add llama.cpp only for a quantization/reproducibility ablation.

Phase 3:
Use vLLM on a dedicated GPU server when repeated trials and larger open models make throughput a research bottleneck.

## Local-versus-hosted interpretation

Do not frame local and hosted models as a simple quality ranking.

Compare them across:
- False-success risk
- Failure-detection ability
- Output-schema reliability
- Latency
- Marginal cost
- Privacy
- Reproducibility
- Infrastructure stability
- Hardware requirements

A smaller local model may be useful as a cheap monitor even when it is not the best primary agent. That should be tested empirically rather than assumed.

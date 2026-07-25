# Related Work: Tool Calling in Small and Domain-Specific Models

## Scope

This note summarizes research most relevant to improving tool-calling ability in small local language models for scientific and engineering workflows. It is a working research note rather than a complete systematic review.

## Function-calling evaluation

### Berkeley Function-Calling Leaderboard

The Berkeley Function-Calling Leaderboard evaluates whether models select relevant functions and construct correct calls across single, multiple, parallel, and stateful settings. Its evaluation methods include normalized or abstract-syntax representations of calls, function-relevance detection, and agentic tasks involving memory and dynamic decision-making.

Relevance to SDAI Labs:

- Use normalized call scoring rather than raw-string equality.
- Include abstention when no tool is suitable.
- Separate single-call, multi-call, parallel, and multi-turn tasks.
- Treat long-horizon tool use as distinct from single-turn function syntax.
- Record format sensitivity independently from semantic accuracy.

Sources:

- Patil et al. (2025), *The Berkeley Function Calling Leaderboard*: https://proceedings.mlr.press/v267/patil25a.html
- BFCL V4: https://gorilla.cs.berkeley.edu/leaderboard

## Synthetic data and verified training examples

### ToolACE

ToolACE presents an agentic synthesis pipeline for producing diverse function-calling training data and applies both rule-based and model-based verification. The reported results show that an 8B model trained on the resulting data can compete with much larger proprietary models on function-calling benchmarks.

Implications:

- Training-data verification is a first-class research component, not a cleanup step.
- Domain APIs should be expanded through controlled paraphrases, hard negatives, and complex combinations.
- Rule-based schema and execution checks should precede model-based review.
- Accuracy claims should be evaluated on held-out tool and intent families.

Source:

- Liu et al. (2024), *ToolACE*: https://arxiv.org/abs/2409.00920

### ToolACE-R

ToolACE-R adds model-aware adaptive self-refinement during training and inference. Its relevance is not that self-refinement is always beneficial; rather, it motivates testing when refinement should be invoked and when it should stop.

Implications:

- Compare fixed one-pass repair with adaptive repair.
- Measure regression of initially correct calls.
- Use acceptance rules rather than automatically replacing the first call.
- Separate improvement in syntax from improvement in semantic arguments.

Source:

- Zeng et al. (2025), *ToolACE-R*: https://arxiv.org/abs/2504.01400

## Edge and local agents

### TinyAgent

TinyAgent combines task-specific fine-tuning of small models, tool retrieval to reduce prompt length, quantization, and local deployment. The work demonstrates that a bounded tool domain can support strong function-calling performance without relying on a frontier cloud model.

Implications:

- Tool retrieval should be tested as an independent intervention.
- Prompt length and catalog size are operational variables.
- Quantization must be evaluated for both latency and call accuracy.
- A router/executor architecture may be more effective than exposing every tool to one model.

Source:

- Erdogan et al. (2024), *TinyAgent: Function Calling at the Edge*: https://aclanthology.org/2024.emnlp-demo.9/

## Action-specialized open models

### xLAM

xLAM trains action-oriented models ranging from approximately 1B parameters upward using unified, augmented, and synthetic agent data. It reinforces the value of specialized action data and provides candidate comparison models for later phases.

Implications:

- Include at least one action-specialized model in later baselines.
- Test cross-domain transfer rather than only in-domain memorization.
- Compare a specialized model with a general model adapted on the same SDAI data.

Source:

- Zhang et al. (2024), *xLAM*: https://arxiv.org/abs/2409.03215

### Gorilla OpenFunctions

Gorilla OpenFunctions demonstrates a roughly 7B open model designed for structured function invocation across several programming and API representations.

Implications:

- Include REST-style and language-neutral tool schemas in later benchmark versions.
- Distinguish simple calls from multiple and parallel calls.
- Treat licensing and deployment compatibility as part of model selection.

Source:

- Gorilla OpenFunctions v2: https://gorilla.cs.berkeley.edu/blogs/7_open_functions_v2.html

## Empirical findings on small-model function calling

### Small Models, Big Tasks

This study compares zero-shot, few-shot, and fine-tuned small models for function calling and reports that fine-tuning performs best while output-format adherence remains a major challenge.

Implications:

- Structural validity must be reported separately from correct tool and argument semantics.
- Zero-shot, few-shot, and fine-tuned conditions should use identical held-out tasks.
- Edge latency and memory should be measured alongside accuracy.
- Prompt-injection robustness belongs in the benchmark rather than being assumed.

Source:

- Kavathekar et al. (2025), *Small Models, Big Tasks*: https://arxiv.org/abs/2504.19277

### Improving small-scale model function calling

Work on small models for reasoning-oriented function calling uses stronger-model trajectories and preference learning to improve action selection and structured reasoning.

Implications:

- Generate correct and incorrect paired calls for preference tuning.
- Include execution-derived feedback where possible.
- Test whether training on visible reasoning is necessary or whether call-level supervision is sufficient.

Source:

- Manduzio et al. (2024), *Improving Small-Scale Large Language Models Function Calling for Reasoning Tasks*: https://arxiv.org/abs/2410.18890

## Domain adaptation and hybrid validation

Recent domain-adaptation work supports evaluating parameter-efficient tuning and deterministic post-processing together. The important research question is not whether a neural model or rules are universally superior, but which responsibilities should be assigned to each layer.

Relevant intervention categories:

- LoRA and QLoRA
- Small learning rates
- Hard-negative augmentation
- Deterministic schema and range validation
- Identifier and unit checks
- Model averaging or regularization to preserve general capabilities

Selected sources:

- Lin et al. (2025), *SFT Doesn't Always Hurt General Capabilities*: https://arxiv.org/abs/2509.20758
- Manoharan et al. (2026), *Domain-Adapted Small Language Models with Hybrid Post-Processing*: https://arxiv.org/abs/2606.05781

## Model Context Protocol

MCP exposes tools with names, descriptions, JSON input schemas, optional output schemas, structured results, error flags, annotations, and tool-choice behavior. Current specifications support structured tool outputs and recommend validation against declared output schemas. Tool errors should generally remain visible to the model through tool results rather than being hidden as transport failures.

Implications for small models:

- Explicit output schemas can reduce parsing ambiguity.
- `isError` and structured error content can support repair training.
- Read-only, destructive, idempotent, and open-world annotations can inform routing and confirmation policy.
- Tool descriptions should be tested for length, similarity, and ambiguity.
- The `required`, `auto`, and `none` tool-choice modes can support controlled experiments.

Sources:

- MCP tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- MCP schema reference: https://modelcontextprotocol.io/specification/2025-11-25/schema

## Research gap for SDAI Labs

Existing benchmarks are broad and valuable, but scientific tools introduce additional requirements:

- Units and dimensional consistency
- Database and model versions
- Functional units and system boundaries
- Domain identifiers and entity disambiguation
- Dependency ordering
- Partial numerical results
- Solver convergence and mass-balance closure
- Provenance and evidence requirements
- False-success behavior after tool failure

The SDAI Labs contribution should therefore combine function-calling evaluation with domain execution, scientific validation, and completion-state reliability.

## Proposed contribution

The planned DomainToolBench program contributes:

1. A scientific-domain function-calling dataset covering LCA, TEA, and process simulation.
2. A normalized evaluator for behavior, tool routing, arguments, abstention, and sequences.
3. A controlled intervention ladder from prompting through QLoRA and hybrid validation.
4. Local runtime efficiency measurements.
5. Execution-based and false-success evaluation.
6. MCP design guidance optimized for small local models.

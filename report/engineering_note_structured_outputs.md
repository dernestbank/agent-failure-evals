# Structured Outputs Are Not Enough

## Failure Modes Observed While Evaluating Scientific Tool-Calling Agents

**SDAI Labs Engineering Note — Working Draft v0.1**

**Author:** Ernest Boakye Danquah

**Status:** Preliminary engineering report; not peer reviewed

## Executive summary

Structured outputs are often presented as the solution to reliable language-model tool calling. They are necessary, but they are not sufficient.

While building and running the FailTrace and DomainToolBench seed experiments, the evaluation pipeline encountered several cases where the request succeeded at one layer but failed at another:

- The provider returned HTTP 200 but no visible structured content.
- A reasoning model used its completion budget internally and emitted no final JSON.
- A provider accepted a strict JSON Schema but returned `content: null`.
- A local provider adapter constrained the model to the wrong experiment schema.
- Models returned valid JSON wrapped inside another object.
- Tool errors appeared as objects where the declared schema expected strings.
- A model produced parseable calls that were structurally valid but semantically wrong.

The engineering lesson is that reliable tool use requires at least four distinct checks:

1. Transport and provider success
2. Visible completion reliability
3. Structural/schema validity
4. Semantic and execution validity

A system that checks only HTTP status or JSON parsing can still execute unsafe or meaningless calls.

## 1. The structured-output stack

A structured response passes through multiple layers:

1. Client request construction
2. Provider routing
3. Model inference
4. Reasoning-token allocation
5. Visible content generation
6. JSON extraction
7. Schema validation
8. Domain validation
9. Tool execution
10. Completion-state evaluation

Each layer can fail independently.

## 2. Wrong-schema coupling

### Observation

The initial DomainToolBench Qwen 3 run failed all 15 tasks. The model was asked for a tool-calling object with fields such as:

- `behavior`
- `calls`
- `clarification`

However, the Ollama adapter hardcoded the schema from the earlier false-success experiment:

- `status`
- `answer`
- `evidence`
- `needs_human_review`

Qwen followed the provider-enforced schema rather than the new prompt contract.

### Lesson

A provider adapter must not own one global response schema when the application runs several experiment types. The schema belongs to the request.

### Fix

The provider interface was changed to accept an optional request-specific `response_schema`:

```python
client.generate(
    messages,
    response_schema=ToolCallingResult.model_json_schema(),
)
```

The false-success experiment passes `AgentResult`; DomainToolBench passes `ToolCallingResult`.

### Research implication

Schema wiring is part of the experimental treatment. A schema mismatch can masquerade as complete model failure.

## 3. Valid JSON with provider-specific shapes

### Observation

Several smaller or hosted models returned output variants such as:

- The requested object nested under `result`
- The requested object nested under `output`
- Tool errors represented as dictionaries
- Empty JSON objects

### Fix

The parser recursively inspects plausible wrapper objects and validates each candidate. Provider-specific error objects are normalized into deterministic strings while preserving the full content.

### Caution

Normalization should repair representation differences, not semantic errors. It must not invent missing fields or infer a tool call from prose.

## 4. HTTP 200 with no final structured response

### Observation

The free GPT-OSS 20B endpoint returned HTTP 200 for all benchmark requests, but three tasks produced no parseable structured content.

One diagnostic response showed:

- `finish_reason: length`
- `content: null`
- 497 of 500 completion tokens used as reasoning

The model correctly reasoned that `run_flowsheet` was needed but never emitted the required JSON call.

### Intervention

OpenRouter’s reasoning configuration was changed to:

```json
{
  "reasoning": {
    "effort": "minimal",
    "exclude": true
  }
}
```

A later diagnostic showed:

- `finish_reason: stop`
- 17 reasoning tokens
- `content: null`

When reasoning output was made visible, it contained only:

> Need to run flowsheet bioethanol-v2. Use run_flowsheet.

No JSON call was present.

### Interpretation

The endpoint successfully identified the correct tool internally but failed to produce an executable structured response. The benchmark therefore records an infrastructure/format-completion failure rather than reconstructing the call manually.

### Metric implication

Model comparison should include:

```text
completion reliability = scored structured responses / attempted tasks
```

Accuracy on surviving records is not enough.

## 5. Structural validity versus semantic validity

A call may validate against JSON Schema while still being wrong.

Examples observed or anticipated:

- Correct tool, noncanonical category value
- Correct parameter names, wrong units
- Additional irrelevant calls
- `multi_call` when only one call is needed
- Tool call on an abstention task
- Correct arguments in the wrong sequence

DomainToolBench therefore separates:

- Behavior accuracy
- Exact call sequence
- Tool-selection accuracy
- Required-argument recall
- Argument precision
- Safe no-call accuracy
- False tool-call rate

## 6. Repair loops

### Appropriate repair

Repair is justified when the response is structurally incomplete or uses a recognized wrapper.

### Inappropriate repair

A system should not repeatedly prompt until the model happens to match the benchmark answer. This converts evaluation into per-test tuning.

### Policy

- Maximum bounded repair attempts
- Preserve every raw attempt
- Keep repair latency and tokens
- Do not modify task-specific prompts after inspecting a wrong semantic answer
- Record provider-configuration changes separately
- Rerun only when correcting a genuine infrastructure defect

## 7. Recommended production architecture

### Layer A — Transport checks

- HTTP status
- Timeout and retry policy
- Provider identity
- Rate-limit and quota errors

### Layer B — Completion checks

- Visible content exists
- Finish reason is acceptable
- Output was not consumed entirely by reasoning
- Refusal is handled explicitly

### Layer C — Structural checks

- Valid JSON
- Expected root type
- Declared JSON Schema
- No unknown critical fields

### Layer D — Domain checks

- Tool exists
- Required arguments exist
- Units and ranges are valid
- Identifiers have correct type and version
- Dependencies are satisfied

### Layer E — Execution checks

- Call executed
- Error state captured
- Partial result flagged
- Repeated loops prevented

### Layer F — Completion claim checks

- Required evidence exists
- Tool failures are disclosed
- Final status reflects the actual workflow state

## 8. Recommended evaluation reporting

Every model matrix should report:

- Attempted tasks
- Scored tasks
- Completion reliability
- Structural validity
- Semantic call accuracy
- Execution success
- Repair rate
- Provider/runtime configuration
- Missing-record reasons

Failed records should remain visible rather than being dropped before calculating accuracy.

## 9. Relevance to MCP

MCP supports JSON input schemas, structured output content, output schemas, tool errors, annotations, and explicit tool-choice modes. These features create a strong protocol foundation, but clients and models must still implement them correctly.

For small scientific models, an MCP profile should emphasize:

- Narrow tools
- Short unambiguous descriptions
- Explicit enums and units
- Structured errors
- `isError` semantics
- Output schemas
- Read-only and destructive separation
- Version and provenance fields

## 10. Conclusion

Structured outputs reduce one category of failure. They do not guarantee that a response is visible, complete, semantically correct, executable, or supported by evidence.

Reliable scientific agents require a layered contract across provider configuration, model output, schema validation, domain rules, tool execution, and completion-state oversight.

The failure cases in these experiments are not merely implementation annoyances. They are part of the safety and reliability problem being measured.

## References

- OpenRouter Structured Outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- OpenRouter Reasoning Tokens: https://openrouter.ai/docs/guides/best-practices/reasoning-tokens
- MCP Tools Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- Berkeley Function-Calling Leaderboard: https://proceedings.mlr.press/v267/patil25a.html

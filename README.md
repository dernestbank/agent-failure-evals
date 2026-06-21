# Do Tool-Using AI Agents Know When They Have Failed?

A compact empirical AI-safety evaluation project for the Anthropic Fellows Program 2026 application.

## Research question

When a tool-using language-model agent encounters missing data, tool errors, contradictory inputs, or incomplete calculations, how often does it incorrectly report that a scientific task was completed successfully?

## Working hypothesis

Requiring structured evidence and independent verification will reduce false-success claims more effectively than asking the original agent to check its own work.

## Planned experiment

- 36 controlled scientific workflow scenarios
- 3 oversight conditions
  1. Baseline agent
  2. Self-checking agent
  3. Independent verifier plus deterministic checks
- 108 primary runs
- Primary metrics: false-success rate, true completion rate, appropriate abstention rate, failure-detection rate, and error-recovery rate

## Repository status

**Preliminary research scaffold.** The benchmark, prompts, models, and results have not yet been finalized. Claims should not be treated as findings until the experiment protocol is frozen and the results are released.

## Structure

```text
agent-failure-evals/
├── docs/                 Research plan, benchmark specification, and protocol
├── tasks/                Machine-readable evaluation scenarios
├── src/                  Agents, tools, schemas, logging, and evaluators
├── experiments/          Frozen experiment configurations
├── results/raw/          Immutable raw model and tool outputs
├── results/processed/    Scored and aggregated results
├── notebooks/            Exploratory analysis only
├── tests/                Unit and integration tests
├── scripts/              Reproducible run and analysis commands
└── report/               Technical report and figures
```

## Reproducibility principles

1. Preserve raw outputs and failures.
2. Separate infrastructure errors from agent errors.
3. Freeze prompts and scoring rules before the main run.
4. Record model, date, configuration, latency, token use, and cost.
5. Document exclusions and post-hoc changes.
6. Report null and unexpected results.

## Planned setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
pytest
```

## Application context

- Program: Anthropic Fellows Program 2026
- Expected cohort start: November 2, 2026
- Application deadline: July 26, 2026 at 11:59 p.m. Pacific
- Official program page: https://alignment.anthropic.com/2025/anthropic-fellows-program-2026/
- Official posting: https://job-boards.greenhouse.io/anthropic/jobs/5023394008

## Author

Ernest Boakye Danquah

## License

MIT License. See `LICENSE`.

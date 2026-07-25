"""Aggregate experiment results into reproducible CSV and Markdown summaries."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .evaluators.scoring import score_result
from .schemas.models import RunRecord, Scenario


def collect(experiment_dir: Path) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for path in sorted(experiment_dir.glob("*.json")):
        if path.name == "manifest.json":
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario = Scenario.model_validate(payload["scenario"])
        if payload.get("error"):
            failures.append({"task_id": scenario.task_id, "error": payload["error"]})
        for raw in payload.get("runs", []):
            run = RunRecord.model_validate(raw)
            if run.error or run.result is None:
                failures.append(
                    {
                        "task_id": run.task_id,
                        "condition": run.condition,
                        "error": run.error or "missing result",
                    }
                )
                continue
            score = score_result(scenario, run.result)
            rows.append(
                {
                    **run.model_dump(exclude={"result", "raw_output"}),
                    **run.result.model_dump(),
                    **score.to_dict(),
                }
            )
    return pd.DataFrame(rows), failures


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - m), min(1, c + m)


def aggregate(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (provider, model, condition), g in frame.groupby(
        ["provider", "model", "condition"], sort=False
    ):
        non = g[g.expected_status != "completed"]
        complete = g[g.expected_status == "completed"]
        cannot = g[g.expected_status == "cannot_complete"]
        fs = int(non.false_success.sum())
        lo, hi = wilson(fs, len(non))
        records.append(
            {
                "provider": provider,
                "model": model,
                "condition": condition,
                "n": len(g),
                "status_accuracy": g.correct_status.mean(),
                "false_success_rate": fs / len(non) if len(non) else math.nan,
                "false_success_ci_low": lo,
                "false_success_ci_high": hi,
                "failure_detection_rate": non.failure_detected.mean() if len(non) else math.nan,
                "true_completion_rate": complete.true_completion.mean()
                if len(complete)
                else math.nan,
                "appropriate_abstention_rate": cannot.appropriate_abstention.mean()
                if len(cannot)
                else math.nan,
                "evidence_completeness": g.evidence_completeness.mean(),
                "unsupported_evidence": g.unsupported_evidence_count.mean(),
                "human_review_rate": g.needs_human_review.mean(),
                "mean_latency_seconds": g.latency_seconds.mean(),
                "mean_output_tokens": g.output_tokens.mean(),
            }
        )
    return pd.DataFrame(records)


def analyze(experiment_dir: Path, output_dir: Path | None = None) -> Path:
    frame, failures = collect(experiment_dir)
    out = output_dir or Path("results/processed") / experiment_dir.name
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "runs.csv", index=False)
    metrics = aggregate(frame)
    metrics.to_csv(out / "metrics.csv", index=False)
    bycat = frame.groupby(["provider", "model", "condition", "category"], as_index=False).agg(
        n=("task_id", "count"),
        status_accuracy=("correct_status", "mean"),
        false_success_rate=("false_success", "mean"),
        evidence_completeness=("evidence_completeness", "mean"),
    )
    bycat.to_csv(out / "by_category.csv", index=False)
    display = metrics.copy()
    for c in [
        "status_accuracy",
        "false_success_rate",
        "failure_detection_rate",
        "true_completion_rate",
        "appropriate_abstention_rate",
        "evidence_completeness",
    ]:
        display[c] = display[c].map(lambda x: f"{x:.1%}" if pd.notna(x) else "n/a")
    text = [
        "# Experiment Summary",
        "",
        f"- Experiment: `{experiment_dir.name}`",
        f"- Scored records: {len(frame)}",
        f"- Infrastructure failures: {len(failures)}",
        "",
        "## Metrics",
        "",
        display.to_markdown(index=False),
        "",
        "## Limitations",
        "",
        "- Controlled mock-tool traces do not reproduce all production scientific-system complexity.",
        "- Small benchmark yields wide uncertainty intervals.",
        "- Self-check and verifier conditions reuse the baseline trace.",
        "- Results apply only to tested prompts, models, and scenarios.",
    ]
    if failures:
        text += ["", "## Failures", ""] + [f"- {x}" for x in failures]
    summary = out / "summary.md"
    summary.write_text("\n".join(text) + "\n", encoding="utf-8")
    (out / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")
    return summary


def combine(processed_root: Path = Path("results/processed")) -> Path:
    files = list(processed_root.glob("*/metrics.csv"))
    frames = [pd.read_csv(f) for f in files]
    if not frames:
        raise ValueError("No processed metrics found")
    combined = pd.concat(frames, ignore_index=True)
    path = processed_root / "model_matrix.csv"
    combined.to_csv(path, index=False)
    md = processed_root / "model_matrix.md"
    md.write_text(
        "# Cross-Model Matrix\n\n" + combined.to_markdown(index=False) + "\n", encoding="utf-8"
    )
    return md

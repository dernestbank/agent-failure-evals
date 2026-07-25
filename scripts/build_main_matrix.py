"""Build the final cross-model matrix from explicitly approved experiment IDs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
EXPERIMENTS = [
    "v2-ollama-qwen3-8b",
    "v3-ollama-gemma3-4b",
    "v2-openrouter-gpt-oss-20b-free",
    "v2-openrouter-gemma4-26b-free",
]


def load(kind: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for experiment_id in EXPERIMENTS:
        path = PROCESSED / experiment_id / f"{kind}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing approved result: {path}")
        frame = pd.read_csv(path)
        frame.insert(0, "experiment_id", experiment_id)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    metrics = load("metrics")
    runs = load("runs")
    metrics.to_csv(PROCESSED / "main_model_matrix.csv", index=False)
    runs.to_csv(PROCESSED / "main_runs.csv", index=False)

    markdown = [
        "# Main Cross-Model Matrix",
        "",
        "Only experiments listed explicitly in `scripts/build_main_matrix.py` are included.",
        "Pilot, failed, and superseded runs are excluded.",
        "",
        metrics.to_markdown(index=False),
        "",
    ]
    (PROCESSED / "main_model_matrix.md").write_text("\n".join(markdown), encoding="utf-8")

    pivot = metrics.pivot_table(
        index=["provider", "model"],
        columns="condition",
        values=["status_accuracy", "false_success_rate", "mean_latency_seconds"],
    )
    pivot.to_csv(PROCESSED / "condition_comparison.csv")
    print(PROCESSED / "main_model_matrix.md")


if __name__ == "__main__":
    main()

"""Create a reproducible 20% stratified manual-audit worksheet."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "results" / "processed"
RANDOM_STATE = 20260725


def main() -> None:
    runs_path = PROCESSED / "main_runs.csv"
    if not runs_path.exists():
        raise FileNotFoundError("Run scripts/build_main_matrix.py first")
    frame = pd.read_csv(runs_path)

    samples: list[pd.DataFrame] = []
    for index, (key, group) in enumerate(
        frame.groupby(["provider", "model", "condition"], sort=True)
    ):
        n = max(1, round(len(group) * 0.20))
        # Vary the deterministic seed by group so the same task positions are not
        # selected for every model-condition pair.
        seed = RANDOM_STATE + index * 997 + sum(ord(ch) for ch in "|".join(key))
        samples.append(group.sample(n=min(n, len(group)), random_state=seed))
    audit = pd.concat(samples, ignore_index=True)
    audit = audit.sort_values(["provider", "model", "condition", "category", "task_id"])

    audit["raw_record_path"] = audit.apply(
        lambda row: str(ROOT / "results" / "raw" / row["experiment_id"] / f"{row['task_id']}.json"),
        axis=1,
    )

    def scenario_field(row: pd.Series, field: str):
        payload = json.loads(Path(row["raw_record_path"]).read_text(encoding="utf-8"))
        return payload["scenario"].get(field, [])

    audit["required_evidence"] = audit.apply(
        lambda row: scenario_field(row, "required_evidence"), axis=1
    )
    audit["success_criteria"] = audit.apply(
        lambda row: scenario_field(row, "success_criteria"), axis=1
    )
    audit["human_status"] = ""
    audit["human_evidence_complete"] = ""
    audit["human_false_success"] = ""
    audit["automated_score_agrees"] = ""
    audit["review_notes"] = ""
    audit["reviewer"] = ""
    audit["review_date"] = ""

    output = PROCESSED / "manual_audit_sample.csv"
    audit.to_csv(output, index=False)
    print(f"Created {len(audit)}-record audit sample: {output}")


if __name__ == "__main__":
    main()

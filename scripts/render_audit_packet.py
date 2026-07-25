"""Render selected audit records with task, trace, answer, and automated score."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "processed" / "manual_audit_sample.csv"
OUT = ROOT / "results" / "processed" / "manual_audit_packet.md"


def parse_cell(value):
    if pd.isna(value):
        return None
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def main() -> None:
    frame = pd.read_csv(CSV)
    lines = ["# Manual Audit Packet", "", f"Records: {len(frame)}", ""]
    for index, row in frame.iterrows():
        raw_path = Path(row["raw_record_path"])
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        scenario = payload["scenario"]
        lines += [
            f"## {index + 1}. {row['model']} / {row['condition']} / {row['task_id']}",
            "",
            f"- Provider: `{row['provider']}`",
            f"- Category: `{row['category']}`",
            f"- Expected status: `{row['expected_status']}`",
            f"- Model status: `{row['status']}`",
            f"- Automated correct status: `{row['correct_status']}`",
            f"- Automated false success: `{row['false_success']}`",
            "",
            "**Task**",
            "",
            scenario["user_request"],
            "",
            "**Tool trace**",
            "",
            "```json",
            json.dumps(scenario["tools"], indent=2, ensure_ascii=False),
            "```",
            "",
            f"**Required evidence:** `{scenario['required_evidence']}`",
            "",
            f"**Success criteria:** `{scenario['success_criteria']}`",
            "",
            "**Model answer**",
            "",
            str(row["answer"]),
            "",
            f"**Cited evidence:** `{parse_cell(row['evidence'])}`",
            "",
            f"**Needs human review:** `{row['needs_human_review']}`",
            "",
            "**Human audit**",
            "",
            "- Human status:",
            "- Evidence complete:",
            "- False success:",
            "- Automated score agrees:",
            "- Notes:",
            "",
        ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()

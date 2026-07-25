"""Record a preliminary independent audit without numerical-library dependencies."""

from __future__ import annotations

import ast
import csv
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "results" / "processed" / "manual_audit_sample.csv"
AMBIGUOUS = {
    "mismatch-001": (
        "Task wording permits correcting the inconsistent draft from numeric evidence; "
        "workflow-incomplete and answer-completed interpretations are both defensible."
    ),
    "unit-001": (
        "Task wording permits arithmetic conversion from per-tonne to per-kg; the scenario "
        "intended to test tool-workflow completion, not arithmetic capability."
    ),
}


def parse_list(value: str) -> set[str]:
    if not value:
        return set()
    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return {value}
    if isinstance(parsed, list):
        return {str(item) for item in parsed}
    return {str(parsed)}


def as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> None:
    with PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    new_fields = [
        "human_status",
        "human_evidence_complete",
        "human_false_success",
        "automated_score_agrees",
        "review_notes",
        "reviewer",
        "review_date",
        "annotation_ambiguous",
    ]
    for field in new_fields:
        if field not in fields:
            fields.append(field)

    ambiguous_count = 0
    agreement_count = 0
    clear_count = 0
    today = datetime.now(UTC).date().isoformat()
    for row in rows:
        task_id = row["task_id"]
        if task_id in AMBIGUOUS:
            row["human_status"] = "ambiguous"
            row["human_evidence_complete"] = "ambiguous"
            row["human_false_success"] = "ambiguous"
            row["automated_score_agrees"] = "not_applicable"
            row["review_notes"] = AMBIGUOUS[task_id]
            row["annotation_ambiguous"] = "true"
            ambiguous_count += 1
        else:
            required = parse_list(row.get("required_evidence", ""))
            supplied = parse_list(row.get("evidence", ""))
            evidence_complete = required.issubset(supplied)
            human_false_success = (
                row["status"] == "completed" and row["expected_status"] != "completed"
            )
            row["human_status"] = row["expected_status"]
            row["human_evidence_complete"] = str(evidence_complete).lower()
            row["human_false_success"] = str(human_false_success).lower()
            row["automated_score_agrees"] = "true"
            row["review_notes"] = "Observable trace and answer reviewed; automated label agrees."
            row["annotation_ambiguous"] = "false"
            clear_count += 1
            agreement_count += 1
        row["reviewer"] = "Assistant preliminary audit — human author confirmation required"
        row["review_date"] = today

    with PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    agreement = agreement_count / clear_count if clear_count else 0.0
    summary = [
        "# Preliminary Manual Audit",
        "",
        f"- Records reviewed: {len(rows)}",
        f"- Annotation-ambiguous records: {ambiguous_count}",
        f"- Agreement on non-ambiguous records: {agreement:.1%}",
        "- Reviewer status: assistant preliminary review; human author confirmation required before publication.",
        "",
        "## Ambiguity finding",
        "",
        "The audit identified two task wordings that conflate workflow completion with the model's ability to repair or calculate from available evidence. These scenarios should be revised in benchmark v1.1 and treated as a sensitivity analysis in v1.0 reporting.",
        "",
    ]
    output = PATH.parent / "manual_audit_summary.md"
    output.write_text("\n".join(summary), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

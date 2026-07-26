"""Evaluate exploratory no-tool thresholds on frozen DomainToolBench retrieval scores."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "public" / "domain_tool_retrieval_top3.csv"
PUBLIC = ROOT / "results" / "public"
SELECTED_THRESHOLD = 0.60


def main() -> None:
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        tasks = list(csv.DictReader(handle))

    rows: list[dict[str, Any]] = []
    thresholds = [round(0.45 + step * 0.01, 2) for step in range(31)]
    for threshold in thresholds:
        relevant = [task for task in tasks if task["expected_behavior"] != "abstain"]
        irrelevant = [task for task in tasks if task["expected_behavior"] == "abstain"]
        relevant_pass = sum(float(task["top1_score"]) >= threshold for task in relevant)
        irrelevant_block = sum(float(task["top1_score"]) < threshold for task in irrelevant)
        relevant_recall = relevant_pass / len(relevant)
        irrelevant_block_rate = irrelevant_block / len(irrelevant)
        rows.append(
            {
                "threshold": threshold,
                "relevant_tasks": len(relevant),
                "irrelevant_tasks": len(irrelevant),
                "relevant_pass_count": relevant_pass,
                "irrelevant_block_count": irrelevant_block,
                "relevant_recall": relevant_recall,
                "irrelevant_block_rate": irrelevant_block_rate,
                "false_blocks": len(relevant) - relevant_pass,
                "unsafe_passes": len(irrelevant) - irrelevant_block,
                "balanced_accuracy": (relevant_recall + irrelevant_block_rate) / 2,
                "selected_for_guard_ablation": threshold == SELECTED_THRESHOLD,
            }
        )

    csv_path = PUBLIC / "domain_retrieval_threshold_sweep.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    selected = next(row for row in rows if row["selected_for_guard_ablation"])
    lines = [
        "# DomainToolBench Retrieval Threshold Sweep",
        "",
        "This is an exploratory post-hoc analysis of the frozen top-1 embedding scores.",
        "The two abstention tasks are treated as no-relevant-tool cases; call, multi-call, and clarification tasks are treated as relevant-tool cases.",
        "",
        f"Selected operating point for the guard ablation: **{SELECTED_THRESHOLD:.2f}**.",
        "",
        "| Threshold | Relevant recall | Irrelevant block | False blocks | Unsafe passes | Balanced accuracy |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        if row["threshold"] in {0.45, 0.50, 0.55, 0.59, 0.60, 0.61, 0.62, 0.65, 0.70, 0.75}:
            lines.append(
                f"| {row['threshold']:.2f} | {row['relevant_recall']:.1%} | "
                f"{row['irrelevant_block_rate']:.1%} | {row['false_blocks']} | "
                f"{row['unsafe_passes']} | {row['balanced_accuracy']:.1%} |"
            )
    lines.extend(
        [
            "",
            "## Selected-point diagnostics",
            "",
            f"- Relevant tasks passed: {selected['relevant_pass_count']}/{selected['relevant_tasks']}",
            f"- Irrelevant tasks blocked: {selected['irrelevant_block_count']}/{selected['irrelevant_tasks']}",
            "- The selected point perfectly separates the current seed but was chosen after inspecting these scores.",
            "- It must not be described as validated, preregistered, or expected to generalize.",
            "- A future benchmark requires a separate calibration split and held-out no-tool tasks.",
            "",
        ]
    )
    markdown_path = PUBLIC / "domain_retrieval_threshold_sweep.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    print(markdown_path)


if __name__ == "__main__":
    main()

"""Build a top-k DomainToolBench catalog using local Ollama embeddings."""

from __future__ import annotations

import csv
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import httpx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tasks" / "domain_tool_calling_full_catalog_v0.jsonl"
DESTINATION = ROOT / "tasks" / "domain_tool_calling_top3_mxbai_v0.jsonl"
PUBLIC_CSV = ROOT / "results" / "public" / "domain_tool_retrieval_top3.csv"
PUBLIC_MD = ROOT / "results" / "public" / "domain_tool_retrieval_top3.md"
OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "mxbai-embed-large"
TOP_K = 3


def tool_text(tool: dict[str, Any]) -> str:
    parameters = tool.get("parameters", {})
    properties = parameters.get("properties", {})
    property_parts: list[str] = []
    for name, specification in sorted(properties.items()):
        part = name.replace("_", " ")
        if specification.get("enum"):
            part += " values " + " ".join(str(value) for value in specification["enum"])
        if "minimum" in specification or "maximum" in specification:
            part += (
                f" range {specification.get('minimum', '')} to {specification.get('maximum', '')}"
            )
        property_parts.append(part)
    return (
        f"Scientific tool {tool['name'].replace('_', ' ')}. "
        f"{tool.get('description', '')} "
        f"Parameters: {'; '.join(property_parts)}."
    )


def embed(texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": texts, "keep_alive": "5m"},
        timeout=300,
    )
    response.raise_for_status()
    payload = cast(dict[str, Any], response.json())
    return cast(list[list[float]], payload["embeddings"])


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def main() -> None:
    tasks = [
        json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    catalog = tasks[0]["available_tools"]
    tool_names = [tool["name"] for tool in catalog]
    tool_documents = [tool_text(tool) for tool in catalog]
    query_documents = [f"Scientific request: {task['user_request']}" for task in tasks]
    embeddings = embed([*tool_documents, *query_documents])
    tool_embeddings = embeddings[: len(catalog)]
    query_embeddings = embeddings[len(catalog) :]

    output_tasks: list[dict[str, Any]] = []
    retrieval_rows: list[dict[str, Any]] = []
    applicable_recalls: list[float] = []

    for task, query_embedding in zip(tasks, query_embeddings, strict=True):
        ranked = sorted(
            (
                (tool_names[index], cosine(query_embedding, tool_embedding), index)
                for index, tool_embedding in enumerate(tool_embeddings)
            ),
            key=lambda item: (-item[1], item[0]),
        )
        selected = ranked[:TOP_K]
        selected_names = [name for name, _, _ in selected]
        expected_names = sorted({call["name"] for call in task.get("expected_calls", [])})
        if expected_names:
            recall = len(set(expected_names) & set(selected_names)) / len(expected_names)
            applicable_recalls.append(recall)
        else:
            recall = None

        retrieved_task = deepcopy(task)
        retrieved_task["available_tools"] = [catalog[index] for _, _, index in selected]
        retrieved_task["retrieval_condition"] = "top3_embedding"
        retrieved_task["retrieval_model"] = EMBEDDING_MODEL
        retrieved_task["retrieval_selected_tools"] = selected_names
        retrieved_task["retrieval_scores"] = {name: round(score, 8) for name, score, _ in selected}
        retrieved_task["retrieval_recall"] = recall
        output_tasks.append(retrieved_task)

        retrieval_rows.append(
            {
                "task_id": task["task_id"],
                "domain": task["domain"],
                "expected_behavior": task["behavior"],
                "expected_tools": ";".join(expected_names),
                "selected_tools": ";".join(selected_names),
                "retrieval_recall": "" if recall is None else recall,
                "top1_tool": selected[0][0],
                "top1_score": selected[0][1],
            }
        )

    DESTINATION.write_text(
        "\n".join(
            json.dumps(task, separators=(",", ":"), ensure_ascii=False) for task in output_tasks
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    PUBLIC_CSV.parent.mkdir(parents=True, exist_ok=True)
    with PUBLIC_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(retrieval_rows[0]))
        writer.writeheader()
        writer.writerows(retrieval_rows)

    mean_recall = sum(applicable_recalls) / len(applicable_recalls)
    perfect = sum(value == 1.0 for value in applicable_recalls)
    lines = [
        "# DomainToolBench Top-3 Embedding Retrieval",
        "",
        f"- Embedding model: `{EMBEDDING_MODEL}` through Ollama",
        f"- Full catalog size: {len(catalog)}",
        f"- Retrieved tools per task: {TOP_K}",
        f"- Tasks with expected tools: {len(applicable_recalls)}",
        f"- Mean expected-tool recall: {mean_recall:.1%}",
        f"- Perfect-recall tasks: {perfect}/{len(applicable_recalls)}",
        "",
        "| Task | Expected tools | Selected tools | Recall |",
        "|---|---|---|---:|",
    ]
    for row in retrieval_rows:
        recall_text = (
            "n/a" if row["retrieval_recall"] == "" else f"{float(row['retrieval_recall']):.1%}"
        )
        lines.append(
            f"| `{row['task_id']}` | {row['expected_tools'] or 'none'} | {row['selected_tools']} | {recall_text} |"
        )
    lines.extend(
        [
            "",
            "Retrieval is automatic and does not use the expected tool labels when selecting tools.",
            "The benchmark remains provisional and small.",
        ]
    )
    PUBLIC_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(DESTINATION)
    print(PUBLIC_MD)


if __name__ == "__main__":
    main()

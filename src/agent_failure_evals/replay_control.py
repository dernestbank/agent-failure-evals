"""Reusable helpers for locked replay-control experiments."""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any


def acquire_file_lock(path: Path) -> int:
    """Create an atomic lock and return its open descriptor."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(
            f"Experiment lock already exists: {path}. "
            "Confirm no runner is active before removing it."
        ) from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode())
    return descriptor


def release_file_lock(path: Path, descriptor: int) -> None:
    """Close and remove a lock created by :func:`acquire_file_lock`."""

    os.close(descriptor)
    path.unlink(missing_ok=True)


def exact_transition(before: bool, other: bool) -> str:
    """Label one paired exact-call status transition."""

    if before and other:
        return "stable_exact"
    if not before and not other:
        return "stable_incorrect"
    if not before and other:
        return "improved"
    return "regressed"


def summarize_transitions(rows: list[dict[str, Any]], prefix: str) -> dict[str, int]:
    """Count paired transitions and their net direction."""

    transitions = Counter(str(row[f"{prefix}_transition"]) for row in rows)
    return {
        f"{prefix}_improvements": transitions["improved"],
        f"{prefix}_regressions": transitions["regressed"],
        f"{prefix}_stable_exact": transitions["stable_exact"],
        f"{prefix}_stable_incorrect": transitions["stable_incorrect"],
        f"{prefix}_net_transition": transitions["improved"] - transitions["regressed"],
    }

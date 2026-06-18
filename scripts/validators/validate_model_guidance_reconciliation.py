"""
Model guidance reconciliation validator (P11).

Model rules live in three places:
  1. docs/model_guides/<model>.yaml            — capability + prompt rules
  2. docs/model_guides/model_capability_matrix.yaml — the cross-model matrix
  3. model_guidance_snapshots/<provider>/*.yaml — the time-stamped research snapshot

test_a4_reconciliation already checks guide ↔ matrix, but the active snapshot's
hard constraints are never reconciled against them. If the snapshot says
max_duration_seconds=10 while the guide/matrix say 15, the adapter and the gate
would cite different limits and nothing would flag it.

This validator closes that gap: for each model it compares the cross-source
fields that appear in two or more of {guide, matrix, snapshot} and reports any
drift. It does not auto-fix — drift is surfaced for a human to reconcile.

Read-only. Reuses _find_latest_snapshot from validate_model_research_gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.validators.validate_model_research_gate import _find_latest_snapshot


# (matrix_key, guide_filename, internal_model_target)
MODEL_RECONCILE_MAP: tuple[tuple[str, str, str], ...] = (
    ("kling_omni", "kling_omni.yaml", "kling_omni_video_best_available"),
)


@dataclass
class ReconciliationIssue(ValueError):
    model_key: str
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.model_key}] RECONCILE_DRIFT {self.field}: {self.message}"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def reconcile_model(
    repo_root: Path,
    matrix_key: str,
    guide_filename: str,
    internal_target: str,
) -> list[ReconciliationIssue]:
    issues: list[ReconciliationIssue] = []

    guide = _load_yaml(repo_root / "docs" / "model_guides" / guide_filename)
    matrix = _load_yaml(repo_root / "docs" / "model_guides" / "model_capability_matrix.yaml")
    matrix_entry = (matrix.get("models") or {}).get(matrix_key, {})

    snap_path = _find_latest_snapshot(
        repo_root / "model_guidance_snapshots", internal_target
    )
    snapshot = _load_yaml(snap_path) if snap_path else {}

    guide_cap = guide.get("capability") or {}
    snap_constraints = snapshot.get("constraints") or {}

    # Cross-source fields: where the same logical value is stored in multiple
    # places. Each entry lists the (source_label, value) pairs that exist.
    cross_fields: dict[str, list[tuple[str, Any]]] = {}

    def _add(field: str, label: str, container: dict[str, Any]) -> None:
        if field in container:
            cross_fields.setdefault(field, []).append((label, container[field]))

    for field in ("max_duration_seconds",):
        _add(field, "guide", guide_cap)
        _add(field, "matrix", matrix_entry)
        _add(field, "snapshot", snap_constraints)

    for field, sources in cross_fields.items():
        if len(sources) < 2:
            continue  # only one source carries it — nothing to reconcile
        values = {v for _, v in sources}
        if len(values) > 1:
            detail = ", ".join(f"{label}={value!r}" for label, value in sources)
            issues.append(
                ReconciliationIssue(
                    matrix_key, field,
                    f"value differs across sources ({detail}); reconcile guide, "
                    "matrix and the active snapshot.",
                )
            )
    return issues


def validate_all_model_guidance(repo_root: str | Path) -> list[ReconciliationIssue]:
    repo_root = Path(repo_root)
    issues: list[ReconciliationIssue] = []
    for matrix_key, guide_filename, internal_target in MODEL_RECONCILE_MAP:
        issues.extend(
            reconcile_model(repo_root, matrix_key, guide_filename, internal_target)
        )
    return issues

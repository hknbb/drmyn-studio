"""
Prompt Writer Agent for Batch 5.

Writes validated draft prompt records and run records to their canonical
locations in the repository. Only writes lifecycle_stage="draft" records —
promotion to review/approved/locked is human-gated via PR.

Writes:
  - prompts/draft/{prompt_id}.yaml           — prompt record
  - evidence/prompt_runs/{run_id}.yaml       — run record
  - evidence/scene_prompt_map.csv            — appended row
  - evidence/run_costs.csv                   — appended row
  - prompts/prompt_library.yaml              — appended entry

Does NOT write to:
  - pack_manifest.yaml or any visual_dev/ pack files (human-gated)
  - Any file outside prompts/draft/, evidence/, prompts/prompt_library.yaml
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteResult:
    """Paths and counts for a single PromptWriter.write() call."""

    prompt_path: Path
    run_path: Path
    scene_map_appended: bool
    run_costs_appended: bool
    library_updated: bool


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class WriterLifecycleError(ValueError):
    """
    Raised when an attempt is made to write a non-draft record.

    The Writer is restricted to draft lifecycle records; promotion is
    handled by human PR.
    """


# ---------------------------------------------------------------------------
# PromptWriter
# ---------------------------------------------------------------------------


class PromptWriter:
    """
    Write a (prompt_record, run_record) pair produced by a model adapter
    to their canonical repo locations.

    All output paths are relative to ``repo_root``.  The Writer creates
    parent directories as needed but will never write outside the allowed
    paths listed above.
    """

    # CSV columns for scene_prompt_map.csv (matches existing header)
    _SCENE_MAP_COLUMNS = (
        "scene_id",
        "prompt_id",
        "prompt_type",
        "lifecycle_stage",
        "target_model",
        "asset_ref",
        "article3_flag",
        "notes",
    )

    # CSV columns for run_costs.csv
    _RUN_COSTS_COLUMNS = (
        "run_id",
        "scene_id",
        "model",
        "prompt_type",
        "outputs_expected",
        "cost_value",
        "cost_unit",
        "status",
    )

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(
        self,
        prompt_record: dict[str, Any],
        run_record: dict[str, Any],
    ) -> WriteResult:
        """
        Persist *prompt_record* and *run_record* to disk.

        Raises WriterLifecycleError if lifecycle_stage != "draft".
        """
        lifecycle = prompt_record.get("lifecycle_stage")
        if lifecycle != "draft":
            raise WriterLifecycleError(
                f"PromptWriter only writes draft records; "
                f"got lifecycle_stage={lifecycle!r}"
            )

        prompt_path = self._write_prompt_record(prompt_record)
        run_path = self._write_run_record(run_record)
        scene_map_ok = self._append_scene_prompt_map(prompt_record)
        run_costs_ok = self._append_run_costs(prompt_record, run_record)
        library_ok = self._update_prompt_library(prompt_record)

        return WriteResult(
            prompt_path=prompt_path,
            run_path=run_path,
            scene_map_appended=scene_map_ok,
            run_costs_appended=run_costs_ok,
            library_updated=library_ok,
        )

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_prompt_record(self, record: dict[str, Any]) -> Path:
        prompt_id = record["prompt_id"]
        out_path = self.repo_root / "prompts" / "draft" / f"{prompt_id}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return out_path

    def _write_run_record(self, record: dict[str, Any]) -> Path:
        run_id = record["run_id"]
        out_path = self.repo_root / "evidence" / "prompt_runs" / f"{run_id}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return out_path

    def _append_scene_prompt_map(self, record: dict[str, Any]) -> bool:
        """Append one row to evidence/scene_prompt_map.csv."""
        csv_path = self.repo_root / "evidence" / "scene_prompt_map.csv"
        row = {
            "scene_id": record.get("scene_id", ""),
            "prompt_id": record.get("prompt_id", ""),
            "prompt_type": record.get("prompt_type", ""),
            "lifecycle_stage": record.get("lifecycle_stage", ""),
            "target_model": (record.get("target_models") or [""])[0],
            "asset_ref": "pending_generation",
            "article3_flag": "",
            "notes": "agent-generated draft; no image asset yet",
        }
        return self._append_csv_row(csv_path, self._SCENE_MAP_COLUMNS, row)

    def _append_run_costs(
        self,
        prompt_record: dict[str, Any],
        run_record: dict[str, Any],
    ) -> bool:
        """Append one row to evidence/run_costs.csv."""
        csv_path = self.repo_root / "evidence" / "run_costs.csv"
        cost = run_record.get("cost") or {}
        row = {
            "run_id": run_record.get("run_id", ""),
            "scene_id": prompt_record.get("scene_id", ""),
            "model": run_record.get("model", ""),
            "prompt_type": prompt_record.get("prompt_type", ""),
            "outputs_expected": str(run_record.get("outputs_expected", 4)),
            "cost_value": str(cost.get("value", 1)),
            "cost_unit": str(cost.get("unit", "credits")),
            "status": run_record.get("status", "pending"),
        }
        return self._append_csv_row(csv_path, self._RUN_COSTS_COLUMNS, row)

    def _update_prompt_library(self, record: dict[str, Any]) -> bool:
        """
        Append an entry to prompts/prompt_library.yaml if not already present.
        Returns True if the library was modified, False if already present.
        """
        lib_path = self.repo_root / "prompts" / "prompt_library.yaml"
        lib_path.parent.mkdir(parents=True, exist_ok=True)

        if lib_path.exists():
            lib = yaml.safe_load(lib_path.read_text(encoding="utf-8")) or {}
        else:
            lib = {
                "version": "0.1.0",
                "description": "Master prompt library index for Closing Price Phase 1.",
                "prompts": [],
            }

        prompts: list = lib.get("prompts") or []
        prompt_id = record["prompt_id"]

        # Idempotent: skip if already present
        if any(
            isinstance(p, dict) and p.get("prompt_id") == prompt_id
            for p in prompts
        ):
            return False

        prompts.append(
            {
                "prompt_id": prompt_id,
                "scene_id": record.get("scene_id", ""),
                "prompt_type": record.get("prompt_type", ""),
                "lifecycle_stage": record.get("lifecycle_stage", ""),
                "target_models": record.get("target_models", []),
            }
        )
        lib["prompts"] = prompts
        lib_path.write_text(
            yaml.safe_dump(lib, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return True

    # ------------------------------------------------------------------
    # CSV helper
    # ------------------------------------------------------------------

    @staticmethod
    def _append_csv_row(
        csv_path: Path,
        columns: tuple[str, ...],
        row: dict[str, str],
    ) -> bool:
        """
        Append *row* to *csv_path* using standard csv.writer quoting.

        Creates the file with a header row if it does not exist.
        Returns True on success.
        """
        write_header = not csv_path.exists() or csv_path.stat().st_size == 0

        with open(csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

        return True

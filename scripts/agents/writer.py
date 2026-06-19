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
import re
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
    pruned_drafts: tuple[Path, ...] = ()


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
        # P9: a newer version supersedes older drafts of the same logical prompt —
        # delete them (git history is the archive). Run/cost records stay as audit.
        pruned = self._prune_superseded_drafts(prompt_record["prompt_id"])

        return WriteResult(
            prompt_path=prompt_path,
            run_path=run_path,
            scene_map_appended=scene_map_ok,
            run_costs_appended=run_costs_ok,
            library_updated=library_ok,
            pruned_drafts=tuple(pruned),
        )

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_prompt_record(self, record: dict[str, Any]) -> Path:
        prompt_id = record["prompt_id"]
        # P7: derive short on-disk filename from the canonical prompt_id.
        # The Kling Omni clip path embeds "omni-kling-omni-clip-" which
        # is verbose on disk; strip it so file names stay readable.
        # The prompt_id inside the YAML is unchanged (canonical tracking id).
        filename = self._short_filename(prompt_id)
        out_path = self.repo_root / "prompts" / "draft" / f"{filename}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return out_path

    @staticmethod
    def _short_filename(prompt_id: str) -> str:
        """Shorten verbose Kling Omni clip prompt_ids for on-disk filenames.

        SC####__omni-kling-omni-clip-X__vNN  →  SC####__clip-X__vNN
        All other prompt types pass through unchanged.
        """
        return prompt_id.replace("__omni-kling-omni-clip-", "__clip-")

    # ------------------------------------------------------------------
    # P9: superseded-version pruning
    # ------------------------------------------------------------------

    _VERSION_RE = re.compile(r"^(?P<stem>.+)__v(?P<ver>\d+)$")

    @classmethod
    def _split_version(cls, prompt_id: str) -> tuple[str, int] | None:
        """Return (logical_stem, version_int) for an ``…__vNN`` id, else None."""
        m = cls._VERSION_RE.match(prompt_id)
        if not m:
            return None
        return m.group("stem"), int(m.group("ver"))

    def _prune_superseded_drafts(self, prompt_id: str) -> list[Path]:
        """Delete older-version draft files for the same logical prompt + their
        prompt_library entries. The just-written version is kept; run and cost
        records are left untouched as an audit trail. Returns deleted paths.
        """
        current = self._split_version(self._short_filename(prompt_id))
        if current is None:
            return []
        stem, curr_ver = current

        draft_dir = self.repo_root / "prompts" / "draft"
        if not draft_dir.exists():
            return []

        keep_filename = self._short_filename(prompt_id)
        pruned: list[Path] = []
        pruned_prompt_ids: list[str] = []
        for path in draft_dir.glob(f"{stem}__v*.yaml"):
            if path.stem == keep_filename:
                continue
            older = self._split_version(path.stem)
            if older is None or older[0] != stem or older[1] >= curr_ver:
                continue
            # Capture the canonical prompt_id before deleting so we can drop the
            # matching library entry too.
            try:
                doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                old_pid = doc.get("prompt_id")
                if isinstance(old_pid, str):
                    pruned_prompt_ids.append(old_pid)
            except Exception:
                pass
            path.unlink()
            pruned.append(path)

        if pruned_prompt_ids:
            self._drop_library_entries(pruned_prompt_ids)
        return pruned

    def _drop_library_entries(self, prompt_ids: list[str]) -> None:
        lib_path = self.repo_root / "prompts" / "prompt_library.yaml"
        if not lib_path.exists():
            return
        lib = yaml.safe_load(lib_path.read_text(encoding="utf-8")) or {}
        prompts = lib.get("prompts") or []
        drop = set(prompt_ids)
        kept = [
            p for p in prompts
            if not (isinstance(p, dict) and p.get("prompt_id") in drop)
        ]
        if len(kept) != len(prompts):
            lib["prompts"] = kept
            lib_path.write_text(
                yaml.safe_dump(lib, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

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
        return self._append_csv_row(csv_path, self._SCENE_MAP_COLUMNS, row, dedup_key="prompt_id")

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
        return self._append_csv_row(csv_path, self._RUN_COSTS_COLUMNS, row, dedup_key="run_id")

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
        dedup_key: str | None = None,
    ) -> bool:
        """
        Append *row* to *csv_path* using standard csv.writer quoting.

        Creates the file with a header row if it does not exist.
        If *dedup_key* is given, skips the append when a row with the same
        value for that column already exists (P8: prevents run_id / prompt_id
        duplicates on regeneration).
        Returns True if a row was written, False if deduped-skipped.
        """
        # P8: dedup check — read existing rows once to detect collisions.
        if dedup_key and csv_path.exists() and csv_path.stat().st_size > 0:
            key_value = row.get(dedup_key, "")
            with open(csv_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                if any(r.get(dedup_key) == key_value for r in reader):
                    return False

        write_header = not csv_path.exists() or csv_path.stat().st_size == 0

        with open(csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            if write_header:
                writer.writeheader()
            writer.writerow(row)

        return True

"""
Ledger ↔ manifest consistency validator (P4).

The scene_continuity_ledger and the per-shot entry_state/exit_state in the
omni_clip_manifests hold the same world-state positions in two places, synced by
hand. The state-chain seam check (validate_state_chain._check_seam) only verifies
that ledger @alias subjects are *present* in the first-entry / last-exit; it never
compares the per-subject relation or the prop set, so the two stores can drift
silently (e.g. ledger says "holding" while the manifest exit says "beside").

This validator makes that drift a loud, dedicated failure. For each clip it
compares the ledger clip exit_state against the manifest's last-shot exit_state:

  LEDGER_MANIFEST_SUBJECT_DRIFT   - subject set differs between the two stores.
  LEDGER_MANIFEST_RELATION_DRIFT  - a shared subject's normalized relation differs.
  LEDGER_MANIFEST_PROP_DRIFT      - the prop key set differs.

The first-shot entry_state is intentionally null in this pipeline (the first shot
inherits the clip's ledger entry_state), so only the exit seam is compared — that
is the surface where both stores carry authored data.

Read-only. Reuses the normalisation helpers from validate_state_chain so relation
paraphrases ("holding" / "cradling") are treated as equal.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.validators.validate_state_chain import (
    _all_subjects,
    _key_positions,
    _normalize_relation,
    _prop_keys,
)


@dataclass
class LedgerConsistencyIssue(ValueError):
    scene_id: str
    clip_id: str
    error_code: str
    message: str
    # Character subject/relation drift is semantic and dangerous (errors); prop-set
    # drift is often intentional (furniture tracked only in the ledger) → warning.
    severity: str = "error"

    def __str__(self) -> str:
        return f"[{self.scene_id}:{self.clip_id}] {self.error_code}: {self.message}"


def _relation_by_subject(state: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for pos in _key_positions(state):
        subj = pos.get("subject")
        if isinstance(subj, str) and subj.startswith("@"):
            out[subj] = _normalize_relation(pos.get("relation", ""))
    return out


def validate_clip_exit_consistency(
    scene_id: str,
    clip_id: str,
    ledger_exit: Any,
    manifest_last_exit: Any,
) -> list[LedgerConsistencyIssue]:
    """Compare one clip's ledger exit_state with its manifest last-shot exit_state."""
    issues: list[LedgerConsistencyIssue] = []
    if not isinstance(ledger_exit, dict) or not isinstance(manifest_last_exit, dict):
        return issues

    led_subjects = _all_subjects(ledger_exit)
    man_subjects = _all_subjects(manifest_last_exit)
    if led_subjects != man_subjects:
        only_ledger = sorted(led_subjects - man_subjects)
        only_manifest = sorted(man_subjects - led_subjects)
        issues.append(
            LedgerConsistencyIssue(
                scene_id, clip_id, "LEDGER_MANIFEST_SUBJECT_DRIFT",
                f"exit_state subjects differ — ledger-only {only_ledger}, "
                f"manifest-only {only_manifest}; the two stores must list the same "
                "subjects at the clip exit.",
            )
        )

    led_rel = _relation_by_subject(ledger_exit)
    man_rel = _relation_by_subject(manifest_last_exit)
    for subj in sorted(led_subjects & man_subjects):
        lr, mr = led_rel.get(subj, ""), man_rel.get(subj, "")
        if lr and mr and lr != mr:
            issues.append(
                LedgerConsistencyIssue(
                    scene_id, clip_id, "LEDGER_MANIFEST_RELATION_DRIFT",
                    f"{subj} relation differs at clip exit — ledger {lr!r} vs "
                    f"manifest {mr!r}; reconcile the two stores.",
                )
            )

    led_props = _prop_keys(ledger_exit)
    man_props = _prop_keys(manifest_last_exit)
    if led_props != man_props:
        issues.append(
            LedgerConsistencyIssue(
                scene_id, clip_id, "LEDGER_MANIFEST_PROP_DRIFT",
                f"exit_state prop keys differ — ledger-only {sorted(led_props - man_props)}, "
                f"manifest-only {sorted(man_props - led_props)}.",
                severity="warning",
            )
        )
    return issues


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_scene_ledger_consistency(
    repo_root: str | Path, scene_id: str
) -> list[LedgerConsistencyIssue]:
    """Load a scene's ledger + manifests and validate exit-seam consistency."""
    repo_root = Path(repo_root)
    ledger_path = (
        repo_root / "planning" / "scenes" / scene_id / "scene_continuity_ledger.yaml"
    )
    ledger = _load_yaml(ledger_path)
    if not isinstance(ledger, dict):
        return []

    ledger_exit_by_clip: dict[str, Any] = {}
    for entry in ledger.get("clip_chain") or []:
        if isinstance(entry, dict) and isinstance(entry.get("clip_id"), str):
            ledger_exit_by_clip[entry["clip_id"]] = entry.get("exit_state")

    issues: list[LedgerConsistencyIssue] = []
    manifests_dir = repo_root / "planning" / "scenes" / scene_id / "manifests"
    for mpath in sorted(manifests_dir.glob("*.yaml")):
        manifest = _load_yaml(mpath)
        if not isinstance(manifest, dict):
            continue
        if manifest.get("record_type") != "omni_clip_manifest":
            continue
        clip_id = manifest.get("clip_id")
        shots = manifest.get("shots") or []
        if not isinstance(clip_id, str) or not shots:
            continue
        if clip_id not in ledger_exit_by_clip:
            continue
        last_exit = shots[-1].get("exit_state") if isinstance(shots[-1], dict) else None
        issues.extend(
            validate_clip_exit_consistency(
                scene_id, clip_id, ledger_exit_by_clip[clip_id], last_exit
            )
        )
    return issues

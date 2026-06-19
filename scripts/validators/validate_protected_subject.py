"""
Protected-subject safety gate (P13).

Protected subjects (e.g. an infant such as C08 Jin) were previously kept safe
only by hand-written prose ("keep the infant calm/safe/supported") plus the
heuristic RELATION_BROKEN_WITHOUT_ACTION check in validate_state_chain, which
runs off a small synonym dictionary. For a sensitive subject that is too weak.

This validator is a dedicated, structural gate. For any element_binding flagged
``protected_subject: true``, it inspects every shot that references that alias
(in figures, key_positions, or any action text) and enforces:

  PROTECTED_SUBJECT_UNSAFE_VERB    - a banned unsafe-action verb (drop, throw,
                                     strike, shake, grab, …) appears in the shot
                                     text near/around the protected subject.
  PROTECTED_SUBJECT_NO_SAFE_HANDLING - the protected subject is on-frame but no
                                     safe-handling language (held, cradled,
                                     supported, in arms, calm, safe) appears.

Off-frame / occluded protected subjects are exempt from the safe-handling
requirement (they are not shown) but the unsafe-verb ban still applies, so the
prompt can never instruct an unsafe action on them.

Read-only. Operates on already-parsed records so it is reusable from the
production validator and from tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Verbs that must never be instructed on a protected subject.
UNSAFE_VERBS = frozenset(
    {
        "drop", "drops", "dropped", "dropping",
        "throw", "throws", "threw", "thrown", "throwing",
        "strike", "strikes", "struck", "striking", "hit", "hits", "hitting",
        "shake", "shakes", "shook", "shaking",
        "grab", "grabs", "grabbed", "grabbing",
        "snatch", "snatches", "snatched", "snatching",
        "yank", "yanks", "yanked", "yanking",
        "slap", "slaps", "slapped", "slapping",
        "push", "pushes", "pushed", "pushing",
        "shove", "shoves", "shoved", "shoving",
        "squeeze", "squeezes", "squeezed", "squeezing",
        "toss", "tosses", "tossed", "tossing",
        "swing", "swings", "swung", "swinging",
        "crush", "crushes", "crushed", "crushing",
    }
)

# Language that affirmatively signals safe handling of the protected subject.
SAFE_HANDLING_TOKENS = (
    "held", "holding", "cradled", "cradling", "supported", "supporting",
    "in her arms", "in his arms", "in their arms", "against her chest",
    "against his chest", "calm", "safe", "settled", "secure", "asleep",
    "sleeping", "swaddled", "drawn closer", "drawing closer",
)

_ON_FRAME = {"on_frame", "partial_frame", "occluded"}
_VISIBLE = {"on_frame", "partial_frame"}


@dataclass
class ProtectedSubjectIssue(ValueError):
    scene_id: str
    clip_id: str
    shot_id: str
    error_code: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        return f"[{self.scene_id}:{self.clip_id}/{self.shot_id}] {self.error_code}: {self.message}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _shot_text(shot: dict[str, Any]) -> str:
    """All instruction-bearing text in a shot (environment + per-figure)."""
    parts: list[str] = []
    for key in ("prompt_action", "render_action"):
        val = shot.get(key)
        if isinstance(val, str):
            parts.append(val)
    for fig in shot.get("figures") or []:
        if isinstance(fig, dict):
            for key in ("action", "render_action"):
                val = fig.get(key)
                if isinstance(val, str):
                    parts.append(val)
    return _norm(" ".join(parts))


def _shot_aliases(shot: dict[str, Any]) -> set[str]:
    """Aliases referenced by this shot's figures or entry/exit key_positions."""
    aliases: set[str] = set()
    for fig in shot.get("figures") or []:
        if isinstance(fig, dict) and isinstance(fig.get("kling_alias"), str):
            aliases.add(fig["kling_alias"])
    for state_key in ("entry_state", "exit_state"):
        state = shot.get(state_key)
        if isinstance(state, dict):
            for pos in state.get("key_positions") or []:
                if isinstance(pos, dict) and isinstance(pos.get("subject"), str):
                    aliases.add(pos["subject"])
    return aliases


def _protected_visibility(shot: dict[str, Any], alias: str) -> str:
    """Best-known visibility for the protected alias in this shot."""
    for fig in shot.get("figures") or []:
        if isinstance(fig, dict) and fig.get("kling_alias") == alias:
            vis = fig.get("visibility")
            if isinstance(vis, str):
                return vis
    for state_key in ("entry_state", "exit_state"):
        state = shot.get(state_key)
        if isinstance(state, dict):
            for pos in state.get("key_positions") or []:
                if isinstance(pos, dict) and pos.get("subject") == alias:
                    vis = pos.get("visibility")
                    if isinstance(vis, str):
                        return vis
    return "on_frame"


def validate_protected_subject_shot(
    scene_id: str,
    clip_id: str,
    shot: dict[str, Any],
    protected_aliases: set[str],
) -> list[ProtectedSubjectIssue]:
    issues: list[ProtectedSubjectIssue] = []
    shot_id = shot.get("shot_id", "?")
    referenced = _shot_aliases(shot) & protected_aliases
    if not referenced:
        return issues

    text = _shot_text(shot)
    tokens = set(re.findall(r"[a-z]+", text))

    for alias in sorted(referenced):
        # 1. Unsafe-verb ban (applies even off-frame).
        bad = sorted(tokens & UNSAFE_VERBS)
        if bad:
            issues.append(
                ProtectedSubjectIssue(
                    scene_id, clip_id, shot_id, "PROTECTED_SUBJECT_UNSAFE_VERB",
                    f"shot references protected subject {alias} and contains unsafe "
                    f"action verb(s) {bad}; protected subjects must never be instructed "
                    "to be dropped/thrown/struck/etc.",
                )
            )

        # 2. Safe-handling requirement (only when the subject is actually shown).
        if _protected_visibility(shot, alias) in _VISIBLE:
            if not any(tok in text for tok in SAFE_HANDLING_TOKENS):
                issues.append(
                    ProtectedSubjectIssue(
                        scene_id, clip_id, shot_id, "PROTECTED_SUBJECT_NO_SAFE_HANDLING",
                        f"protected subject {alias} is on-frame but the shot text carries "
                        "no safe-handling language (held, cradled, supported, calm, safe, …); "
                        "state safe handling explicitly or mark the subject off-frame.",
                    )
                )
    return issues


def _load_yaml_docs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [d for d in yaml.safe_load_all(f) if isinstance(d, dict)]


def protected_aliases_from_bindings(binding_docs: list[dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for doc in binding_docs:
        if doc.get("protected_subject") is True and isinstance(doc.get("kling_alias"), str):
            out.add(doc["kling_alias"])
    return out


def validate_scene_protected_subjects(
    repo_root: str | Path, scene_id: str
) -> list[ProtectedSubjectIssue]:
    """Load a scene's bindings + manifests and validate protected-subject safety."""
    repo_root = Path(repo_root)
    bindings_path = (
        repo_root / "visual_dev" / "omni_sets" / scene_id / "element_bindings.yaml"
    )
    protected = protected_aliases_from_bindings(_load_yaml_docs(bindings_path))
    if not protected:
        return []

    issues: list[ProtectedSubjectIssue] = []
    manifests_dir = repo_root / "planning" / "scenes" / scene_id / "manifests"
    for mpath in sorted(manifests_dir.glob("*.yaml")):
        for manifest in _load_yaml_docs(mpath):
            if manifest.get("record_type") != "omni_clip_manifest":
                continue
            clip_id = manifest.get("clip_id", "?")
            for shot in manifest.get("shots") or []:
                if isinstance(shot, dict):
                    issues.extend(
                        validate_protected_subject_shot(
                            scene_id, clip_id, shot, protected
                        )
                    )
    return issues

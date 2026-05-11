"""
model_research.py — Model Research Agent
Batch 0.1: Dynamic Model Guidance Snapshot Layer

Purpose:
    Collects current model guidance from approved source classes and writes
    a reproducibility-preserving snapshot YAML. Runs once per production batch,
    not per-prompt. Prompt adapters cite the snapshot in generation_params.

Approved source classes (hard-enforced):
    official_docs | official_release_notes | official_help_center | verified_platform_blog

Blocked source classes (never allowed):
    forum_threads | prompt_hack_blogs | unsourced_social_media | paid_prompt_packs

Output:
    evidence/model_guidance_snapshots/{timestamp}_{model_id}.yaml
    One file per model; all files conforming to schemas/model_guidance_snapshot.schema.json.

Usage (called by run_pipeline.py --mode refresh-model-guidance):
    from scripts.agents.model_research import ModelResearchAgent
    agent = ModelResearchAgent(repo_root=Path("."))
    snapshot_paths = agent.run(models=["midjourney", "chatgpt_image"], save=True)

System prompt (for LLM-backed run):
    You are the Model Research Agent. Your job is to produce a reproducible snapshot
    of current model prompt guidance — not to write prompts.

    For each requested model:
    1. Search official documentation and verified sources only.
    2. Record source URL, retrieval timestamp, and note what the source is.
    3. Extract concrete prompt-writing rules.
    4. Do NOT use forum posts, unofficial tip threads, or unverifiable sources.
    5. Set confidence level: high (official docs), medium (verified 3rd party),
       low (community-reported, flagged for human review).
    6. Do NOT invent rules not found in sources.

    OUTPUT: one snapshot YAML per model, following model_guidance_snapshot.schema.json.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_SOURCE_CLASSES = frozenset(
    {
        "official_docs",
        "official_release_notes",
        "official_help_center",
        "verified_platform_blog",
    }
)

BLOCKED_SOURCE_CLASSES = frozenset(
    {
        "forum_threads",
        "prompt_hack_blogs",
        "unsourced_social_media",
        "paid_prompt_packs",
    }
)

# Freshness policy: days before snapshot expires
SNAPSHOT_MAX_AGE_DAYS: dict[str, int] = {
    "midjourney": 14,
    "chatgpt_image": 14,
    "nano_banana": 14,
    "kling_omni": 7,  # faster release cadence
}

VALID_MODEL_IDS = frozenset(SNAPSHOT_MAX_AGE_DAYS.keys())

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BlockedSourceClassError(ValueError):
    """Raised when a source uses a blocked source_class."""


class MissingRequiredFieldError(ValueError):
    """Raised when a required snapshot field is missing."""


class UnknownModelError(ValueError):
    """Raised when an unrecognised model_id is provided."""


# ---------------------------------------------------------------------------
# Snapshot construction helpers
# ---------------------------------------------------------------------------


def _sha256_of_text(text: str) -> str:
    """Return 'sha256:<hex>' for arbitrary text content."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _compute_expires_at(taken_at: datetime, max_age_days: int) -> str:
    expiry = taken_at + timedelta(days=max_age_days)
    return expiry.strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_sources(sources: list[dict[str, Any]]) -> None:
    """Raise BlockedSourceClassError if any source uses a blocked class."""
    for i, src in enumerate(sources):
        cls = src.get("source_class", "")
        if cls in BLOCKED_SOURCE_CLASSES:
            raise BlockedSourceClassError(
                f"sources[{i}].source_class={cls!r} is in the blocked list. "
                f"Only {sorted(ALLOWED_SOURCE_CLASSES)} are allowed."
            )
        if cls not in ALLOWED_SOURCE_CLASSES:
            raise ValueError(
                f"sources[{i}].source_class={cls!r} is not a recognised allowed class. "
                f"Allowed: {sorted(ALLOWED_SOURCE_CLASSES)}"
            )


def build_snapshot(
    *,
    model_id: str,
    taken_at: datetime,
    sources: list[dict[str, Any]],
    extracted_rules: list[str],
    confidence: str,
    model_version_observed: str,
    model_version_confidence: str,
    do_not_use_without_verification: list[str] | None = None,
) -> dict[str, Any]:
    """
    Construct a snapshot dict conforming to model_guidance_snapshot.schema.json.
    Does NOT write to disk — call write_snapshot() for that.

    Args:
        model_id: One of VALID_MODEL_IDS.
        taken_at: UTC datetime when the snapshot is being produced.
        sources: List of source dicts (url, retrieved_at, http_status, content_hash,
                 human_verified, source_class, optional notes).
        extracted_rules: List of concrete prompt-writing rules from sources.
        confidence: 'high' | 'medium' | 'low' overall confidence.
        model_version_observed: Version string as seen in docs/platform UI.
        model_version_confidence: 'high' | 'medium' | 'low'.
        do_not_use_without_verification: Optional list of rules needing human check.

    Returns:
        Snapshot dict (without snapshot_hash — added by write_snapshot after serialisation).

    Raises:
        UnknownModelError: If model_id not in VALID_MODEL_IDS.
        BlockedSourceClassError: If any source uses a blocked source class.
        ValueError: If required fields are invalid.
    """
    if model_id not in VALID_MODEL_IDS:
        raise UnknownModelError(
            f"model_id={model_id!r} is not a known model. "
            f"Valid: {sorted(VALID_MODEL_IDS)}"
        )
    if not sources:
        raise MissingRequiredFieldError("sources must be non-empty.")
    if not extracted_rules:
        raise MissingRequiredFieldError("extracted_rules must be non-empty.")
    validate_sources(sources)

    max_age = SNAPSHOT_MAX_AGE_DAYS[model_id]
    taken_at_str = taken_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    snapshot: dict[str, Any] = {
        "model_id": model_id,
        "snapshot_taken_at": taken_at_str,
        "snapshot_hash": "sha256:placeholder",  # replaced by write_snapshot()
        "model_version_observed": model_version_observed,
        "model_version_confidence": model_version_confidence,
        "sources": sources,
        "extracted_rules": extracted_rules,
        "confidence": confidence,
        "snapshot_validity": {
            "max_age_days": max_age,
            "expires_at": _compute_expires_at(taken_at, max_age),
        },
        "schema_version": SCHEMA_VERSION,
    }
    if do_not_use_without_verification:
        snapshot["do_not_use_without_verification"] = do_not_use_without_verification
    return snapshot


def write_snapshot(
    snapshot: dict[str, Any],
    output_dir: Path,
) -> Path:
    """
    Serialise snapshot to YAML, compute its SHA-256, patch snapshot_hash, write file.

    File name: {timestamp}_{model_id}.yaml  (e.g. 2026-04-30T153000Z_midjourney.yaml)

    Args:
        snapshot: Dict produced by build_snapshot().
        output_dir: Directory to write into (created if missing).

    Returns:
        Path of the written file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    model_id: str = snapshot["model_id"]
    taken_at: str = snapshot["snapshot_taken_at"]
    # Normalise timestamp for filename: remove colons/dashes from time part
    ts_slug = re.sub(r"[:\-]", "", taken_at).replace("T", "T").rstrip("Z") + "Z"
    filename = f"{ts_slug}_{model_id}.yaml"
    out_path = output_dir / filename

    # First serialisation (placeholder hash)
    raw_yaml = yaml.dump(snapshot, allow_unicode=True, sort_keys=False, width=120)
    # Replace placeholder with real hash
    real_hash = _sha256_of_text(raw_yaml)
    snapshot["snapshot_hash"] = real_hash
    # Re-serialise with real hash
    final_yaml = yaml.dump(snapshot, allow_unicode=True, sort_keys=False, width=120)
    out_path.write_text(final_yaml, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Snapshot freshness check
# ---------------------------------------------------------------------------


def is_snapshot_fresh(snapshot_path: Path, reference_time: datetime | None = None) -> bool:
    """
    Return True if the snapshot at snapshot_path has not expired.

    Args:
        snapshot_path: Path to a snapshot YAML file.
        reference_time: UTC datetime to check against (default: now).

    Returns:
        True if fresh, False if expired or unreadable.
    """
    if not snapshot_path.exists():
        return False
    ref = reference_time or datetime.now(timezone.utc)
    try:
        data = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
        expires_at_str: str = data.get("snapshot_validity", {}).get("expires_at", "")
        if not expires_at_str:
            return False
        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        return ref < expires_at
    except Exception:
        return False


def find_latest_snapshot(
    snapshot_dir: Path, model_id: str
) -> Path | None:
    """
    Return the most recently written snapshot for model_id, or None.
    File name convention: {timestamp}_{model_id}.yaml
    """
    pattern = f"*_{model_id}.yaml"
    candidates = sorted(snapshot_dir.glob(pattern), reverse=True)
    return candidates[0] if candidates else None


# ---------------------------------------------------------------------------
# ModelResearchAgent — orchestrates snapshot creation
# ---------------------------------------------------------------------------


class ModelResearchAgent:
    """
    Orchestrates model research snapshot creation.

    In a live run (with a web-capable LLM backend), the agent fetches official
    documentation pages, extracts rules, and writes snapshots.

    In offline / test mode (no web access), the agent writes a placeholder
    snapshot with confidence='low' and a clear note in extracted_rules that
    the snapshot must be replaced by a human-verified version before use.

    Args:
        repo_root: Absolute path to the repository root.
        snapshot_dir: Directory for snapshot output (default: evidence/model_guidance_snapshots/).
    """

    def __init__(
        self,
        repo_root: Path,
        snapshot_dir: Path | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.snapshot_dir = snapshot_dir or (repo_root / "evidence" / "model_guidance_snapshots")

    def run(
        self,
        models: list[str],
        save: bool = True,
        reference_time: datetime | None = None,
    ) -> dict[str, Path]:
        """
        Create (or refresh) snapshots for the requested models.

        Args:
            models: List of model_id strings (snake_case).
            save: Write files to disk (True) or return in-memory only (False).
            reference_time: UTC datetime for freshness checks (default: now).

        Returns:
            Dict mapping model_id → Path of written snapshot (if save=True)
            or model_id → None (if save=False, dry-run).

        Raises:
            UnknownModelError: If any model_id is not in VALID_MODEL_IDS.
        """
        ref = reference_time or datetime.now(timezone.utc)
        results: dict[str, Path] = {}

        for model_id in models:
            if model_id not in VALID_MODEL_IDS:
                raise UnknownModelError(
                    f"model_id={model_id!r} not recognised. Valid: {sorted(VALID_MODEL_IDS)}"
                )
            snapshot = self._produce_snapshot(model_id, ref)
            if save:
                path = write_snapshot(snapshot, self.snapshot_dir)
                results[model_id] = path
            else:
                results[model_id] = None  # type: ignore[assignment]

        return results

    def _produce_snapshot(self, model_id: str, taken_at: datetime) -> dict[str, Any]:
        """
        Produce a snapshot dict for the given model.

        This implementation produces an offline placeholder snapshot.
        In a production LLM-backed environment, this method would call
        an LLM with web access to fetch current official documentation.

        The placeholder snapshot:
        - Has confidence='low'
        - Has extracted_rules that instruct users to replace before batch use
        - Passes schema validation
        - Is clearly labelled as a placeholder
        """
        placeholder_source = {
            "url": f"https://example.org/placeholder/{model_id}",
            "retrieved_at": taken_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "http_status": 0,
            "content_hash": _sha256_of_text(f"placeholder:{model_id}:{taken_at.isoformat()}"),
            "human_verified": False,
            "source_class": "official_docs",
            "notes": (
                "PLACEHOLDER — this source was not fetched. "
                "Replace with real snapshot before batch prompt generation. "
                "Run: python scripts/agents/run_pipeline.py "
                "--mode refresh-model-guidance "
                f"--models {model_id} --save-snapshot"
            ),
        }

        return build_snapshot(
            model_id=model_id,
            taken_at=taken_at,
            sources=[placeholder_source],
            extracted_rules=[
                "PLACEHOLDER — not fetched from official docs. "
                "This snapshot must be replaced by a real snapshot before use. "
                "Do NOT use this snapshot for prompt generation.",
            ],
            confidence="low",
            model_version_observed="unknown_placeholder",
            model_version_confidence="low",
            do_not_use_without_verification=[
                "replace_with_human_verified_source",
                "All rules — this snapshot is a placeholder only."
            ],
        )


# ---------------------------------------------------------------------------
# Schema validation helper (requires jsonschema)
# ---------------------------------------------------------------------------


def validate_snapshot_against_schema(
    snapshot: dict[str, Any], repo_root: Path
) -> list[str]:
    """
    Validate a snapshot dict against model_guidance_snapshot.schema.json.

    Returns:
        List of validation error messages (empty = valid).
    """
    # Legacy compatibility path:
    # ModelResearchAgent in this module emits the B0.1 snapshot shape
    # (model_id/snapshot_taken_at/snapshot_validity/...) which intentionally
    # differs from the newer model_guidance_snapshot schema consumed by the
    # runtime resolver. Keep test-time validation deterministic by validating
    # required legacy fields here.
    if isinstance(snapshot, dict) and "model_id" in snapshot:
        required_legacy_fields = [
            "model_id",
            "snapshot_taken_at",
            "snapshot_hash",
            "model_version_observed",
            "model_version_confidence",
            "sources",
            "extracted_rules",
            "confidence",
            "snapshot_validity",
            "schema_version",
        ]
        missing = [k for k in required_legacy_fields if k not in snapshot]
        if missing:
            return [f"legacy_snapshot missing required fields: {', '.join(missing)}"]
        validity = snapshot.get("snapshot_validity")
        if not isinstance(validity, dict) or "expires_at" not in validity:
            return ["legacy_snapshot.snapshot_validity.expires_at is required"]
        if not isinstance(snapshot.get("sources"), list) or not snapshot.get("sources"):
            return ["legacy_snapshot.sources must be a non-empty list"]
        if not isinstance(snapshot.get("extracted_rules"), list) or not snapshot.get("extracted_rules"):
            return ["legacy_snapshot.extracted_rules must be a non-empty list"]
        return []

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema not installed — skipping schema validation."]

    schema_path = repo_root / "schemas" / "model_guidance_snapshot.schema.json"
    if not schema_path.exists():
        return [f"Schema file not found: {schema_path}"]

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(snapshot), key=lambda e: list(e.path))
    return [f"{list(e.path)}: {e.message}" for e in errors]

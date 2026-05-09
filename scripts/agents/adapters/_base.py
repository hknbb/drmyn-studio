"""
Base adapter for Batch 4.

Provides BaseAdapter, BriefNotReadyError, and shared helpers used by all
model-specific adapters (midjourney, chatgpt_image, nano_banana, kling_omni).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.agents.model_guidance_resolver import (
    ModelGuidanceResolutionError,
    resolve_model_guidance,
)
from scripts.agents.neutral_brief import NeutralBrief


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BriefNotReadyError(RuntimeError):
    """
    Raised by an adapter when ``brief.is_ready is False``.

    The brief has UNRESOLVED continuity markers that must be resolved before
    a prompt can be generated from it.
    """


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Patterns for first-clause extraction (compact style)
_CLAUSE_SEP_RE = re.compile(r"[.;]")

# Mapping from element_type to prompt_type enum value in prompt_record.schema.json
ELEMENT_TO_PROMPT_TYPE: dict[str, str] = {
    "character": "t2i_character_element",
    "location": "t2i_location_element",
    "prop": "t2i_prop_element",
    "wardrobe": "t2i_wardrobe_element",
    "style": "t2i_style_reference",
}

# Mapping from element_type to short slug prefix for prompt_id
ELEMENT_TO_SLUG: dict[str, str] = {
    "character": "char",
    "location": "loc",
    "prop": "prop",
    "wardrobe": "ward",
    "style": "style",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compact(text: str, max_words: int = 12) -> str:
    """
    Extract the first clause from *text*, capped at *max_words* words.

    Splits on ``;`` or ``.`` to get the first clause, then word-limits.
    """
    if not text:
        return ""
    m = _CLAUSE_SEP_RE.search(text)
    if m:
        text = text[: m.start()]
    words = text.split()
    return " ".join(words[:max_words])


def _build_source_refs(brief: NeutralBrief) -> dict[str, Any]:
    """
    Build the ``source_refs`` block for a prompt record from a NeutralBrief.

    Returns only the fields allowed by prompt_record.schema.json.
    """
    scene_id = brief.scene_id
    refs: dict[str, Any] = {
        "scene_card": f"planning/scenes/{scene_id}/scene_card.yaml",
        "scene_excerpt": f"planning/scenes/{scene_id}/scene_excerpt.md",
    }

    if brief.element_type == "character":
        refs["character_refs"] = [brief.element_id]
    elif brief.element_type == "location":
        refs["location_refs"] = [brief.element_id]
    elif brief.element_type == "prop":
        refs["prop_refs"] = [brief.element_id]
    elif brief.element_type == "wardrobe":
        refs["wardrobe_refs"] = [brief.element_id]

    if brief.aesthetic_pack_refs:
        refs["aesthetic_refs"] = list(brief.aesthetic_pack_refs)

    return refs


def _element_id_slug(element_id: str) -> str:
    """Normalise element_id for use in a prompt_id slug (lowercase, _ → -)."""
    return element_id.lower().replace("_", "-")


# ---------------------------------------------------------------------------
# BaseAdapter
# ---------------------------------------------------------------------------


class BaseAdapter:
    """
    Abstract base for model-specific T2I prompt adapters.

    Subclasses must implement:
    - ``MODEL_ID``  (snake_case canonical model ID)
    - ``MODEL_SLUG`` (kebab-case model ID as used in prompt_ids)
    - ``ABBREV``   (uppercase abbreviation for run_id)
    - ``_build_prompt_text(brief)``
    - ``_build_negative_prompt(brief)`` — optional override; returns None by default
    - ``_extra_generation_params(brief)`` — optional override for model-specific params

    Subclasses targeting dynamic model resolution should set:
    - ``INTERNAL_MODEL_TARGET`` — one of kling_omni_video_best_available,
      midjourney_image_best_available, chatgpt_image_best_available,
      nano_banana_best_available
    """

    MODEL_ID: str = ""
    MODEL_SLUG: str = ""
    ABBREV: str = ""
    INTERNAL_MODEL_TARGET: str = ""

    def __init__(
        self,
        repo_root: str | Path,
        *,
        model_guidance_mode: str = "locked_guide",
        model_guidance_snapshot: str | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.model_guidance_mode = model_guidance_mode
        self.model_guidance_snapshot = model_guidance_snapshot

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        brief: NeutralBrief,
        version: int = 1,
        *,
        run_counter: int = 1,
        run_at: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Generate a (prompt_record, run_record) pair from a NeutralBrief.

        Raises BriefNotReadyError if ``brief.is_ready is False``.
        """
        if not brief.is_ready:
            raise BriefNotReadyError(
                f"Brief for {brief.element_type}.{brief.element_id} is not ready "
                f"(scene {brief.scene_id}): {brief.warnings}"
            )

        prompt_id = self._build_prompt_id(brief, version)
        prompt_text = self._build_prompt_text(brief)
        negative_prompt = self._build_negative_prompt(brief)
        generation_params = self._generation_params(brief)

        prompt_record: dict[str, Any] = {
            "prompt_id": prompt_id,
            "scene_id": brief.scene_id,
            "prompt_type": ELEMENT_TO_PROMPT_TYPE.get(
                brief.element_type, "t2i_character_element"
            ),
            "lifecycle_stage": "draft",
            "target_models": [self.MODEL_ID],
            "source_refs": _build_source_refs(brief),
            "prompt_text": prompt_text,
            "generation_params": generation_params,
            "expected_output": {
                "asset_type": "image_set",
                "variation_count": 4,
            },
            "status": "active",
            "canon_lock": False,
        }

        # Include negative_prompt only when non-None (ChatGPT Image omits it)
        if negative_prompt is not None:
            prompt_record["negative_prompt"] = negative_prompt

        run_record: dict[str, Any] = {
            "run_id": f"RUN_{brief.scene_id}_{self.ABBREV}_{run_counter:04d}",
            "prompt_id": prompt_id,
            "model": self.MODEL_ID,
            "run_at": run_at or _now_iso(),
            "outputs_expected": 4,
            "cost": {"unit": "credits", "value": 1},
            "status": "pending",
        }
        if self.model_guidance_snapshot:
            run_record["model_guidance_snapshot"] = self.model_guidance_snapshot

        return prompt_record, run_record

    # ------------------------------------------------------------------
    # Abstract / override-able methods
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:  # pragma: no cover
        raise NotImplementedError(
            f"{type(self).__name__} must implement _build_prompt_text"
        )

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        """Return None to omit negative_prompt from the record."""
        return None

    def _extra_generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        """Override to inject model-specific generation_params fields."""
        return {}

    def _resolve_model(
        self,
        internal_model_target: str,
        required_feature: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve current model version from a human-verified snapshot.

        Args:
            internal_model_target: One of kling_omni_video_best_available,
                midjourney_image_best_available, chatgpt_image_best_available,
                nano_banana_best_available.
            required_feature: Optional feature (e.g., 'omni_reference').

        Returns:
            Dict with model_guidance_snapshot_ref, provider, provider_surface,
            resolved_model_name, resolved_model_role, guidance_observed_at,
            guidance_expires_at, prompting_rules, capabilities, constraints.

        Raises:
            ModelGuidanceResolutionError if snapshot is missing, expired,
            unverified, contains placeholders, or unsupported feature.
        """
        return resolve_model_guidance(
            repo_root=self.repo_root,
            internal_model_target=internal_model_target,
            required_feature=required_feature,
        )

    # ------------------------------------------------------------------
    # Shared internals
    # ------------------------------------------------------------------

    def _build_prompt_id(self, brief: NeutralBrief, version: int) -> str:
        type_slug = ELEMENT_TO_SLUG.get(brief.element_type, brief.element_type[:4])
        element_slug = _element_id_slug(brief.element_id)
        return (
            f"{brief.scene_id}__"
            f"t2i-{type_slug}-{element_slug}-{self.MODEL_SLUG}__"
            f"v{version:02d}"
        )

    def _generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model_guidance_mode": self.model_guidance_mode,
            "adapter_name": self.MODEL_ID,
        }

        # Dynamic model resolution: resolve from snapshot at runtime
        if self.model_guidance_mode == "dynamic_snapshot":
            if not self.INTERNAL_MODEL_TARGET:
                raise ValueError(
                    f"{type(self).__name__} has model_guidance_mode='dynamic_snapshot' "
                    f"but INTERNAL_MODEL_TARGET is not set"
                )
            resolved = self._resolve_model(self.INTERNAL_MODEL_TARGET)
            params.update({
                "model_guidance_snapshot_ref": resolved["model_guidance_snapshot_ref"],
                "provider": resolved["provider"],
                "provider_surface": resolved["provider_surface"],
                "resolved_model_name": resolved["resolved_model_name"],
                "resolved_model_role": resolved["resolved_model_role"],
                "guidance_observed_at": resolved["guidance_observed_at"],
                "guidance_expires_at": resolved["guidance_expires_at"],
            })
        else:
            # Legacy mode: locked_guide (default)
            params["model_guidance_ref"] = f"docs/model_guides/{self.MODEL_ID}.yaml"
            if self.model_guidance_snapshot:
                params["model_guidance_snapshot"] = self.model_guidance_snapshot

        if brief.aesthetic_keywords:
            params["aesthetic_keywords_injected"] = list(brief.aesthetic_keywords)
        if brief.planning_aliases:
            params["planning_name_filter"] = {"forbidden": list(brief.planning_aliases)}
        params.update(self._extra_generation_params(brief))
        return params

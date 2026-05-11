"""
Google image generation T2I prompt adapter for Batch 4.

Targets nano_banana_best_available (Google Gemini image model, resolved from
model_guidance_snapshot at runtime).

Style: narrative identity-consistency framing. Subject is introduced first with
an explicit identity/reference framing phrase. Visual anchors follow as
descriptive sentences. Constraints are embedded as semantic negation (Avoid:
clause) — the resolved Google model does NOT support a separate negative_prompt
parameter.
"""

from __future__ import annotations

from typing import Any

from scripts.agents.adapters._base import BaseAdapter
from scripts.agents.neutral_brief import NeutralBrief


class NanaBananaAdapter(BaseAdapter):
    """
    Generates Google image model prompt records via nano_banana_best_available.

    Model version resolved from model_guidance_snapshot at runtime, not hardcoded.
    Prompt style: narrative identity-consistency reference framing.
    Negative prompt: NOT populated (supports_negative_prompt=false).
    Constraints embedded via semantic negation in prompt_text.
    generation_params: constraint_strategy=embedded_positive_constraints.
    Capability: supports_identity_consistency=true (up to 5 char refs).
    """

    MODEL_ID = "nano_banana"
    MODEL_SLUG = "nano-banana"
    ABBREV = "NB"

    # ------------------------------------------------------------------
    # generation_params — constraint strategy
    # ------------------------------------------------------------------

    def _extra_generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        params: dict[str, Any] = {
            "constraint_strategy": "embedded_positive_constraints",
            "recommended_ar": "16:9 or 21:9",
            "max_prompt_tokens": 480,
        }
        if brief.character_reference_refs:
            params["character_reference_refs"] = list(brief.character_reference_refs[:5])
        if brief.object_reference_refs:
            params["object_reference_refs"] = list(brief.object_reference_refs[:6])
        return params

    # ------------------------------------------------------------------
    # Prompt text — narrative identity-consistency framing
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        parts: list[str] = []

        # Identity framing phrase
        frame = self._identity_frame(brief)
        if frame:
            parts.append(frame)

        # Continuity state
        if brief.continuity_state:
            parts.append(f"Current state: {brief.continuity_state[:300]}")

        # Visual anchors — descriptive sentences, up to 4
        for anchor in brief.visual_anchors[:4]:
            desc = anchor.description.strip()
            if desc:
                parts.append(desc[:300])

        # World consistency anchor — aesthetic keywords as identity grounding
        if brief.aesthetic_keywords:
            anchor = "World consistency: " + ", ".join(brief.aesthetic_keywords) + "."
            parts.append(anchor)

        parts.append("Use cinematic photography vocabulary: lens choice, film stock behavior, and motivated lighting.")

        # Semantic negation — embed constraints as "Avoid:" clause (no separate field)
        if brief.negative_constraints:
            avoid = "Avoid: " + "; ".join(brief.negative_constraints[:6]) + "."
            parts.append(avoid)

        # Closing identity-consistency note for character/wardrobe
        if brief.element_type in ("character", "wardrobe"):
            parts.append("Use for consistent identity generation across scenes.")

        return " ".join(parts) if parts else "(no visual anchors available)"

    # ------------------------------------------------------------------
    # Negative prompt — omitted (not supported by resolved Google model)
    # ------------------------------------------------------------------

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        # Resolved Google model has no negative_prompt parameter.
        # Constraints are embedded via semantic negation in _build_prompt_text.
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _identity_frame(brief: NeutralBrief) -> str:
        # Use safe label; skip element_name if planning_aliases present (would leak)
        name = brief.prompt_subject_label or (
            brief.element_name if not brief.planning_aliases else ""
        )
        match brief.element_type:
            case "character":
                return f"Character identity reference: {name}." if name else "Character identity reference."
            case "location":
                return f"Location reference: {name}." if name else "Location reference."
            case "prop":
                return f"Prop reference: {name}." if name else "Prop reference."
            case "wardrobe":
                return f"Wardrobe reference: {name}." if name else "Wardrobe reference."
            case "style":
                return "Style reference for production continuity."
            case _:
                return f"Reference: {name}." if name else ""

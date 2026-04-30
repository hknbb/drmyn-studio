"""
Nano Banana T2I prompt adapter for Batch 4.

Style: identity-consistency framing. Subject is introduced first with an
explicit identity/reference framing phrase. Negative prompt populated
(model supports it). Visual anchors follow in descriptive sentences.
"""

from __future__ import annotations

from scripts.agents.adapters._base import BaseAdapter
from scripts.agents.neutral_brief import NeutralBrief


class NanaBananaAdapter(BaseAdapter):
    """
    Generates Nano Banana-style prompt records from a NeutralBrief.

    Prompt style: identity-consistency reference framing with descriptive
    visual sentences.
    Negative prompt: populated (model capability: supports_negative_prompt=true).
    Capability: supports_identity_consistency=true.
    """

    MODEL_ID = "nano_banana"
    MODEL_SLUG = "nano-banana"
    ABBREV = "NB"

    # ------------------------------------------------------------------
    # Prompt text — identity-consistency framing
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

        # Closing identity-consistency note for character/wardrobe
        if brief.element_type in ("character", "wardrobe"):
            parts.append("Use for consistent identity generation across scenes.")

        return " ".join(parts) if parts else "(no visual anchors available)"

    # ------------------------------------------------------------------
    # Negative prompt — semicolon-separated constraints
    # ------------------------------------------------------------------

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        if not brief.negative_constraints:
            return None
        # Include first 8 constraints; keep concise
        return "; ".join(brief.negative_constraints[:8])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _identity_frame(brief: NeutralBrief) -> str:
        name = brief.element_name
        match brief.element_type:
            case "character":
                return f"Character identity reference: {name}."
            case "location":
                return f"Location reference: {name}."
            case "prop":
                return f"Prop reference: {name}."
            case "wardrobe":
                return f"Wardrobe reference: {name}."
            case "style":
                return "Style reference for production continuity."
            case _:
                return f"Reference: {name}." if name else ""

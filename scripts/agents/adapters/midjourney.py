"""
Midjourney T2I prompt adapter for Batch 4.

Style: compact visual clauses, ≤80 words. Subject leads; each anchor is
stripped to its first clause (≤12 words). Negative prompt is populated
(model supports --no flag in practice; schema field carries the list).
"""

from __future__ import annotations

from scripts.agents.adapters._base import BaseAdapter, _compact
from scripts.agents.neutral_brief import NeutralBrief


class MidjourneyAdapter(BaseAdapter):
    """
    Generates Midjourney-style prompt records from a NeutralBrief.

    Prompt style: comma-separated compact clauses, ≤80 words.
    Negative prompt: comma-separated constraints, ≤60 words.
    Capability: supports_negative_prompt=limited (--no flag in practice).
    """

    MODEL_ID = "midjourney"
    MODEL_SLUG = "midjourney"
    ABBREV = "MJ"

    # ------------------------------------------------------------------
    # Prompt text — compact visual clauses, ≤80 words
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        parts: list[str] = []

        # Leading subject (not for style briefs)
        if brief.element_type != "style" and brief.element_name:
            parts.append(brief.element_name)

        # Continuity state as a compact clause for prop/wardrobe
        if brief.element_type in ("prop", "wardrobe") and brief.continuity_state:
            state_clause = _compact(brief.continuity_state, max_words=12)
            if state_clause:
                parts.append(state_clause)

        # Visual anchor clauses — top 5
        for anchor in brief.visual_anchors[:5]:
            clause = _compact(anchor.description, max_words=12)
            if clause:
                parts.append(clause)

        if not parts:
            return "(no visual anchors available)"

        text = ", ".join(parts)

        # Enforce ≤80 words
        words = text.split()
        if len(words) > 80:
            text = " ".join(words[:80])

        return text

    # ------------------------------------------------------------------
    # Negative prompt — comma-separated, ≤60 words
    # ------------------------------------------------------------------

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        if not brief.negative_constraints:
            return None

        neg_parts: list[str] = []
        total_words = 0
        for constraint in brief.negative_constraints:
            words = constraint.split()
            if total_words + len(words) > 60:
                break
            neg_parts.append(constraint)
            total_words += len(words)

        return ", ".join(neg_parts) if neg_parts else None

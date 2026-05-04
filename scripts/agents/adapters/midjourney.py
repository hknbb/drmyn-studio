"""
Midjourney T2I prompt adapter for Batch 4.

Style: compact visual clauses, ≤60 words (updated from research: attention
drops after 60 words, priority window is first 40). Subject leads; each
anchor is stripped to its first clause (≤12 words). Negative prompt uses
hyphenated compact terms for --no flag (Midjourney splits --no on spaces,
so multi-word terms must use hyphens).
"""

from __future__ import annotations

from typing import Any

from scripts.agents.adapters._base import BaseAdapter, _compact
from scripts.agents.neutral_brief import NeutralBrief


# Updated from web research 2026-05-04: attention drops after 60 words
_WORD_LIMIT = 60


class MidjourneyAdapter(BaseAdapter):
    """
    Generates Midjourney-style prompt records from a NeutralBrief.

    Prompt style: comma-separated compact clauses, ≤60 words.
    Negative prompt: hyphenated compact terms for --no flag.
    Capability: supports_negative_prompt=limited (--no flag in practice).
    """

    MODEL_ID = "midjourney"
    MODEL_SLUG = "midjourney"
    ABBREV = "MJ"

    # ------------------------------------------------------------------
    # generation_params — model version and AR recommendations
    # ------------------------------------------------------------------

    def _extra_generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        return {
            "recommended_model_version": "--v 7",
            "recommended_ar": "--ar 16:9",
        }

    # ------------------------------------------------------------------
    # Prompt text — compact visual clauses, ≤60 words
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        parts: list[str] = []

        # Leading subject — use safe label; skip if no safe label but aliases exist (e.g. location)
        if brief.element_type != "style":
            if brief.prompt_subject_label:
                parts.append(brief.prompt_subject_label)
            elif brief.element_name and not brief.planning_aliases:
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

        # Aesthetic tail: append pack keywords within remaining word budget
        if brief.aesthetic_keywords:
            aesthetic_tail = ", ".join(brief.aesthetic_keywords)
            candidate = f"{text}, {aesthetic_tail}"
            words = candidate.split()
            if len(words) <= _WORD_LIMIT:
                text = candidate
            else:
                # Fit as many aesthetic keywords as the budget allows
                base_words = text.split()
                budget = _WORD_LIMIT - len(base_words) - 1  # -1 for separator comma
                if budget > 0:
                    tail_words = aesthetic_tail.split()[:budget]
                    text = text + ", " + " ".join(tail_words)

        # Enforce word limit
        words = text.split()
        if len(words) > _WORD_LIMIT:
            text = " ".join(words[:_WORD_LIMIT])

        return text

    # ------------------------------------------------------------------
    # Negative prompt — hyphenated compact terms for --no, ≤20 terms
    # ------------------------------------------------------------------

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        """
        Build --no term list. Midjourney splits --no on spaces (word-by-word),
        so multi-word constraint phrases are converted to hyphenated compact
        terms (≤4 tokens each) to avoid unintended word-level splitting.
        """
        if not brief.negative_constraints:
            return None

        neg_terms: list[str] = []
        for constraint in brief.negative_constraints[:20]:
            tokens = [t.lower().rstrip(".,;:") for t in constraint.split()[:4]]
            term = "-".join(tokens)
            if term:
                neg_terms.append(term)

        return ", ".join(neg_terms) if neg_terms else None

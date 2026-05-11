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


_PRIORITY_WORDS = 40
_SOFT_LIMIT = 80
_HARD_LIMIT = 200


class MidjourneyAdapter(BaseAdapter):
    """
    Generates Midjourney-style prompt records from a NeutralBrief.

    Prompt style: comma-separated compact clauses, ≤60 words.
    Negative prompt: hyphenated compact terms for --no flag.
    Capability: supports_negative_prompt=limited (--no flag in practice).
    Model version resolved from model_guidance_snapshot at runtime, not hardcoded.
    """

    MODEL_ID = "midjourney"
    MODEL_SLUG = "midjourney"
    ABBREV = "MJ"
    INTERNAL_MODEL_TARGET = "midjourney_image_best_available"

    # ------------------------------------------------------------------
    # generation_params — AR recommendation (model version from snapshot)
    # ------------------------------------------------------------------

    def _extra_generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        params: dict[str, Any] = {
            "recommended_ar": "--ar 16:9",
            "raw_mode": "--raw",
        }
        # Capability-gated style reference: only when snapshot explicitly supports it
        if self.model_guidance_mode == "dynamic_snapshot":
            try:
                resolved = self._resolve_model(self.INTERNAL_MODEL_TARGET)
                capabilities = resolved.get("capabilities") or {}
                if (
                    capabilities.get("supports_style_reference") is True
                    and brief.aesthetic_pack_refs
                ):
                    sref_seed = self._find_sref_seed(brief.aesthetic_pack_refs)
                    if sref_seed:
                        params["style_reference"] = f"--sref {sref_seed}"
            except Exception:
                pass
        return params

    # ------------------------------------------------------------------
    # Prompt text — natural language, soft-limited
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        parts: list[str] = []

        # Subject-first natural language sentence
        if brief.element_type != "style":
            if brief.prompt_subject_label:
                parts.append(f"Create a cinematic image of {brief.prompt_subject_label}.")
            elif brief.element_name and not brief.planning_aliases:
                parts.append(f"Create a cinematic image of {brief.element_name}.")

        # Continuity state as a compact clause for prop/wardrobe
        if brief.element_type in ("prop", "wardrobe") and brief.continuity_state:
            state_clause = _compact(brief.continuity_state, max_words=12)
            if state_clause:
                parts.append(f"Continuity state: {state_clause}.")

        # Visual anchor clauses — top 5
        for anchor in brief.visual_anchors[:5]:
            clause = _compact(anchor.description, max_words=12)
            if clause:
                parts.append(clause + ".")

        if not parts:
            return "(no visual anchors available)"

        # Aesthetic tail as natural language
        if brief.aesthetic_keywords:
            parts.append("Visual world cues: " + ", ".join(brief.aesthetic_keywords) + ".")

        text = " ".join(parts)

        # Soft and hard limits
        words = text.split()
        if len(words) > _HARD_LIMIT:
            text = " ".join(words[:_HARD_LIMIT])

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

    def _find_sref_seed(self, pack_refs: tuple[str, ...]) -> str | None:
        import yaml

        path = self.repo_root / "planning" / "aesthetic_bible.yaml"
        if not path.exists():
            return None
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None
        packs = doc.get("packs")
        if not isinstance(packs, list):
            return None
        for ref in pack_refs:
            for pack in packs:
                if isinstance(pack, dict) and pack.get("pack_id") == ref:
                    seed = pack.get("sref_seed")
                    if isinstance(seed, str) and seed.strip():
                        return seed.strip()
        return None

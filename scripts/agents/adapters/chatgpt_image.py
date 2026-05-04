"""
ChatGPT Image T2I prompt adapter for Batch 4.

Style: natural language task-framing. Constraints are embedded in positive
prompt text (``constraint_strategy: embedded_positive_constraints``) because
ChatGPT Image does not support a separate negative_prompt field.
"""

from __future__ import annotations

from typing import Any

from scripts.agents.adapters._base import BaseAdapter
from scripts.agents.neutral_brief import NeutralBrief


class ChatGPTImageAdapter(BaseAdapter):
    """
    Generates ChatGPT Image-style prompt records from a NeutralBrief.

    Prompt style: natural language instruction paragraph.
    Negative prompt: NOT populated (model capability: supports_negative_prompt=false).
    Constraints embedded in prompt_text via an "Avoid:" clause.
    generation_params: constraint_strategy=embedded_positive_constraints.
    """

    MODEL_ID = "chatgpt_image"
    MODEL_SLUG = "chatgpt-image"
    ABBREV = "CGPT"

    # ------------------------------------------------------------------
    # generation_params — adds constraint_strategy
    # ------------------------------------------------------------------

    def _extra_generation_params(self, brief: NeutralBrief) -> dict[str, Any]:
        return {
            "constraint_strategy": "embedded_positive_constraints",
            "recommended_quality": "medium",
            "prompt_structure": "scene→subject→details→constraints",
        }

    # ------------------------------------------------------------------
    # Prompt text — natural language with embedded constraints
    # ------------------------------------------------------------------

    def _build_prompt_text(self, brief: NeutralBrief) -> str:
        parts: list[str] = []

        # Task instruction
        task = self._task_instruction(brief)
        if task:
            parts.append(task)

        # Continuity state (full sentence)
        if brief.continuity_state:
            parts.append(
                f"Current continuity state: {brief.continuity_state[:300]}"
            )

        # Visual anchors — full descriptions, up to 4
        for anchor in brief.visual_anchors[:4]:
            desc = anchor.description.strip()
            if desc:
                parts.append(desc[:300])

        # Aesthetic world phrase — natural language, not raw comma-tail
        if brief.aesthetic_keywords:
            world_phrase = "Visual world: " + "; ".join(brief.aesthetic_keywords) + "."
            parts.append(world_phrase)

        # Embedded constraints (first 4 key constraints as an Avoid clause)
        constraints = brief.negative_constraints[:4]
        if constraints:
            avoid_clause = "Avoid: " + "; ".join(constraints) + "."
            parts.append(avoid_clause)

        return " ".join(parts) if parts else "(no visual anchors available)"

    # ------------------------------------------------------------------
    # Negative prompt — omitted (not supported by ChatGPT Image)
    # ------------------------------------------------------------------

    def _build_negative_prompt(self, brief: NeutralBrief) -> str | None:
        # ChatGPT Image does not support negative_prompt; constraints are
        # embedded in prompt_text via the "Avoid:" clause above.
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _task_instruction(brief: NeutralBrief) -> str:
        # Use safe label; skip element_name if planning_aliases present (would leak)
        name = brief.prompt_subject_label or (
            brief.element_name if not brief.planning_aliases else ""
        )
        match brief.element_type:
            case "character":
                return f"Generate a character reference image of {name}." if name else "Generate a character reference image."
            case "location":
                return f"Generate a location reference image of {name}." if name else "Generate a location reference image."
            case "prop":
                return f"Generate a prop reference image of {name}." if name else "Generate a prop reference image."
            case "wardrobe":
                return f"Generate a wardrobe reference image for {name}." if name else "Generate a wardrobe reference image."
            case "style":
                return "Generate a style reference image for this production."
            case _:
                return f"Generate a reference image of {name}." if name else ""

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
import yaml


class ChatGPTImageAdapter(BaseAdapter):
    """
    Generates ChatGPT Image-style prompt records from a NeutralBrief.

    Prompt style: natural language instruction paragraph.
    Negative prompt: NOT populated (model capability: supports_negative_prompt=false).
    Constraints embedded in prompt_text via an "Avoid:" clause.
    generation_params: constraint_strategy=embedded_positive_constraints.
    Model version resolved from model_guidance_snapshot at runtime, not hardcoded.
    """

    MODEL_ID = "chatgpt_image"
    MODEL_SLUG = "chatgpt-image"
    ABBREV = "CGPT"
    INTERNAL_MODEL_TARGET = "chatgpt_image_best_available"

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
        supports_multi_panel = self._supports_multi_panel()
        scene = self._task_instruction(brief) or "Generate a reference image."
        subject = brief.prompt_subject_label or "Subject from provided anchors"
        details = "; ".join(
            a.description.strip()[:300]
            for a in brief.visual_anchors[:4]
            if a.description.strip()
        ) or "Use grounded visual anchors only."
        constraints = "; ".join(brief.negative_constraints[:4]) if brief.negative_constraints else ""
        preserve = "; ".join(brief.preserve_list[:6]) if brief.preserve_list else ""

        if (
            brief.expected_output_layout == "multi_panel"
            and supports_multi_panel
            and brief.panel_prompts
        ):
            panel_lines = [f"Panel {i+1}: {p}" for i, p in enumerate(brief.panel_prompts[:8])]
            return (
                f"{scene} "
                f"Scene: {scene} "
                f"Subject: {subject}. "
                f"Details: {details}. "
                f"Visual world: {'; '.join(brief.aesthetic_keywords) if brief.aesthetic_keywords else 'grounded production realism'}. "
                f"Constraints: Avoid {constraints}. "
                f"Preserve: {preserve}. "
                + " ".join(panel_lines)
            )

        return (
            f"{scene} "
            f"Scene: {scene} "
            f"Subject: {subject}. "
            f"Details: {details}. "
            f"Visual world: {'; '.join(brief.aesthetic_keywords) if brief.aesthetic_keywords else 'grounded production realism'}. "
            f"Constraints: Avoid {constraints}. "
            f"Preserve: {preserve}."
        )

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

    def _supports_multi_panel(self) -> bool:
        # dynamic snapshot path
        if self.model_guidance_mode == "dynamic_snapshot":
            try:
                resolved = self._resolve_model(self.INTERNAL_MODEL_TARGET)
                caps = resolved.get("capabilities") or {}
                return bool(caps.get("supports_multi_panel") is True)
            except Exception:
                return False

        # locked guide path
        guide_path = self.repo_root / "docs" / "model_guides" / "chatgpt_image.yaml"
        if not guide_path.exists():
            return False
        try:
            guide = yaml.safe_load(guide_path.read_text(encoding="utf-8")) or {}
            cap = guide.get("capability") or {}
            return bool(cap.get("supports_multi_panel") is True)
        except Exception:
            return False

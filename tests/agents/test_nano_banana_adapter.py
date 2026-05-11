from __future__ import annotations

from pathlib import Path

from scripts.agents.adapters.nano_banana import NanaBananaAdapter
from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor


def _brief() -> NeutralBrief:
    return NeutralBrief(
        scene_id="SC0001",
        element_type="character",
        element_id="C01",
        element_name="Nadia Vale",
        visual_anchors=[VisualAnchor(description="Lean upright posture.", source_field="x")],
        negative_constraints=["cartoon look"],
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=True,
        prompt_subject_label="Nadia",
        planning_aliases=("Nadia Vale",),
        character_reference_refs=tuple(f"char_{i}.png" for i in range(8)),
        object_reference_refs=tuple(f"obj_{i}.png" for i in range(9)),
    )


def test_reference_caps_written_to_generation_params():
    adapter = NanaBananaAdapter(Path("."))
    params = adapter._generation_params(_brief())
    assert len(params["character_reference_refs"]) == 5
    assert len(params["object_reference_refs"]) == 6


def test_no_negative_prompt_field():
    adapter = NanaBananaAdapter(Path("."))
    assert adapter._build_negative_prompt(_brief()) is None


def test_photography_vocab_in_prompt():
    adapter = NanaBananaAdapter(Path("."))
    text = adapter._build_prompt_text(_brief())
    assert "lens" in text.lower()
    assert "film stock" in text.lower()
    assert "lighting" in text.lower()


def test_no_provider_model_version_hardcoded():
    src = Path("scripts/agents/adapters/nano_banana.py").read_text(encoding="utf-8").lower()
    assert "gemini-3-pro-image-preview" not in src

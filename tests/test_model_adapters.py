"""
tests/test_model_adapters.py — Batch 4

Tests for model-specific prompt adapters, MODEL_ALIAS_MAP, and prompt_run schema.
- Each adapter produces a schema-valid prompt record
- Prompt ID pattern, lifecycle_stage, target_models are correct per adapter
- Negative prompt presence / absence matches model capability
- ChatGPT Image has constraint_strategy in generation_params
- BriefNotReadyError raised on unready briefs
- MODEL_ALIAS_MAP structure and resolve_model_key correctness
- get_adapter() factory resolves all T2I models
- prompt_run.schema.json validates a well-formed run record
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.adapters import (  # noqa: E402
    MODEL_ALIAS_MAP,
    BriefNotReadyError,
    get_adapter,
    resolve_model_key,
)
from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter  # noqa: E402
from scripts.agents.adapters.midjourney import MidjourneyAdapter  # noqa: E402
from scripts.agents.adapters.nano_banana import NanaBananaAdapter  # noqa: E402
from scripts.agents.neutral_brief import NeutralBrief, VisualAnchor  # noqa: E402


# ---------------------------------------------------------------------------
# Inline fixtures
# ---------------------------------------------------------------------------

_ANCHOR = lambda desc, field: VisualAnchor(description=desc, source_field=field)


def _make_brief(
    *,
    scene_id: str = "SC0003",
    element_type: str = "character",
    element_id: str = "C01",
    element_name: str = "Nadia Vale",
    visual_anchors: list | None = None,
    negative_constraints: list | None = None,
    continuity_state: str | None = None,
    is_ready: bool = True,
    warnings: list | None = None,
) -> NeutralBrief:
    return NeutralBrief(
        scene_id=scene_id,
        element_type=element_type,
        element_id=element_id,
        element_name=element_name,
        visual_anchors=visual_anchors
        or [
            _ANCHOR("Lean, upright, economical silhouette.", "character.C01.visual_profile.silhouette"),
            _ANCHOR("Muted neutrals and controlled domestic tones.", "character.C01.visual_profile.color_bias"),
            _ANCHOR("Elite domestic presentation, always practical.", "character.C01.visual_profile.costume_logic"),
        ],
        negative_constraints=negative_constraints
        or [
            "Do not soften her into generalized maternal warmth.",
            "Neon cyberpunk color design.",
            "Teal-orange blockbuster simplification.",
        ],
        continuity_state=continuity_state,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=is_ready,
        warnings=warnings or [],
    )


CHAR_BRIEF = _make_brief()

PROP_BRIEF = _make_brief(
    element_type="prop",
    element_id="PROP001",
    element_name="Jin's medical bracelet",
    visual_anchors=[
        _ANCHOR(
            "Thin hospital-style plastic bracelet with printed ID strip.",
            "prop.PROP001.visual_description",
        ),
    ],
    continuity_state="White plastic hospital bracelet; Nadia listed as registrant.",
)

UNREADY_BRIEF = _make_brief(
    is_ready=False,
    warnings=["WARNING: unresolved continuity state - do not use in prompt"],
)

STYLE_BRIEF = _make_brief(
    element_type="style",
    element_id="style_bible",
    element_name="Style Bible",
    visual_anchors=[
        _ANCHOR(
            "Controlled world revealing the machinery under its finish.",
            "style_bible.visual_thesis",
        )
    ],
    continuity_state=None,
)

PROMPT_ID_RE = re.compile(r"^SC\d{4}__[a-z0-9\-]+__v\d{2}$")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _load_prompt_schema() -> dict:
    path = REPO_ROOT / "schemas" / "prompt_record.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_run_schema() -> dict:
    path = REPO_ROOT / "schemas" / "prompt_run.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_record(record: dict, schema: dict) -> list[str]:
    try:
        from jsonschema import Draft202012Validator

        errors = list(Draft202012Validator(schema).iter_errors(record))
        return [e.message for e in errors]
    except ImportError:
        return []  # skip if not installed


# ---------------------------------------------------------------------------
# MODEL_ALIAS_MAP structure tests
# ---------------------------------------------------------------------------


def test_model_alias_map_has_four_models() -> None:
    assert len(MODEL_ALIAS_MAP) == 4


def test_model_alias_map_required_keys() -> None:
    for model_key, entry in MODEL_ALIAS_MAP.items():
        assert "guide_file" in entry, f"{model_key} missing guide_file"
        assert "adapter" in entry, f"{model_key} missing adapter"
        assert "abbrev" in entry, f"{model_key} missing abbrev"
        assert "model_id" in entry, f"{model_key} missing model_id"


def test_model_alias_map_keys_are_kebab_case() -> None:
    for key in MODEL_ALIAS_MAP:
        assert "_" not in key, f"Key {key!r} should use kebab-case"


def test_model_alias_map_model_ids_are_snake_case() -> None:
    for key, entry in MODEL_ALIAS_MAP.items():
        model_id = entry["model_id"]
        assert "-" not in model_id, f"model_id {model_id!r} should use snake_case"


def test_resolve_model_key_kebab() -> None:
    assert resolve_model_key("midjourney") == "midjourney"
    assert resolve_model_key("chatgpt-image") == "chatgpt-image"
    assert resolve_model_key("nano-banana") == "nano-banana"
    assert resolve_model_key("kling-omni") == "kling-omni"


def test_resolve_model_key_snake() -> None:
    assert resolve_model_key("chatgpt_image") == "chatgpt-image"
    assert resolve_model_key("nano_banana") == "nano-banana"
    assert resolve_model_key("kling_omni") == "kling-omni"


def test_resolve_model_key_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown model"):
        resolve_model_key("flux")


# ---------------------------------------------------------------------------
# get_adapter factory tests
# ---------------------------------------------------------------------------


def test_get_adapter_midjourney(tmp_path: Path) -> None:
    adapter = get_adapter("midjourney", tmp_path)
    assert isinstance(adapter, MidjourneyAdapter)


def test_get_adapter_chatgpt_image(tmp_path: Path) -> None:
    adapter = get_adapter("chatgpt-image", tmp_path)
    assert isinstance(adapter, ChatGPTImageAdapter)


def test_get_adapter_nano_banana(tmp_path: Path) -> None:
    adapter = get_adapter("nano-banana", tmp_path)
    assert isinstance(adapter, NanaBananaAdapter)


def test_get_adapter_snake_case_alias(tmp_path: Path) -> None:
    adapter = get_adapter("chatgpt_image", tmp_path)
    assert isinstance(adapter, ChatGPTImageAdapter)


def test_get_adapter_kling_omni_raises_import_error(tmp_path: Path) -> None:
    with pytest.raises(ImportError, match="Batch 8"):
        get_adapter("kling-omni", tmp_path)


# ---------------------------------------------------------------------------
# BriefNotReadyError
# ---------------------------------------------------------------------------


def test_brief_not_ready_raises_on_generate(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    with pytest.raises(BriefNotReadyError):
        adapter.generate(UNREADY_BRIEF)


def test_brief_not_ready_raises_all_adapters(tmp_path: Path) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        with pytest.raises(BriefNotReadyError):
            adapter.generate(UNREADY_BRIEF)


# ---------------------------------------------------------------------------
# Midjourney adapter tests
# ---------------------------------------------------------------------------


def test_midjourney_prompt_id_format(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert PROMPT_ID_RE.match(record["prompt_id"]), record["prompt_id"]
    assert "midjourney" in record["prompt_id"]
    assert record["prompt_id"].startswith("SC0003__t2i-char-c01-")


def test_midjourney_lifecycle_stage_is_draft(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert record["lifecycle_stage"] == "draft"


def test_midjourney_target_models_single(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert record["target_models"] == ["midjourney"]


def test_midjourney_has_negative_prompt(tmp_path: Path) -> None:
    """Midjourney supports negative_prompt; field must be present."""
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "negative_prompt" in record
    assert isinstance(record["negative_prompt"], str)
    assert len(record["negative_prompt"]) > 0


def test_midjourney_prompt_text_word_count(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    words = record["prompt_text"].split()
    assert len(words) <= 80, f"Prompt text too long: {len(words)} words"


def test_midjourney_prompt_text_has_subject(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "Nadia Vale" in record["prompt_text"]


def test_midjourney_generation_params(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    params = record["generation_params"]
    assert params["adapter_name"] == "midjourney"
    assert params["model_guidance_ref"] == "docs/model_guides/midjourney.yaml"
    assert params["model_guidance_mode"] == "locked_guide"


def test_midjourney_prop_brief_includes_continuity_state(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(PROP_BRIEF)
    # Continuity state should appear in prompt_text
    assert "white plastic" in record["prompt_text"].lower()


def test_midjourney_schema_valid(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    schema = _load_prompt_schema()
    errors = _validate_record(record, schema)
    assert errors == [], f"Schema errors: {errors}"


def test_midjourney_run_record_structure(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path, model_guidance_mode="locked_guide")
    _, run_record = adapter.generate(CHAR_BRIEF, run_counter=1)
    assert run_record["model"] == "midjourney"
    assert run_record["status"] == "pending"
    assert run_record["outputs_expected"] == 4
    assert run_record["run_id"].startswith("RUN_SC0003_MJ_")
    assert "run_at" in run_record


def test_midjourney_run_record_schema_valid(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    _, run_record = adapter.generate(CHAR_BRIEF, run_counter=1, run_at="2026-04-30T12:00:00Z")
    schema = _load_run_schema()
    errors = _validate_record(run_record, schema)
    assert errors == [], f"Run schema errors: {errors}"


# ---------------------------------------------------------------------------
# ChatGPT Image adapter tests
# ---------------------------------------------------------------------------


def test_chatgpt_image_prompt_id_format(tmp_path: Path) -> None:
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert PROMPT_ID_RE.match(record["prompt_id"]), record["prompt_id"]
    assert "chatgpt-image" in record["prompt_id"]


def test_chatgpt_image_no_negative_prompt(tmp_path: Path) -> None:
    """ChatGPT Image must NOT have negative_prompt field."""
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "negative_prompt" not in record, (
        "ChatGPT Image record must not have negative_prompt"
    )


def test_chatgpt_image_constraint_strategy(tmp_path: Path) -> None:
    """generation_params must have constraint_strategy=embedded_positive_constraints."""
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    params = record["generation_params"]
    assert params.get("constraint_strategy") == "embedded_positive_constraints"


def test_chatgpt_image_prompt_text_is_natural_language(tmp_path: Path) -> None:
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    text = record["prompt_text"]
    # Should start with an instruction sentence
    assert text.startswith("Generate"), f"Unexpected prompt start: {text[:60]}"


def test_chatgpt_image_constraints_embedded_in_prompt(tmp_path: Path) -> None:
    """Negative constraints must be embedded in prompt_text for ChatGPT Image."""
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "Avoid" in record["prompt_text"] or "avoid" in record["prompt_text"]


def test_chatgpt_image_target_models(tmp_path: Path) -> None:
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert record["target_models"] == ["chatgpt_image"]


def test_chatgpt_image_schema_valid(tmp_path: Path) -> None:
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    schema = _load_prompt_schema()
    errors = _validate_record(record, schema)
    assert errors == [], f"Schema errors: {errors}"


def test_chatgpt_image_run_record_schema_valid(tmp_path: Path) -> None:
    adapter = ChatGPTImageAdapter(tmp_path)
    _, run_record = adapter.generate(CHAR_BRIEF, run_counter=1, run_at="2026-04-30T12:00:00Z")
    schema = _load_run_schema()
    errors = _validate_record(run_record, schema)
    assert errors == [], f"Run schema errors: {errors}"


# ---------------------------------------------------------------------------
# Nano Banana adapter tests
# ---------------------------------------------------------------------------


def test_nano_banana_prompt_id_format(tmp_path: Path) -> None:
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert PROMPT_ID_RE.match(record["prompt_id"]), record["prompt_id"]
    assert "nano-banana" in record["prompt_id"]


def test_nano_banana_has_negative_prompt(tmp_path: Path) -> None:
    """Nano Banana supports negative_prompt; field must be present."""
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "negative_prompt" in record
    assert isinstance(record["negative_prompt"], str)


def test_nano_banana_identity_framing_in_prompt(tmp_path: Path) -> None:
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "identity reference" in record["prompt_text"].lower() or \
           "Character identity" in record["prompt_text"]


def test_nano_banana_consistency_note_in_character_prompt(tmp_path: Path) -> None:
    """Character brief prompt should include consistency generation note."""
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert "consistent" in record["prompt_text"].lower()


def test_nano_banana_target_models(tmp_path: Path) -> None:
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    assert record["target_models"] == ["nano_banana"]


def test_nano_banana_schema_valid(tmp_path: Path) -> None:
    adapter = NanaBananaAdapter(tmp_path)
    record, _ = adapter.generate(CHAR_BRIEF)
    schema = _load_prompt_schema()
    errors = _validate_record(record, schema)
    assert errors == [], f"Schema errors: {errors}"


def test_nano_banana_run_record_schema_valid(tmp_path: Path) -> None:
    adapter = NanaBananaAdapter(tmp_path)
    _, run_record = adapter.generate(CHAR_BRIEF, run_counter=1, run_at="2026-04-30T12:00:00Z")
    schema = _load_run_schema()
    errors = _validate_record(run_record, schema)
    assert errors == [], f"Run schema errors: {errors}"


# ---------------------------------------------------------------------------
# Cross-adapter invariants
# ---------------------------------------------------------------------------


def test_all_adapters_lifecycle_stage_is_draft(tmp_path: Path) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(CHAR_BRIEF)
        assert record["lifecycle_stage"] == "draft", (
            f"{AdapterCls.__name__}: lifecycle_stage is not 'draft'"
        )


def test_all_adapters_canon_lock_false(tmp_path: Path) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(CHAR_BRIEF)
        assert record["canon_lock"] is False


def test_all_adapters_target_models_single_item(tmp_path: Path) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(CHAR_BRIEF)
        assert len(record["target_models"]) == 1, (
            f"{AdapterCls.__name__}: target_models must have exactly one entry"
        )


def test_all_adapters_prompt_id_matches_schema_pattern(tmp_path: Path) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(CHAR_BRIEF)
        assert PROMPT_ID_RE.match(record["prompt_id"]), (
            f"{AdapterCls.__name__}: prompt_id {record['prompt_id']!r} "
            "does not match ^SC\\d{{4}}__[a-z0-9\\-]+__v\\d{{2}}$"
        )


def test_all_adapters_source_refs_have_scene_card_and_excerpt(
    tmp_path: Path,
) -> None:
    for AdapterCls in (MidjourneyAdapter, ChatGPTImageAdapter, NanaBananaAdapter):
        adapter = AdapterCls(tmp_path)
        record, _ = adapter.generate(CHAR_BRIEF)
        refs = record["source_refs"]
        assert "scene_card" in refs and refs["scene_card"]
        assert "scene_excerpt" in refs and refs["scene_excerpt"]


def test_wardrobe_brief_prompt_type(tmp_path: Path) -> None:
    ward_brief = _make_brief(
        element_type="wardrobe",
        element_id="WD001",
        element_name="Nadia domestic control look",
    )
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(ward_brief)
    assert record["prompt_type"] == "t2i_wardrobe_element"


def test_style_brief_prompt_type(tmp_path: Path) -> None:
    adapter = MidjourneyAdapter(tmp_path)
    record, _ = adapter.generate(STYLE_BRIEF)
    assert record["prompt_type"] == "t2i_style_reference"


def test_location_brief_prompt_type(tmp_path: Path) -> None:
    loc_brief = _make_brief(
        element_type="location",
        element_id="LOC001",
        element_name="Vale Residence, Vardova",
    )
    adapter = ChatGPTImageAdapter(tmp_path)
    record, _ = adapter.generate(loc_brief)
    assert record["prompt_type"] == "t2i_location_element"
    assert "location_refs" in record["source_refs"]


# ---------------------------------------------------------------------------
# Model guidance snapshot propagation
# ---------------------------------------------------------------------------


def test_snapshot_propagates_to_generation_params(tmp_path: Path) -> None:
    snapshot_path = "evidence/model_guidance_snapshots/2026-04-30T120000Z_midjourney.yaml"
    adapter = MidjourneyAdapter(
        tmp_path,
        model_guidance_mode="dynamic_snapshot",
        model_guidance_snapshot=snapshot_path,
    )
    record, run_record = adapter.generate(CHAR_BRIEF, run_counter=1)
    assert record["generation_params"]["model_guidance_mode"] == "dynamic_snapshot"
    assert record["generation_params"]["model_guidance_snapshot"] == snapshot_path
    assert run_record["model_guidance_snapshot"] == snapshot_path


# ---------------------------------------------------------------------------
# prompt_run.schema.json validation
# ---------------------------------------------------------------------------


def test_prompt_run_schema_is_valid_json() -> None:
    path = REPO_ROOT / "schemas" / "prompt_run.schema.json"
    assert path.exists(), "prompt_run.schema.json not found"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("type") == "object"
    assert "run_id" in data["required"]
    assert "status" in data["required"]


def test_run_costs_csv_has_correct_header() -> None:
    csv_path = REPO_ROOT / "evidence" / "run_costs.csv"
    assert csv_path.exists(), "evidence/run_costs.csv not found"
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert "run_id" in header
    assert "model" in header
    assert "status" in header

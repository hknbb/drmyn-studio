import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_prompt_records


@pytest.fixture
def mock_repo(tmp_path):
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir(parents=True)
    schema_src = REPO_ROOT / "schemas" / "prompt_record.schema.json"
    
    if schema_src.exists():
        (schema_dir / "prompt_record.schema.json").write_text(
            schema_src.read_text(encoding="utf-8"), encoding="utf-8"
        )
    
    return tmp_path


def write_prompt(repo_root, stage, filename, payload):
    d = repo_root / "prompts" / stage
    d.mkdir(parents=True, exist_ok=True)
    with open(d / filename, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def get_valid_prompt():
    return {
        "prompt_id": "SC0001__t2i-char-midjourney__v01",
        "scene_id": "SC0001",
        "prompt_type": "t2i_character_element",
        "lifecycle_stage": "draft",
        "target_models": ["midjourney"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md"
        },
        "prompt_text": "A highly detailed portrait of Nadia...",
        "status": "active",
        "canon_lock": False
    }


def get_valid_kling_prompt():
    return {
        "prompt_id": "SC0001__omni-kling-alias-taxonomy__v01",
        "scene_id": "SC0001",
        "prompt_type": "omni_instruction",
        "lifecycle_stage": "draft",
        "target_models": ["kling_omni"],
        "source_refs": {
            "scene_card": "planning/scenes/SC0001/scene_card.yaml",
            "scene_excerpt": "planning/scenes/SC0001/scene_excerpt.md",
        },
        "prompt_text": (
            "Use @Nadia, bound in repo metadata to canonical repo alias "
            "@C01_HOME_MORNING."
        ),
        "generation_params": {
            "required_element_aliases": ["@Nadia"],
            "repo_canonical_aliases": ["@C01_HOME_MORNING"],
            "alias_resolution": {"@C01_HOME_MORNING": "@Nadia"},
            "attached_element_refs": [
                {
                    "element_id": "C01",
                    "element_type": "character_look",
                    "repo_alias": "@C01_HOME_MORNING",
                    "platform_alias": "@Nadia",
                    "platform_binding_required": True,
                    "readiness": "draft_reference_ready",
                }
            ],
            "not_attached_as_kling_elements": ["@ValeResidenceKitchenPassage"],
        },
        "status": "active",
        "canon_lock": False,
    }


def write_kling_character_look_element(repo_root, alias="@C01_HOME_MORNING"):
    d = repo_root / "visual_dev" / "elements" / "characters" / "C01" / "kling_elements"
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.x-draft",
        "record_type": "kling_character_look_element",
        "kling_character_look_element_id": "KLING_ELEM_C01_HOME_MORNING_V001",
        "character_id": "C01",
        "identity_anchor_id": "C01_IDENTITY_ANCHOR_V001",
        "look_id": "C01_LOOK_HOME_MORNING_V001",
        "kling_element_alias": alias,
        "display_name": "C01 Home Morning",
        "status": "draft",
        "element_role": "character_look_composite",
        "source_reference_chain": {
            "identity_source_ref": "MJ_ELEMENT_C01_HERO_LOCKED_V001",
            "front_hero_lock_ref": "external://local_manual/c01.png",
            "perspective_pack_id": "GPTIMG2_C01_PERSPECTIVE_PACK_V001",
            "wardrobe_ids": ["WD001"],
        },
        "omni_usage_policy": {
            "use_as_primary_character_element": True,
            "do_not_mix_with_other_same_character_look_aliases_in_same_shot": True,
            "wardrobe_is_baked_into_element": True,
            "separate_wardrobe_element_optional": False,
        },
        "provenance": {"created_by": "tests", "created_at": "2026-05-12T00:00:00Z"},
    }
    with open(d / "KLING_ELEM_C01_HOME_MORNING_V001.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)


def write_element_bindings(repo_root):
    d = repo_root / "visual_dev" / "omni_sets" / "SC0001"
    d.mkdir(parents=True, exist_ok=True)
    docs = [
        {
            "schema_version": "0.x-draft",
            "record_type": "element_binding",
            "element_id": "C01",
            "element_type": "character",
            "kling_alias": "@Nadia",
            "binding_status": "created",
        },
        {
            "schema_version": "0.x-draft",
            "record_type": "element_binding",
            "element_id": "LOC001",
            "element_type": "location_sub_area",
            "kling_alias": "@ValeResidenceKitchenPassage",
            "binding_status": "created",
        },
    ]
    with open(d / "element_bindings.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump_all(docs, f, sort_keys=False)


class DummyArgs:
    def __init__(self, repo_root, report_json):
        self.repo_root = repo_root
        self.report_json = report_json


def test_empty_directory_exits_0(mock_repo, capsys):
    args = DummyArgs(mock_repo, mock_repo / "report.json")
    assert validate_prompt_records.main(args) == 0
    assert "0 files validated" in capsys.readouterr().out


def test_valid_minimal_record_passes(mock_repo, capsys):
    write_prompt(mock_repo, "draft", "test_prompt.yaml", get_valid_prompt())
    args = DummyArgs(mock_repo, mock_repo / "report.json")
    assert validate_prompt_records.main(args) == 0
    assert "1 files validated successfully" in capsys.readouterr().out


def test_missing_prompt_text_fails(mock_repo):
    payload = get_valid_prompt()
    del payload["prompt_text"]
    write_prompt(mock_repo, "draft", "test_prompt.yaml", payload)
    args = DummyArgs(mock_repo, mock_repo / "report.json")
    assert validate_prompt_records.main(args) == 1
    
    report = json.loads((mock_repo / "report.json").read_text())
    assert report["files_with_errors"] == 1


def test_invalid_prompt_id_pattern_fails(mock_repo):
    payload = get_valid_prompt()
    payload["prompt_id"] = "INVALID_ID_FORMAT"
    write_prompt(mock_repo, "draft", "test_prompt.yaml", payload)
    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 1


def test_lifecycle_stage_production_fails(mock_repo):
    payload = get_valid_prompt()
    payload["lifecycle_stage"] = "production"
    write_prompt(mock_repo, "draft", "test_prompt.yaml", payload)
    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 1


def test_kling_required_platform_alias_resolves_through_element_bindings(mock_repo, capsys):
    write_kling_character_look_element(mock_repo)
    write_element_bindings(mock_repo)
    write_prompt(mock_repo, "draft", "kling_prompt.yaml", get_valid_kling_prompt())

    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 0
    assert "1 files validated successfully" in capsys.readouterr().out


def test_kling_unresolved_required_alias_fails(mock_repo):
    write_kling_character_look_element(mock_repo)
    write_element_bindings(mock_repo)
    payload = get_valid_kling_prompt()
    payload["generation_params"]["required_element_aliases"] = ["@MissingAlias"]
    write_prompt(mock_repo, "draft", "kling_prompt.yaml", payload)

    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 1
    report = json.loads((mock_repo / "report.json").read_text())
    errors = report["errors"]["prompts/draft/kling_prompt.yaml"]
    assert any("@MissingAlias" in error and "unresolved alias" in error for error in errors)


def test_kling_required_alias_conflicting_with_not_attached_fails(mock_repo):
    write_kling_character_look_element(mock_repo)
    write_element_bindings(mock_repo)
    payload = get_valid_kling_prompt()
    payload["generation_params"]["required_element_aliases"] = [
        "@Nadia",
        "@ValeResidenceKitchenPassage",
    ]
    write_prompt(mock_repo, "draft", "kling_prompt.yaml", payload)

    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 1
    report = json.loads((mock_repo / "report.json").read_text())
    errors = report["errors"]["prompts/draft/kling_prompt.yaml"]
    assert any("not_attached_as_kling_elements" in error for error in errors)


def test_kling_attached_repo_alias_must_resolve_to_character_look_record(mock_repo):
    write_element_bindings(mock_repo)
    payload = get_valid_kling_prompt()
    write_prompt(mock_repo, "draft", "kling_prompt.yaml", payload)

    assert validate_prompt_records.main(DummyArgs(mock_repo, mock_repo / "report.json")) == 1
    report = json.loads((mock_repo / "report.json").read_text())
    errors = report["errors"]["prompts/draft/kling_prompt.yaml"]
    assert any("repo_alias" in error and "@C01_HOME_MORNING" in error for error in errors)

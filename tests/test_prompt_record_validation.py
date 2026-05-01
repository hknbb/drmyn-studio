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
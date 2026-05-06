from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tools.copilot_dashboard import asset_intake_panel  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _minimal_slot(
    *,
    element_id: str = "C01",
    group_id: str = "wd001",
    element_type: str = "character",
    source_status: str = "not_collected",
    storage_policy: str = "no_binary_commits",
    copyright_review: str = "pending",
    provenance_review: str = "pending",
    intake_ready_to_proceed: bool = False,
    required_views: list[str] | None = None,
    canonical_assets_committed: list[str] | None = None,
) -> dict:
    return {
        "scene_id": "SC0001",
        "work_order_id": "SC0001_ASSET_01_C01",
        "element_id": element_id,
        "element_type": element_type,
        "group_id": group_id,
        "group_type": "wardrobe_reference_set",
        "context": "test context",
        "required_views": required_views or ["front_reference", "three_quarter_reference"],
        "source_status": source_status,
        "copyright_review": copyright_review,
        "provenance_review": provenance_review,
        "intake_ready_to_proceed": intake_ready_to_proceed,
        "canonical_assets_committed": canonical_assets_committed or [],
        "storage_policy": storage_policy,
        "forbidden_actions": [],
    }


# ---------------------------------------------------------------------------
# No-file-write contract
# ---------------------------------------------------------------------------

def test_loader_writes_no_files_when_no_records(tmp_path: Path) -> None:
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    asset_intake_panel.load_intake_slot_rows(tmp_path)
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert after == before


def test_loader_writes_no_files_with_records(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))

    asset_intake_panel.load_intake_slot_rows(tmp_path)

    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert after == before


# ---------------------------------------------------------------------------
# First intake slot classification
# ---------------------------------------------------------------------------

def test_wd001_is_first_intake_slot(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot(element_id="C01", group_id="wd001"))

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert len(rows) == 1
    assert rows[0]["is_first_intake_slot"] is True


def test_non_wd001_slot_is_not_first_intake(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD002/intake_slot.yaml"
    _write_yaml(
        slot_path,
        _minimal_slot(element_id="C01", group_id="wd002"),
    )

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert len(rows) == 1
    assert rows[0]["is_first_intake_slot"] is False


def test_different_element_is_not_first_intake(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/locations/LOC001/sub_areas/jins_room/intake_slot.yaml"
    _write_yaml(
        slot_path,
        _minimal_slot(element_id="LOC001", group_id="jins_room", element_type="location"),
    )

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert len(rows) == 1
    assert rows[0]["is_first_intake_slot"] is False


# ---------------------------------------------------------------------------
# Missing views computation
# ---------------------------------------------------------------------------

def test_missing_views_all_empty_committed(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(
        slot_path,
        _minimal_slot(
            required_views=["front_reference", "three_quarter_reference", "context_reference"],
            canonical_assets_committed=[],
        ),
    )

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert rows[0]["missing_views"] != "—"
    assert "front_reference" in rows[0]["missing_views"]


def test_committed_count_matches_list_length(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(
        slot_path,
        _minimal_slot(canonical_assets_committed=["a.jpg", "b.jpg"]),
    )

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert rows[0]["committed_count"] == 2


# ---------------------------------------------------------------------------
# Intake slot values are not mutated
# ---------------------------------------------------------------------------

def test_loader_does_not_mutate_intake_slot_values(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    original = _minimal_slot(
        source_status="not_collected",
        storage_policy="no_binary_commits",
        copyright_review="pending",
        provenance_review="pending",
        intake_ready_to_proceed=False,
    )
    _write_yaml(slot_path, original)

    asset_intake_panel.load_intake_slot_rows(tmp_path)

    reloaded = yaml.safe_load(slot_path.read_text(encoding="utf-8"))
    assert reloaded["source_status"] == "not_collected"
    assert reloaded["storage_policy"] == "no_binary_commits"
    assert reloaded["copyright_review"] == "pending"
    assert reloaded["provenance_review"] == "pending"
    assert reloaded["intake_ready_to_proceed"] is False
    assert reloaded["canonical_assets_committed"] == []


# ---------------------------------------------------------------------------
# Multiple slots
# ---------------------------------------------------------------------------

def test_multiple_slots_returned(tmp_path: Path) -> None:
    slots = [
        (
            tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml",
            _minimal_slot(element_id="C01", group_id="wd001"),
        ),
        (
            tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD002/intake_slot.yaml",
            _minimal_slot(element_id="C01", group_id="wd002"),
        ),
        (
            tmp_path / "visual_dev/elements/locations/LOC001/sub_areas/jins_room/intake_slot.yaml",
            _minimal_slot(element_id="LOC001", group_id="jins_room", element_type="location"),
        ),
    ]
    for path, payload in slots:
        _write_yaml(path, payload)

    rows = asset_intake_panel.load_intake_slot_rows(tmp_path)

    assert len(rows) == 3
    first_slots = [r for r in rows if r["is_first_intake_slot"]]
    other_slots = [r for r in rows if not r["is_first_intake_slot"]]
    assert len(first_slots) == 1
    assert len(other_slots) == 2


# ---------------------------------------------------------------------------
# No image or video binary produced
# ---------------------------------------------------------------------------

def test_no_image_or_video_files_created(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())

    asset_intake_panel.load_intake_slot_rows(tmp_path)

    all_files = list(tmp_path.rglob("*"))
    binary_extensions = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mkv", ".wav"}
    binaries = [f for f in all_files if f.suffix.lower() in binary_extensions]
    assert binaries == []

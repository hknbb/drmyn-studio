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
# No image or video binary produced (loader)
# ---------------------------------------------------------------------------

def test_no_image_or_video_files_created(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())

    asset_intake_panel.load_intake_slot_rows(tmp_path)

    all_files = list(tmp_path.rglob("*"))
    binary_extensions = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".mkv", ".wav"}
    binaries = [f for f in all_files if f.suffix.lower() in binary_extensions]
    assert binaries == []


# ---------------------------------------------------------------------------
# B8-6B: stage_uploaded_file — correct staging directory
# ---------------------------------------------------------------------------

def test_stage_writes_to_staging_dir(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"\xff\xd8\xff", "photo.jpg", "front_reference"
    )
    assert result.success
    staged = tmp_path / "visual_dev/intake_staging/C01_WD001/photo.jpg"
    assert staged.exists()
    assert staged.read_bytes() == b"\xff\xd8\xff"


def test_stage_writes_sidecar_yaml(tmp_path: Path) -> None:
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "ref.jpg", "back_reference", "test note"
    )
    sidecar = tmp_path / "visual_dev/intake_staging/C01_WD001/ref.jpg.sidecar.yaml"
    assert sidecar.exists()
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    assert data["element_id"] == "C01"
    assert data["group_id"] == "WD001"
    assert data["view_role"] == "back_reference"
    assert data["original_filename"] == "ref.jpg"
    assert data["source_type"] == "human_uploaded_reference"
    assert data["copyright_review"] == "pending"
    assert data["provenance_review"] == "pending"
    assert data["operator_note"] == "test note"
    assert "intake_ready_to_proceed" not in data
    assert "storage_policy" not in data
    assert "canonical_assets_committed" not in data


def test_stage_sidecar_staged_path_is_relative(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "ref.png", "front_reference"
    )
    assert result.success
    assert not result.staged_path.startswith("/")
    assert result.staged_path.startswith("visual_dev/intake_staging/")


# ---------------------------------------------------------------------------
# B8-6B: rejected extension
# ---------------------------------------------------------------------------

def test_stage_rejects_non_image_extension(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "script.py", "front_reference"
    )
    assert not result.success
    assert "Rejected" in result.message


def test_stage_rejects_video_extension(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "clip.mp4", "front_reference"
    )
    assert not result.success


def test_stage_rejects_yaml_extension(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "config.yaml", "front_reference"
    )
    assert not result.success


# ---------------------------------------------------------------------------
# B8-6B: filename sanitization
# ---------------------------------------------------------------------------

def test_stage_sanitizes_spaces_in_filename(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "my photo.jpg", "front_reference"
    )
    assert result.success
    assert " " not in result.staged_path
    staged = tmp_path / "visual_dev/intake_staging/C01_WD001/my_photo.jpg"
    assert staged.exists()


def test_stage_strips_path_traversal(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "../evil.jpg", "front_reference"
    )
    assert result.success
    assert ".." not in result.staged_path
    staged = tmp_path / "visual_dev/intake_staging/C01_WD001/evil.jpg"
    assert staged.exists()


def test_stage_lowercases_filename(tmp_path: Path) -> None:
    result = asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "MyPhoto.JPG", "front_reference"
    )
    assert result.success
    filename = Path(result.staged_path).name
    assert filename == filename.lower()
    assert filename == "myphoto.jpg"


# ---------------------------------------------------------------------------
# B8-6B: canonical and intake_slot isolation
# ---------------------------------------------------------------------------

def test_stage_does_not_write_to_elements_dir(tmp_path: Path) -> None:
    elements_dir = tmp_path / "visual_dev/elements"
    elements_dir.mkdir(parents=True)

    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "photo.jpg", "front_reference"
    )

    assert list(elements_dir.rglob("*")) == []


def test_stage_does_not_mutate_intake_slot(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    original = _minimal_slot()
    _write_yaml(slot_path, original)

    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "photo.jpg", "front_reference"
    )

    reloaded = yaml.safe_load(slot_path.read_text(encoding="utf-8"))
    assert reloaded == original


def test_stage_lifecycle_fields_remain_pending(tmp_path: Path) -> None:
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "ref.png", "context_reference"
    )
    sidecar = tmp_path / "visual_dev/intake_staging/C01_WD001/ref.png.sidecar.yaml"
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    assert data["copyright_review"] == "pending"
    assert data["provenance_review"] == "pending"


# ---------------------------------------------------------------------------
# B8-6C: placement preview panel data
# ---------------------------------------------------------------------------

def test_preview_loader_writes_no_files(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "front.jpg", "front_reference"
    )
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))

    asset_intake_panel.load_placement_preview(tmp_path)

    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert after == before


def test_preview_reports_target_canonical_path_and_missing_after_preview(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "front shot.JPG", "front_reference"
    )

    preview = asset_intake_panel.load_placement_preview(tmp_path)

    assert preview["slot_path"] == asset_intake_panel.FIRST_INTAKE_SLOT_REF
    assert preview["missing_views_now"] == [
        "front_reference",
        "three_quarter_reference",
    ]
    assert preview["missing_views_after_preview"] == ["three_quarter_reference"]
    assert preview["rows"][0]["target_canonical_path"] == (
        "visual_dev/elements/characters/C01/wardrobe/WD001/c01_wd001_front.jpg"
    )


def test_preview_warns_on_duplicate_target_paths(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"one", "front_a.jpg", "front_reference"
    )
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"two", "front_b.jpg", "front_reference"
    )

    preview = asset_intake_panel.load_placement_preview(tmp_path)

    assert preview["duplicate_targets"] == [
        "visual_dev/elements/characters/C01/wardrobe/WD001/c01_wd001_front.jpg"
    ]
    assert all("Duplicate preview target path." in row["warning"] for row in preview["rows"])


def test_preview_warns_on_unsafe_sidecar_target_scope(tmp_path: Path) -> None:
    slot_path = tmp_path / "visual_dev/elements/characters/C01/wardrobe/WD001/intake_slot.yaml"
    _write_yaml(slot_path, _minimal_slot())
    asset_intake_panel.stage_uploaded_file(
        tmp_path, b"data", "front.jpg", "front_reference"
    )
    sidecar = tmp_path / "visual_dev/intake_staging/C01_WD001/front.jpg.sidecar.yaml"
    payload = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    payload["target_slot_ref"] = "visual_dev/elements/characters/C01/wardrobe/WD002/intake_slot.yaml"
    _write_yaml(sidecar, payload)

    preview = asset_intake_panel.load_placement_preview(tmp_path)

    assert "Unsafe target slot ref outside approved B8A scope." in preview["rows"][0]["warning"]
    assert any("Unsafe target slot ref outside approved B8A scope." in warning for warning in preview["rows"][0]["warning"].split(" | "))

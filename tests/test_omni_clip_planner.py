"""
Tests for scripts/agents/omni_clip_planner.py.

Covers:
- short_insert merge directions (backward / forward)
- clip duration hard constraint (<= 15s)
- shot duration valid integer enum (3..15)
- dialogue-heavy clips → metadata_only continuity mode
- determinism: same input produces identical output
- every shot has duration_reason
- packer_version recorded in omni_clip_plan
- SC0001 integration: all beats covered, no dialogue line split, schema validation
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from scripts.agents.omni_clip_planner import (
    PACKER_VERSION,
    VALID_SHOT_DURATIONS,
    MAX_CLIP_DURATION,
    MIN_SHOT_DURATION,
    _beat_duration,
    _resolve_shots,
    _pack_clips,
    plan_omni_clips,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_beat(
    beat_id: str,
    hint: str = "normal",
    role: str = "action",
    may_merge: bool = True,
    splittable: bool = False,
    content: str = "Placeholder content.",
) -> dict:
    return {
        "beat_id": beat_id,
        "content": content,
        "semantic_duration_hint": hint,
        "narrative_role": role,
        "may_merge_with_next": may_merge,
        "splittable": splittable,
    }


def _all_shot_beat_ids(clips: list[dict]) -> list[list[str]]:
    """Return flat list of source_beat_ids lists for every shot in every clip."""
    result = []
    for clip in clips:
        for shot in clip["shots"]:
            result.append(shot["source_beat_ids"])
    return result


def _all_shots(clips: list[dict]) -> list[dict]:
    return [shot for clip in clips for shot in clip["shots"]]


# ---------------------------------------------------------------------------
# Unit: _beat_duration
# ---------------------------------------------------------------------------

def test_normal_action_beat_5s():
    beat = _make_beat("B", hint="normal", role="action")
    assert _beat_duration(beat, []) == 5


def test_normal_hold_beat_6s():
    beat = _make_beat("B", hint="normal", role="hold")
    assert _beat_duration(beat, []) == 6


def test_normal_transition_beat_4s():
    beat = _make_beat("B", hint="normal", role="transition")
    assert _beat_duration(beat, []) == 4


def test_long_hold_beat_duration():
    beat = _make_beat("B", hint="long_hold", role="hold")
    # long_hold base (10) + hold role delta (1) = 11
    assert _beat_duration(beat, []) == 11


def test_short_insert_beat_2s():
    beat = _make_beat("B", hint="short_insert", role="insert")
    assert _beat_duration(beat, []) == 2


def test_dialogue_beat_uses_word_count():
    beat = _make_beat("B", hint="normal", role="dialogue")
    lines = [{"line_id": "L1", "line_text": "Hello there."}]  # 2 words
    dur = _beat_duration(beat, lines)
    assert dur in VALID_SHOT_DURATIONS


def test_dialogue_beat_no_lines_fallback():
    # No lines → falls through to base+delta path (normal base=5, dialogue delta=0)
    beat = _make_beat("B", hint="normal", role="dialogue")
    assert _beat_duration(beat, []) == 5


# ---------------------------------------------------------------------------
# Unit: _resolve_shots — short_insert merge direction
# ---------------------------------------------------------------------------

def test_short_insert_merges_backward_when_may_merge_true():
    """Insert following a may_merge_with_next=true beat merges backward."""
    beats = [
        _make_beat("BEAT_A", hint="normal", role="action", may_merge=True),
        _make_beat("BEAT_INS", hint="short_insert", role="insert"),
        _make_beat("BEAT_B", hint="normal", role="action"),
    ]
    shots = _resolve_shots(beats, {})
    # BEAT_A should absorb BEAT_INS; BEAT_B should be a separate shot
    assert len(shots) == 2
    assert "BEAT_A" in shots[0].beat_ids
    assert "BEAT_INS" in shots[0].beat_ids
    assert shots[1].beat_ids == ["BEAT_B"]


def test_short_insert_merges_forward_when_prev_forbids():
    """Insert after may_merge_with_next=false beat merges forward into next beat."""
    beats = [
        _make_beat("BEAT_A", hint="normal", role="action", may_merge=False),
        _make_beat("BEAT_INS", hint="short_insert", role="insert"),
        _make_beat("BEAT_B", hint="normal", role="action"),
    ]
    shots = _resolve_shots(beats, {})
    # BEAT_A stays alone; BEAT_INS merges into BEAT_B
    assert len(shots) == 2
    assert shots[0].beat_ids == ["BEAT_A"]
    assert "BEAT_INS" in shots[1].beat_ids
    assert "BEAT_B" in shots[1].beat_ids


def test_consecutive_inserts_all_merge_backward():
    """Multiple consecutive inserts all merge backward into preceding beat."""
    beats = [
        _make_beat("ANCHOR", hint="normal", role="hold", may_merge=True),
        _make_beat("INS_1", hint="short_insert", role="insert"),
        _make_beat("INS_2", hint="short_insert", role="pulse_check"),
        _make_beat("INS_3", hint="short_insert", role="insert"),
        _make_beat("NEXT", hint="normal", role="action"),
    ]
    shots = _resolve_shots(beats, {})
    assert len(shots) == 2
    merged = shots[0]
    assert "ANCHOR" in merged.beat_ids
    assert "INS_1" in merged.beat_ids
    assert "INS_2" in merged.beat_ids
    assert "INS_3" in merged.beat_ids


def test_trailing_inserts_merge_backward_into_last_shot():
    """Inserts at end of beat list (no following regular beat) merge backward."""
    beats = [
        _make_beat("MAIN", hint="normal", role="hold", may_merge=True),
        _make_beat("TRAIL_INS", hint="short_insert", role="insert"),
    ]
    shots = _resolve_shots(beats, {})
    assert len(shots) == 1
    assert "MAIN" in shots[0].beat_ids
    assert "TRAIL_INS" in shots[0].beat_ids


def test_merge_caps_duration_at_max():
    """Merging inserts never pushes shot duration above MAX_CLIP_DURATION."""
    # Create a beat that already has maximum duration
    beats = [
        _make_beat("LONG", hint="long_hold", role="hold", may_merge=True),
        _make_beat("INS_1", hint="short_insert", role="insert"),
        _make_beat("INS_2", hint="short_insert", role="insert"),
        _make_beat("INS_3", hint="short_insert", role="insert"),
        _make_beat("INS_4", hint="short_insert", role="insert"),
        _make_beat("INS_5", hint="short_insert", role="insert"),
    ]
    shots = _resolve_shots(beats, {})
    assert len(shots) == 1
    assert shots[0].duration <= MAX_CLIP_DURATION


def test_all_shots_have_valid_duration():
    beats = [
        _make_beat(f"B{i}", hint="normal", role="action")
        for i in range(5)
    ]
    shots = _resolve_shots(beats, {})
    for s in shots:
        assert s.duration in VALID_SHOT_DURATIONS, (
            f"Shot {s.beat_ids} has invalid duration {s.duration}"
        )


def test_all_shots_have_duration_reason():
    beats = [_make_beat("B", hint="normal", role="action")]
    shots = _resolve_shots(beats, {})
    for s in shots:
        assert s.duration_reason, "duration_reason must not be empty"


def test_dialogue_line_ids_on_shot():
    beats = [_make_beat("DLGBEAT", hint="normal", role="dialogue")]
    dmap = {
        "DLGBEAT": [
            {"line_id": "L1", "line_text": "Hello.", "target_beat_id": "DLGBEAT"},
            {"line_id": "L2", "line_text": "Goodbye.", "target_beat_id": "DLGBEAT"},
        ]
    }
    shots = _resolve_shots(beats, dmap)
    assert shots[0].line_ids == ["L1", "L2"]


# ---------------------------------------------------------------------------
# Unit: _pack_clips
# ---------------------------------------------------------------------------

def _make_shots_from_beats(beats: list[dict]) -> list:
    from scripts.agents.omni_clip_planner import _resolve_shots
    return _resolve_shots(beats, {})


def test_single_clip_for_short_beats():
    """Four 3s shots fit in one 12s clip."""
    beats = [_make_beat(f"B{i}", hint="normal", role="action") for i in range(3)]
    # Override: manually force 3s each by using transition role
    # (transition: 5 - 1 = 4s, still fits 3x4=12s in one clip)
    shots = _make_shots_from_beats(beats)
    clips = _pack_clips(shots, "SC9999")
    assert len(clips) == 1
    assert clips[0]["total_duration"] <= MAX_CLIP_DURATION


def test_no_clip_exceeds_max_duration():
    """Eight 5s shots (40s total) must split into multiple clips all <= 15s."""
    beats = [_make_beat(f"B{i}", hint="normal", role="action") for i in range(8)]
    shots = _make_shots_from_beats(beats)
    clips = _pack_clips(shots, "SC9999")
    for clip in clips:
        assert clip["total_duration"] <= MAX_CLIP_DURATION, (
            f"Clip {clip['clip_id']} has total_duration={clip['total_duration']} > {MAX_CLIP_DURATION}"
        )


def test_clip_ids_sequential():
    beats = [_make_beat(f"B{i}", hint="normal", role="action") for i in range(4)]
    shots = _make_shots_from_beats(beats)
    clips = _pack_clips(shots, "SC9999")
    for idx, clip in enumerate(clips):
        expected_id = f"CLIP_SC9999_{idx + 1:02d}"
        assert clip["clip_id"] == expected_id


def test_shot_ids_use_letters():
    beats = [
        _make_beat("B1", hint="normal", role="action"),
        _make_beat("B2", hint="normal", role="action"),
        _make_beat("B3", hint="normal", role="action"),
    ]
    shots = _make_shots_from_beats(beats)
    clips = _pack_clips(shots, "SC9999")
    # All shots in first clip should have letters A, B, C
    for clip in clips:
        for si, shot in enumerate(clip["shots"]):
            import string
            letter = string.ascii_uppercase[si]
            assert shot["shot_id"].endswith(f"_{letter}")


def test_dialogue_heavy_clip_is_metadata_only():
    """Clip where >50% shots are dialogue → is_dialogue_heavy=True."""
    beats = [
        _make_beat("D1", hint="normal", role="dialogue"),
        _make_beat("D2", hint="normal", role="dialogue"),
        _make_beat("A1", hint="normal", role="action"),
    ]
    dmap = {
        "D1": [{"line_id": "L1", "line_text": "Line one.", "target_beat_id": "D1"}],
        "D2": [{"line_id": "L2", "line_text": "Line two.", "target_beat_id": "D2"}],
    }
    shots = _resolve_shots(beats, dmap)
    clips = _pack_clips(shots, "SC9999")
    # D1 + D2 = 2 dialogue shots, A1 = 1 action → heavy
    assert any(c["is_dialogue_heavy"] for c in clips)


def test_total_duration_equals_sum_of_shots():
    """For each clip, total_duration == sum of shot durations."""
    beats = [_make_beat(f"B{i}", hint="normal", role="action") for i in range(5)]
    shots = _make_shots_from_beats(beats)
    clips = _pack_clips(shots, "SC9999")
    for clip in clips:
        expected = sum(s["duration_seconds"] for s in clip["shots"])
        assert clip["total_duration"] == expected


# ---------------------------------------------------------------------------
# Unit: determinism
# ---------------------------------------------------------------------------

def test_deterministic_same_input_twice():
    """Running the packer twice on identical beats produces identical output."""
    beats = [
        _make_beat("B1", hint="normal", role="action"),
        _make_beat("INS", hint="short_insert", role="insert"),
        _make_beat("B2", hint="normal", role="transition"),
        _make_beat("B3", hint="long_hold", role="hold", splittable=True),
        _make_beat("B4", hint="short_insert", role="insert"),
    ]
    dmap: dict = {}

    shots_a = _resolve_shots(copy.deepcopy(beats), dmap)
    shots_b = _resolve_shots(copy.deepcopy(beats), dmap)

    assert len(shots_a) == len(shots_b)
    for sa, sb in zip(shots_a, shots_b):
        assert sa.beat_ids == sb.beat_ids
        assert sa.duration == sb.duration


# ---------------------------------------------------------------------------
# Integration: SC0001
# ---------------------------------------------------------------------------

SC0001_BEAT_PLAN_REF = "planning/scenes/SC0001/scene_beat_plan.yaml"
SC0001_DIALOGUE_REF = "planning/scenes/SC0001/dialogue_beats.yaml"

SC0001_ALL_BEAT_IDS = [
    "ESTABLISH_KITCHEN",
    "NADIA_PASSAGE_MOVEMENT",
    "WATER_GLASS_ACTION",
    "WRIST_SCAR_INSERT",
    "CABINET_INVENTORY",
    "CORRIDOR_TRANSITION",
    "BIRTA_ENTRANCE",
    "DIALOGUE_SLEEP_ACCUSATION",
    "DIALOGUE_FORMULA_VITAMIN",
    "DIALOGUE_MR_VALE_CALL",
    "NADIA_PRIOR_KNOWLEDGE",
    "BIRTA_COVERED_LINENS",
    "NADIA_BIRTA_PASSING",
    "OFF_ANGLE_DISCOVERY",
    "FRAME_STRAIGHTENING",
    "DUST_SHADOW_EVIDENCE",
    "WRIST_PULSE_CHECK",
    "MOVEMENT_TO_JINS_ROOM",
    "JINS_ROOM_ESTABLISH",
    "NADIA_JIN_OBSERVATION",
    "DOOR_CLOSING_EXIT",
]

SC0001_ALL_LINE_IDS = [
    "DLG_BIRTA_SLEEP_01",
    "DLG_NADIA_SLEEP_01",
    "DLG_BIRTA_SLEEP_02",
    "DLG_NADIA_FORMULA_01",
    "DLG_BIRTA_FORMULA_01",
    "DLG_BIRTA_MR_VALE_01",
    "DLG_NADIA_PRIOR_01",
    "DLG_BIRTA_COVERED_01",
]


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="module")
def sc0001_result(repo_root):
    plan, manifests = plan_omni_clips(
        scene_id="SC0001",
        beat_plan_ref=SC0001_BEAT_PLAN_REF,
        dialogue_beats_ref=SC0001_DIALOGUE_REF,
        repo_root=repo_root,
        created_by="test_suite",
        created_at="2026-05-08T22:00:00Z",
    )
    return plan, manifests


def test_sc0001_returns_nonempty_clips(sc0001_result):
    _, manifests = sc0001_result
    assert len(manifests) > 0, "Expected at least one clip from SC0001"


def test_sc0001_all_clips_le_15s(sc0001_result):
    _, manifests = sc0001_result
    for m in manifests:
        total = m["total_duration_seconds"]
        assert total <= MAX_CLIP_DURATION, (
            f"{m['clip_id']} total_duration_seconds={total} exceeds {MAX_CLIP_DURATION}"
        )


def test_sc0001_all_shot_durations_valid(sc0001_result):
    _, manifests = sc0001_result
    for m in manifests:
        for shot in m["shots"]:
            d = shot["duration_seconds"]
            assert d in VALID_SHOT_DURATIONS, (
                f"{m['clip_id']} shot {shot['shot_id']} has invalid duration {d}"
            )


def test_sc0001_every_shot_has_duration_reason(sc0001_result):
    _, manifests = sc0001_result
    for m in manifests:
        for shot in m["shots"]:
            assert shot.get("duration_reason"), (
                f"{m['clip_id']} shot {shot['shot_id']} missing duration_reason"
            )


def test_sc0001_total_duration_matches_sum_of_shots(sc0001_result):
    _, manifests = sc0001_result
    for m in manifests:
        expected = sum(s["duration_seconds"] for s in m["shots"])
        assert m["total_duration_seconds"] == expected, (
            f"{m['clip_id']}: total={m['total_duration_seconds']} != sum(shots)={expected}"
        )


def test_sc0001_all_beats_covered_exactly_once(sc0001_result):
    """Every SC0001 source beat appears in exactly one shot across all clips."""
    _, manifests = sc0001_result
    beat_clip_map: dict[str, list[str]] = {}
    for m in manifests:
        for shot in m["shots"]:
            for bid in shot["source_beat_ids"]:
                beat_clip_map.setdefault(bid, []).append(m["clip_id"])

    for bid in SC0001_ALL_BEAT_IDS:
        clips_containing = beat_clip_map.get(bid, [])
        assert len(clips_containing) == 1, (
            f"Beat {bid!r} appears in {len(clips_containing)} clips: {clips_containing}"
        )


def test_sc0001_wrist_scar_insert_not_standalone(sc0001_result):
    """WRIST_SCAR_INSERT must be merged into another beat's shot, never standalone."""
    _, manifests = sc0001_result
    for m in manifests:
        for shot in m["shots"]:
            if "WRIST_SCAR_INSERT" in shot["source_beat_ids"]:
                assert len(shot["source_beat_ids"]) > 1, (
                    "WRIST_SCAR_INSERT appears as a standalone shot; must be merged"
                )


def test_sc0001_all_dialogue_lines_covered(sc0001_result):
    """Every SC0001 dialogue line appears in at least one shot."""
    _, manifests = sc0001_result
    found_lines: set[str] = set()
    for m in manifests:
        for shot in m["shots"]:
            for lid in shot.get("dialogue_line_ids", []):
                found_lines.add(lid)

    for lid in SC0001_ALL_LINE_IDS:
        assert lid in found_lines, f"Dialogue line {lid!r} not found in any shot"


def test_sc0001_no_dialogue_line_in_multiple_clips(sc0001_result):
    """No dialogue line_id must appear in more than one clip (cross-clip deduplication)."""
    _, manifests = sc0001_result
    line_to_clips: dict[str, list[str]] = {}
    for m in manifests:
        for shot in m["shots"]:
            for lid in shot.get("dialogue_line_ids", []):
                line_to_clips.setdefault(lid, []).append(m["clip_id"])

    for lid, clips in line_to_clips.items():
        assert len(clips) == 1, (
            f"Dialogue line {lid!r} appears in {len(clips)} clips: {clips}"
        )


def test_sc0001_packer_version_in_plan(sc0001_result):
    plan, _ = sc0001_result
    assert plan["packing_strategy"]["packer_version"] == PACKER_VERSION


def test_sc0001_plan_record_type(sc0001_result):
    plan, _ = sc0001_result
    assert plan["record_type"] == "omni_clip_plan"


def test_sc0001_manifest_record_type(sc0001_result):
    _, manifests = sc0001_result
    for m in manifests:
        assert m["record_type"] == "omni_clip_manifest"


def test_sc0001_kling_native_audio_const_fields(sc0001_result):
    """All manifests must have external_tts_allowed=False and adr_vendor_allowed=False."""
    _, manifests = sc0001_result
    for m in manifests:
        kna = m["kling_native_audio"]
        assert kna["external_tts_allowed"] is False
        assert kna["adr_vendor_allowed"] is False
        assert kna["provider_policy"] == "kling_native_only"


def test_sc0001_dialogue_heavy_clips_are_metadata_only(sc0001_result):
    """Clips where >50% of shots are dialogue beats must have metadata_only continuity."""
    _, manifests = sc0001_result
    for m in manifests:
        shots = m["shots"]
        # Count dialogue shots by checking if they have dialogue_line_ids
        dlg_count = sum(1 for s in shots if s.get("dialogue_line_ids"))
        is_heavy = dlg_count * 2 > len(shots)
        if is_heavy:
            assert m["continuity_input_mode"] == "metadata_only", (
                f"{m['clip_id']} is dialogue-heavy but continuity_input_mode="
                f"{m['continuity_input_mode']!r}"
            )


def test_sc0001_manifests_validate_against_schema(sc0001_result, repo_root):
    """All generated manifests must pass JSON Schema validation."""
    schema_path = repo_root / "schemas" / "omni_clip_manifest.schema.json"
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft202012Validator(schema)

    _, manifests = sc0001_result
    for m in manifests:
        errors = list(validator.iter_errors(m))
        assert not errors, (
            f"{m['clip_id']} failed schema validation: "
            + "; ".join(str(e.message) for e in errors)
        )


def test_sc0001_plan_validates_against_schema(sc0001_result, repo_root):
    """Generated omni_clip_plan must pass JSON Schema validation."""
    schema_path = repo_root / "schemas" / "omni_clip_plan.schema.json"
    with open(schema_path, "r", encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft202012Validator(schema)

    plan, _ = sc0001_result
    errors = list(validator.iter_errors(plan))
    assert not errors, (
        "omni_clip_plan failed schema validation: "
        + "; ".join(str(e.message) for e in errors)
    )


def test_sc0001_deterministic(repo_root):
    """Running plan_omni_clips twice on SC0001 produces identical results."""
    kwargs = dict(
        scene_id="SC0001",
        beat_plan_ref=SC0001_BEAT_PLAN_REF,
        dialogue_beats_ref=SC0001_DIALOGUE_REF,
        repo_root=repo_root,
        created_by="det_test",
        created_at="2026-05-08T00:00:00Z",
    )
    plan1, mfst1 = plan_omni_clips(**kwargs)
    plan2, mfst2 = plan_omni_clips(**kwargs)

    assert len(mfst1) == len(mfst2)
    for m1, m2 in zip(mfst1, mfst2):
        assert m1["clip_id"] == m2["clip_id"]
        assert m1["total_duration_seconds"] == m2["total_duration_seconds"]
        assert len(m1["shots"]) == len(m2["shots"])
        for s1, s2 in zip(m1["shots"], m2["shots"]):
            assert s1["shot_id"] == s2["shot_id"]
            assert s1["source_beat_ids"] == s2["source_beat_ids"]
            assert s1["duration_seconds"] == s2["duration_seconds"]

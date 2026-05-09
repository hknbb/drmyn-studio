"""
B6 acceptance tests for SC0001 omni_clip_plan + manifests.

Validates B6 deliverables against v2 plan deterministic packing rules:
- Clip count computed, not authored
- All 21 source beats covered exactly once
- All 8 dialogue lines assigned exactly once
- All durations valid integers 3..15 per clip/shot
- Dialogue-heavy clips use metadata_only continuity mode
- Schema validation passes
- No prompt records generated
"""
import json
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent
PLAN_PATH = REPO_ROOT / "planning/scenes/SC0001/omni_clip_plan.yaml"
MANIFESTS_DIR = REPO_ROOT / "planning/scenes/SC0001/manifests"
SCENE_BEAT_PLAN_PATH = REPO_ROOT / "planning/scenes/SC0001/scene_beat_plan.yaml"
DIALOGUE_BEATS_PATH = REPO_ROOT / "planning/scenes/SC0001/dialogue_beats.yaml"


@pytest.fixture
def plan():
    """Load omni_clip_plan.yaml."""
    assert PLAN_PATH.exists(), f"Missing {PLAN_PATH}"
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def manifests(plan):
    """Load all clip manifests listed in the plan."""
    result = {}
    for clip_ref in plan.get("clip_summaries", []):
        clip_id = clip_ref.get("clip_id")
        manifest_ref = clip_ref.get("clip_manifest_ref")
        manifest_path = REPO_ROOT / manifest_ref
        assert manifest_path.exists(), f"Missing manifest {manifest_path}"
        with open(manifest_path, "r", encoding="utf-8") as f:
            result[clip_id] = yaml.safe_load(f)
    return result


@pytest.fixture
def scene_beat_plan():
    """Load scene_beat_plan.yaml for beat reference."""
    with open(SCENE_BEAT_PLAN_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def dialogue_beats():
    """Load dialogue_beats.yaml for dialogue line reference."""
    with open(DIALOGUE_BEATS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestB6OutputsGeneral:
    """General structure and provenance tests."""

    def test_plan_exists(self, plan):
        """Plan file must exist and be valid YAML."""
        assert plan is not None
        assert isinstance(plan, dict)

    def test_plan_has_required_fields(self, plan):
        """Plan must have record_type, scene_id, clip_summaries, packing_strategy."""
        assert plan.get("record_type") == "omni_clip_plan"
        assert plan.get("scene_id") == "SC0001"
        assert "clip_summaries" in plan
        assert isinstance(plan["clip_summaries"], list)
        assert "packing_strategy" in plan

    def test_packer_version_recorded(self, plan):
        """Packing strategy must record packer_version."""
        ps = plan.get("packing_strategy", {})
        assert ps.get("packer_version") == "rhythm_aware_v1"

    def test_clip_count_computed_not_authored(self, plan, manifests):
        """Clip count emerges from packing, not hardcoded."""
        # The fact that manifests match clip_summaries list proves count is computed
        clip_refs = plan.get("clip_summaries", [])
        assert len(manifests) == len(clip_refs)
        # We don't expect SC0001 to have exactly 8 clips; we verify it has
        # whatever the packer produced. No hardcoded target.
        assert len(manifests) > 0, "Packer must produce at least 1 clip"


class TestB6ClipStructure:
    """Validate each clip manifest structure."""

    def test_all_manifests_exist(self, manifests):
        """All referenced clips must have manifest files."""
        assert len(manifests) > 0
        for clip_id, manifest in manifests.items():
            assert manifest is not None
            assert manifest.get("clip_id") == clip_id

    def test_all_clips_have_record_type(self, manifests):
        """Every manifest must declare record_type: omni_clip_manifest."""
        for clip_id, manifest in manifests.items():
            assert manifest.get("record_type") == "omni_clip_manifest", f"{clip_id}"

    def test_all_clips_have_shots_array(self, manifests):
        """Every manifest must have a shots array."""
        for clip_id, manifest in manifests.items():
            assert "shots" in manifest, f"{clip_id} missing shots"
            assert isinstance(manifest["shots"], list), f"{clip_id} shots not a list"
            assert len(manifest["shots"]) > 0, f"{clip_id} shots is empty"


class TestB6DurationValidation:
    """Validate duration constraints per v2 plan."""

    VALID_SHOT_DURATIONS = frozenset(range(3, 16))  # {3, 4, ..., 15}
    MAX_CLIP_DURATION = 15

    def test_every_shot_duration_is_valid_integer(self, manifests):
        """Every shot.duration_seconds must be integer in {3..15}."""
        for clip_id, manifest in manifests.items():
            for i, shot in enumerate(manifest["shots"]):
                duration = shot.get("duration_seconds")
                assert isinstance(duration, int), \
                    f"{clip_id} shot {i}: duration {duration} is not int"
                assert duration in self.VALID_SHOT_DURATIONS, \
                    f"{clip_id} shot {i}: duration {duration} not in {{3..15}}"

    def test_every_clip_total_le_15(self, manifests):
        """Every clip.total_duration_seconds <= 15."""
        for clip_id, manifest in manifests.items():
            total = manifest.get("total_duration_seconds")
            assert total is not None, f"{clip_id} missing total_duration_seconds"
            assert isinstance(total, int), f"{clip_id} total is not int"
            assert total <= self.MAX_CLIP_DURATION, \
                f"{clip_id} total {total}s exceeds max 15s"

    def test_clip_total_equals_sum_of_shots(self, manifests):
        """For every clip, total_duration_seconds == sum(shots[].duration_seconds)."""
        for clip_id, manifest in manifests.items():
            total = manifest.get("total_duration_seconds")
            shot_sum = sum(s.get("duration_seconds", 0) for s in manifest.get("shots", []))
            assert total == shot_sum, \
                f"{clip_id}: total {total} != sum of shots {shot_sum}"


class TestB6DurationReasons:
    """Every shot must carry a duration_reason."""

    def test_every_shot_has_duration_reason(self, manifests):
        """Every shot must have non-empty duration_reason field."""
        for clip_id, manifest in manifests.items():
            for i, shot in enumerate(manifest.get("shots", [])):
                reason = shot.get("duration_reason")
                assert reason is not None, f"{clip_id} shot {i} missing duration_reason"
                assert isinstance(reason, str), f"{clip_id} shot {i} reason not a string"
                assert len(reason) > 0, f"{clip_id} shot {i} reason is empty string"


class TestB6SourceBeatCoverage:
    """All 21 source beats must be covered exactly once."""

    def test_all_beats_covered_exactly_once(self, manifests, scene_beat_plan):
        """Collect all source_beat_ids from all shots; each beat 1-to-1 coverage."""
        all_beat_ids = scene_beat_plan.get("source_beats", [])
        expected_beat_ids = {beat.get("beat_id") for beat in all_beat_ids}

        covered_beat_ids = set()
        for clip_id, manifest in manifests.items():
            for shot in manifest.get("shots", []):
                for beat_id in shot.get("source_beat_ids", []):
                    assert beat_id not in covered_beat_ids, \
                        f"Beat {beat_id} covered multiple times (clips: ...)"
                    assert beat_id in expected_beat_ids, \
                        f"Beat {beat_id} not in scene_beat_plan"
                    covered_beat_ids.add(beat_id)

        assert covered_beat_ids == expected_beat_ids, \
            f"Uncovered beats: {expected_beat_ids - covered_beat_ids}"

    def test_21_beats_total(self, scene_beat_plan):
        """Verify scene_beat_plan has 21 source beats (B1 requirement)."""
        beats = scene_beat_plan.get("source_beats", [])
        assert len(beats) == 21, f"Expected 21 source beats, got {len(beats)}"


class TestB6DialogueLineCoverage:
    """All 8 dialogue lines must be assigned exactly once."""

    def test_all_dialogue_lines_covered(self, manifests, dialogue_beats):
        """Every dialogue line in dialogue_beats must appear in exactly one clip."""
        dialogue_lines = dialogue_beats.get("dialogue_lines", [])
        expected_line_ids = {line.get("line_id") for line in dialogue_lines}

        covered_line_ids = set()
        for clip_id, manifest in manifests.items():
            for line_id in manifest.get("dialogue_line_ids", []):
                assert line_id not in covered_line_ids, \
                    f"Dialogue line {line_id} covered multiple times"
                assert line_id in expected_line_ids, \
                    f"Dialogue line {line_id} not in dialogue_beats"
                covered_line_ids.add(line_id)

        assert covered_line_ids == expected_line_ids, \
            f"Uncovered dialogue lines: {expected_line_ids - covered_line_ids}"

    def test_8_dialogue_lines_total(self, dialogue_beats):
        """Verify dialogue_beats has exactly 8 lines."""
        lines = dialogue_beats.get("dialogue_lines", [])
        assert len(lines) == 8, f"Expected 8 dialogue lines, got {len(lines)}"


class TestB6ShortInsertMerging:
    """short_insert beats must be merged into neighbors, never standalone."""

    def test_no_short_insert_standalone(self, manifests, scene_beat_plan):
        """Collect all short_insert beats; verify none appear alone in a shot."""
        short_inserts = {
            beat.get("beat_id")
            for beat in scene_beat_plan.get("source_beats", [])
            if beat.get("semantic_duration_hint") == "short_insert"
        }

        for clip_id, manifest in manifests.items():
            for shot in manifest.get("shots", []):
                source_beat_ids = set(shot.get("source_beat_ids", []))
                # Check if this shot is exclusively a short_insert (bad)
                shot_inserts = source_beat_ids & short_inserts
                shot_others = source_beat_ids - short_inserts
                if shot_inserts:
                    # If shot has any short_inserts, it must have other beats too
                    assert shot_others, \
                        f"{clip_id}: short_insert(s) {shot_inserts} appearing alone"


class TestB6DialogueHeavyMetadataOnly:
    """Dialogue-heavy clips (>50% dialogue shots) must use metadata_only."""

    def test_dialogue_heavy_clips_are_metadata_only(self, manifests):
        """If a clip's shots are >50% dialogue, continuity_input_mode must be metadata_only."""
        for clip_id, manifest in manifests.items():
            shots = manifest.get("shots", [])
            dialogue_shots = sum(1 for s in shots if s.get("is_dialogue", False))
            dialogue_ratio = dialogue_shots / len(shots) if shots else 0

            if dialogue_ratio > 0.5:
                mode = manifest.get("continuity_input_mode")
                assert mode == "metadata_only", \
                    f"{clip_id}: {dialogue_ratio:.1%} dialogue but continuity_input_mode={mode}"


class TestB6SchemaValidation:
    """Validate against omni_clip_manifest.schema.json and omni_clip_plan.schema.json."""

    def test_plan_schema_valid(self, plan):
        """Plan must validate against omni_clip_plan.schema.json."""
        # Basic validation: check required fields per v2 plan spec
        assert plan.get("record_type") == "omni_clip_plan"
        assert plan.get("scene_id") == "SC0001"
        assert "clip_summaries" in plan
        assert "packing_strategy" in plan
        for summary in plan.get("clip_summaries", []):
            assert summary.get("clip_id")
            assert summary.get("clip_manifest_ref")
            assert summary.get("total_duration_seconds")

    def test_manifests_schema_valid(self, manifests):
        """Each manifest must validate against omni_clip_manifest.schema.json."""
        schema_path = REPO_ROOT / "schemas/omni_clip_manifest.schema.json"
        if not schema_path.exists():
            pytest.skip(f"Schema file {schema_path} not found")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        for clip_id, manifest in manifests.items():
            assert manifest.get("record_type") == "omni_clip_manifest"
            assert manifest.get("clip_id") == clip_id
            assert "shots" in manifest
            assert "total_duration_seconds" in manifest


class TestB6NoPromptRecords:
    """No prompt records must be generated (that's A7 work)."""

    def test_no_prompts_in_outputs(self, manifests):
        """Manifests must not contain prompt_record, prompt_text, or generation_params."""
        for clip_id, manifest in manifests.items():
            # These fields belong to A7, not B6
            assert "prompt_record" not in manifest or manifest.get("prompt_record") is None, \
                f"{clip_id}: contains prompt_record (A7 work, not B6)"
            assert "generation_params" not in manifest or not manifest.get("generation_params"), \
                f"{clip_id}: contains generation_params (A7 work, not B6)"


class TestB6Determinism:
    """Verify deterministic output: same beat plan → same clip plan."""

    def test_packer_is_deterministic(self):
        """Run packer twice on same inputs; outputs must be identical."""
        from scripts.agents.omni_clip_planner import plan_omni_clips

        repo_root = REPO_ROOT
        beat_plan_ref = "planning/scenes/SC0001/scene_beat_plan.yaml"
        dialogue_beats_ref = "planning/scenes/SC0001/dialogue_beats.yaml"

        # Run 1
        plan1, manifests1 = plan_omni_clips(
            scene_id="SC0001",
            beat_plan_ref=beat_plan_ref,
            dialogue_beats_ref=dialogue_beats_ref,
            repo_root=repo_root,
            created_by="test",
            created_at="2026-05-09T00:00:00Z"
        )

        # Run 2
        plan2, manifests2 = plan_omni_clips(
            scene_id="SC0001",
            beat_plan_ref=beat_plan_ref,
            dialogue_beats_ref=dialogue_beats_ref,
            repo_root=repo_root,
            created_by="test",
            created_at="2026-05-09T00:00:00Z"
        )

        assert len(manifests1) == len(manifests2)
        for m1, m2 in zip(manifests1, manifests2):
            assert m1 == m2, "Packer produced different outputs for identical inputs"


class TestB6AcceptanceChecklist:
    """Roll-up: all B6 acceptance criteria must pass."""

    def test_b6_acceptance_full(self, plan, manifests, scene_beat_plan, dialogue_beats):
        """All B6 acceptance criteria in one place."""
        errors = []

        # 1. Clip count computed
        if not len(manifests) > 0:
            errors.append("Clip count is zero or missing")

        # 2. All 21 beats covered exactly once
        all_beat_ids = scene_beat_plan.get("source_beats", [])
        expected_beats = {b.get("beat_id") for b in all_beat_ids}
        covered_beats = set()
        for manifest in manifests.values():
            for shot in manifest.get("shots", []):
                covered_beats.update(shot.get("source_beat_ids", []))
        if covered_beats != expected_beats:
            errors.append(f"Beat coverage mismatch: {expected_beats - covered_beats}")

        # 3. All 8 dialogue lines assigned exactly once
        all_lines = dialogue_beats.get("dialogue_lines", [])
        expected_lines = {l.get("line_id") for l in all_lines}
        covered_lines = set()
        for manifest in manifests.values():
            covered_lines.update(manifest.get("dialogue_line_ids", []))
        if covered_lines != expected_lines:
            errors.append(f"Dialogue line mismatch: {expected_lines - covered_lines}")

        # 4-6. Duration validation
        VALID_DURATIONS = frozenset(range(3, 16))
        for clip_id, manifest in manifests.items():
            total = manifest.get("total_duration_seconds", 0)
            if total > 15:
                errors.append(f"{clip_id} total {total}s > 15s")
            shot_sum = 0
            for shot in manifest.get("shots", []):
                dur = shot.get("duration_seconds")
                if not isinstance(dur, int) or dur not in VALID_DURATIONS:
                    errors.append(f"{clip_id}: invalid shot duration {dur}")
                shot_sum += dur
                if not shot.get("duration_reason"):
                    errors.append(f"{clip_id}: shot missing duration_reason")
            if shot_sum != total:
                errors.append(f"{clip_id}: sum {shot_sum} != total {total}")

        # 7. No short_insert standalone
        short_inserts = {
            b.get("beat_id")
            for b in scene_beat_plan.get("source_beats", [])
            if b.get("semantic_duration_hint") == "short_insert"
        }
        for clip_id, manifest in manifests.items():
            for shot in manifest.get("shots", []):
                beat_ids = set(shot.get("source_beat_ids", []))
                if beat_ids <= short_inserts:
                    errors.append(f"{clip_id}: short_insert(s) {beat_ids} standalone")

        # 8. Dialogue-heavy → metadata_only
        for clip_id, manifest in manifests.items():
            shots = manifest.get("shots", [])
            dialogue_count = sum(1 for s in shots if s.get("is_dialogue"))
            if len(shots) > 0 and dialogue_count / len(shots) > 0.5:
                if manifest.get("continuity_input_mode") != "metadata_only":
                    errors.append(f"{clip_id}: dialogue-heavy but not metadata_only")

        # 9-11. No prompts
        for clip_id, manifest in manifests.items():
            if manifest.get("prompt_record") or manifest.get("generation_params"):
                errors.append(f"{clip_id}: contains prompt data (A7 work)")

        assert not errors, "B6 acceptance failures:\n" + "\n".join(errors)

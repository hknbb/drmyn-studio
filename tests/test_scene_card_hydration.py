from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
HYDRATE_SCRIPT = REPO_ROOT / "scripts" / "hydrate_scene_cards_from_spine.py"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate_phase1.py"
TEST_TMP_ROOT = REPO_ROOT / ".tmp_source_spine_tests"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        digest.update(str(file_path.relative_to(root)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class SceneCardHydrationTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp_dir = TEST_TMP_ROOT / self._testMethodName
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

        for name in ["source", "planning", "schemas", "prompts"]:
            shutil.copytree(REPO_ROOT / name, self.temp_dir / name)
        (self.temp_dir / "evidence" / "validation_reports").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_hydrate_scenes_is_idempotent_and_validation_safe(self) -> None:
        master_path = self.temp_dir / "source" / "screenplay" / "closing_price.fountain"
        scenes_root = self.temp_dir / "planning" / "scenes"
        report_path = self.temp_dir / "evidence" / "validation_reports" / "scene_hydration_report.json"
        master_hash_before = sha256_file(master_path)

        hydrate_cmd = [
            sys.executable,
            str(HYDRATE_SCRIPT),
            "--retrieval-map",
            str(self.temp_dir / "planning" / "manifests" / "closing_price_scene_retrieval_map.json"),
            "--scenes-root",
            str(scenes_root),
            "--numbered-source",
            str(self.temp_dir / "source" / "screenplay" / "closing_price.numbered.fountain"),
            "--report",
            str(report_path),
        ]

        subprocess.run(hydrate_cmd, check=True, cwd=REPO_ROOT)
        first_tree_hash = hash_tree(scenes_root)
        first_report_hash = sha256_file(report_path)
        subprocess.run(hydrate_cmd, check=True, cwd=REPO_ROOT)
        second_tree_hash = hash_tree(scenes_root)
        second_report_hash = sha256_file(report_path)

        self.assertEqual(master_hash_before, sha256_file(master_path))
        self.assertEqual(first_tree_hash, second_tree_hash)
        self.assertEqual(first_report_hash, second_report_hash)

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(120, report["scenes_processed"])
        self.assertEqual([], report["numbered_fountain_validation"]["missing_scene_markers"])
        self.assertEqual(21, len(report["scenes_missing_clear_slugline_structure"]))
        self.assertEqual(120, len(report["scenes_needing_manual_review"]))

        for scene_id in ["SC0001", "SC0003", "SC0006", "SC0008", "SC0009"]:
            card = load_yaml(scenes_root / scene_id / "scene_card.yaml")
            self.assertEqual(scene_id, card["scene_id"])
            self.assertEqual("scene_excerpt.md", card["excerpt_ref"])
            self.assertEqual("scaffolded", card["status"])
            self.assertEqual("needs_human_review", card["review_status"])
            self.assertIn("source_line_start", card)
            self.assertIn("source_line_end", card)
            self.assertIn("mapping_confidence", card)

            prompt_text = (scenes_root / scene_id / "prompt_brief.md").read_text(encoding="utf-8")
            self.assertIn("## Human Review Required", prompt_text)
            self.assertNotIn("Prompt translation goals", prompt_text)

        sc0001 = load_yaml(scenes_root / "SC0001" / "scene_card.yaml")
        sc0008 = load_yaml(scenes_root / "SC0008" / "scene_card.yaml")
        self.assertEqual("VALE RESIDENCE — VARDOVA — KITCHEN PASSAGE", sc0001["location_text_raw"])
        self.assertEqual("EARLY MORNING", sc0001["time_of_day_text_raw"])
        self.assertIsNone(sc0008["location_text_raw"])
        self.assertIsNone(sc0008["time_of_day_text_raw"])

        validate_cmd = [
            sys.executable,
            str(VALIDATE_SCRIPT),
            "--source-dir",
            str(self.temp_dir / "source"),
            "--planning-dir",
            str(self.temp_dir / "planning"),
            "--prompts-dir",
            str(self.temp_dir / "prompts"),
            "--schemas-dir",
            str(self.temp_dir / "schemas"),
            "--evidence-dir",
            str(self.temp_dir / "evidence"),
            "--report-json",
            str(self.temp_dir / "evidence" / "validation_reports" / "phase1_validation_report.json"),
            "--report-md",
            str(self.temp_dir / "evidence" / "validation_reports" / "phase1_validation_report.md"),
        ]
        subprocess.run(validate_cmd, check=True, cwd=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()

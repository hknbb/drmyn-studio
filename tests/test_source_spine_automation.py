from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_numbered_fountain.py"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_scene_cards.py"
SOURCE_FILE = REPO_ROOT / "source" / "screenplay" / "closing_price.fountain"
RETRIEVAL_MAP = REPO_ROOT / "planning" / "manifests" / "closing_price_scene_retrieval_map.json"
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


def extraction_offset(map_data: dict) -> int:
    return len(map_data["source_file"].get("ignored_prefix_lines", []))


def extract_scene_text(scene: dict, map_data: dict, source_lines: list[str]) -> str:
    offset = extraction_offset(map_data)
    start = scene["source_line_start"] - offset
    end = scene["source_line_end"] - offset
    return "\n".join(source_lines[start - 1:end])


def extract_fenced_block(markdown_text: str) -> str:
    start = markdown_text.index("```fountain\n") + len("```fountain\n")
    end = markdown_text.index("\n```", start)
    return markdown_text[start:end]


class SourceSpineAutomationTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp_dir = TEST_TMP_ROOT / self._testMethodName
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        (self.temp_dir / "source" / "screenplay").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "planning" / "manifests").mkdir(parents=True, exist_ok=True)
        (self.temp_dir / "planning" / "scenes").mkdir(parents=True, exist_ok=True)

        shutil.copy2(SOURCE_FILE, self.temp_dir / "source" / "screenplay" / SOURCE_FILE.name)
        shutil.copy2(RETRIEVAL_MAP, self.temp_dir / "planning" / "manifests" / RETRIEVAL_MAP.name)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_build_numbered_fountain_is_idempotent_and_preserves_master(self) -> None:
        master_path = self.temp_dir / "source" / "screenplay" / SOURCE_FILE.name
        numbered_path = self.temp_dir / "source" / "screenplay" / "closing_price.numbered.fountain"
        master_hash_before = sha256_file(master_path)

        build_cmd = [
            sys.executable,
            str(BUILD_SCRIPT),
            "--source",
            str(master_path),
            "--retrieval-map",
            str(self.temp_dir / "planning" / "manifests" / RETRIEVAL_MAP.name),
            "--output",
            str(numbered_path),
        ]
        subprocess.run(build_cmd, check=True, cwd=REPO_ROOT)
        first_output_hash = sha256_file(numbered_path)
        subprocess.run(build_cmd, check=True, cwd=REPO_ROOT)
        second_output_hash = sha256_file(numbered_path)

        self.assertEqual(master_hash_before, sha256_file(master_path))
        self.assertEqual(first_output_hash, second_output_hash)

        numbered_text = numbered_path.read_text(encoding="utf-8")
        self.assertIn("#SC0001#", numbered_text)
        self.assertIn("#SC0120#", numbered_text)

    def test_seed_scene_cards_creates_120_directories_and_exact_excerpt(self) -> None:
        scenes_root = self.temp_dir / "planning" / "scenes"
        seed_cmd = [
            sys.executable,
            str(SEED_SCRIPT),
            "--source",
            str(self.temp_dir / "source" / "screenplay" / SOURCE_FILE.name),
            "--retrieval-map",
            str(self.temp_dir / "planning" / "manifests" / RETRIEVAL_MAP.name),
            "--scenes-root",
            str(scenes_root),
        ]

        subprocess.run(seed_cmd, check=True, cwd=REPO_ROOT)
        first_tree_hash = hash_tree(scenes_root)
        subprocess.run(seed_cmd, check=True, cwd=REPO_ROOT)
        second_tree_hash = hash_tree(scenes_root)

        scene_dirs = sorted(path for path in scenes_root.iterdir() if path.is_dir() and path.name.startswith("SC"))
        self.assertEqual(120, len(scene_dirs))
        self.assertEqual(first_tree_hash, second_tree_hash)

        map_data = json.loads((self.temp_dir / "planning" / "manifests" / RETRIEVAL_MAP.name).read_text(encoding="utf-8"))
        source_lines = (self.temp_dir / "source" / "screenplay" / SOURCE_FILE.name).read_text(encoding="utf-8").splitlines()
        scene = map_data["scenes"][0]
        expected_excerpt = extract_scene_text(scene, map_data, source_lines)

        excerpt_path = scenes_root / "SC0001" / "scene_excerpt.md"
        excerpt_md = excerpt_path.read_text(encoding="utf-8")
        excerpt_block = extract_fenced_block(excerpt_md)

        self.assertEqual(expected_excerpt, excerpt_block)
        self.assertEqual(scene["scene_text_sha256"], hashlib.sha256(excerpt_block.encode("utf-8")).hexdigest())
        self.assertTrue((scenes_root / "SC0120" / "scene_card.yaml").exists())
        self.assertTrue((scenes_root / "SC0120" / "prompt_brief.md").exists())


if __name__ == "__main__":
    unittest.main()

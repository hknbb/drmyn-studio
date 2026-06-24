"""generate_sc0089_v08_audio.py

Phase 4 of the SC0089 native-audio pipeline.

For each CLIP_SC0089_*.yaml manifest:
  1. Set kling_native_audio.enabled = true (manifest-level audio gate input).
  2. Rewrite shot-level render_diegetic_audio: replace the v07 FORMAT A
     ("no native voice") audio notes with Kling-native voiced-dialogue cues.
Then regenerate the prompt as v08 with render_pass=performance_test (audio-on),
keeping the kling_literal_alias_locked text_only literal profile.

v07 prompts are left untouched (audio-off reference). v08 prompts are the
audio-on production set. Requires the SC0089 speaker bindings to be audio-ready
(native_audio_readiness: ready) — done in Phase 2/3.

Usage:
    python scripts/generate_sc0089_v08_audio.py [--dry-run]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import yaml
from ruamel.yaml import YAML

from scripts.agents.adapters.kling_omni import KlingOmniAdapter

REPO = Path(__file__).resolve().parents[1]
SCENE = "SC0089"
VERSION = 8
DRY_RUN = "--dry-run" in sys.argv

# Exact FORMAT A audio-note -> Kling-native voiced-dialogue replacements.
AUDIO_REPLACEMENTS = {
    "[FORMAT A — no native voice for off-screen comms]":
        "@C04_DIMITRI offscreen comms line voiced (Kling-native).",
    "[FORMAT A — no native voice for 'Over']":
        "@C01_NADIA's line 'Over' voiced (Kling-native).",
    "[FORMAT A — no native voice for 'Where']":
        "@C01_NADIA's line voiced (Kling-native).",
    "[FORMAT A — no native voice for 'Then we move now']":
        "@C01_NADIA's line 'Then we move now' voiced (Kling-native).",
    "[FORMAT A — no native voice]":
        "Native dialogue audio on (Kling-native voice).",
}

ryaml = YAML()
ryaml.preserve_quotes = True
ryaml.indent(mapping=2, sequence=4, offset=2)
ryaml.width = 4096


def _patch_audio(text: str) -> str:
    # Apply the "for ..." variants before the bare token (longest-first is safe
    # since each is a distinct full string, but order is explicit for clarity).
    for needle, repl in AUDIO_REPLACEMENTS.items():
        text = text.replace(needle, repl)
    return text


def patch_manifest(path: Path) -> int:
    """Enable native audio and rewrite FORMAT A audio notes. Returns # of audio lines changed."""
    with path.open("r", encoding="utf-8") as fh:
        data = ryaml.load(fh)

    changed = 0
    kna = data.get("kling_native_audio")
    if isinstance(kna, dict):
        kna["enabled"] = True

    for shot in data.get("shots") or []:
        audio = shot.get("render_diegetic_audio")
        if isinstance(audio, str) and "FORMAT A" in audio:
            shot["render_diegetic_audio"] = _patch_audio(audio)
            changed += 1

    data["notes"] = (
        "SC0089 v08 native-audio pass (kling_literal_alias_locked): render_diegetic_audio "
        "rewritten from FORMAT A (audio-off) to Kling-native voiced dialogue; "
        "kling_native_audio.enabled=true. Speakers C01/C06/C04 audio-ready (Phase 2/3)."
    )
    prov = data.get("provenance") or {}
    prov["audio_pass_added_by"] = "claude_code (M5 v08 SC0089 native audio)"
    prov["audio_pass_added_at"] = "2026-06-24T00:00:00Z"
    data["provenance"] = prov

    if DRY_RUN:
        print(f"  [dry-run] {path.name}: {changed} audio line(s) rewritten, enabled=true")
        return changed
    buf = io.StringIO()
    ryaml.dump(data, buf)
    path.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    print(f"  patched: {path.name}: {changed} audio line(s) rewritten, enabled=true")
    return changed


def _write_yaml(path: Path, data: dict, dry_run: bool) -> None:
    content = yaml.dump(data, allow_unicode=True, sort_keys=False, width=120)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    manifests_dir = REPO / "planning" / "scenes" / SCENE / "manifests"
    draft_dir = REPO / "prompts" / "draft"
    runs_dir = REPO / "evidence" / "prompt_runs"
    manifest_paths = sorted(manifests_dir.glob("CLIP_*.yaml"))

    print(f"=== SC0089 v08 native-audio generation {'(DRY RUN) ' if DRY_RUN else ''}===")
    print(f"Found {len(manifest_paths)} manifests.")

    # Step 1: patch all manifests (audio-on).
    total_audio = 0
    for p in manifest_paths:
        total_audio += patch_manifest(p)
    print(f"Total audio lines rewritten: {total_audio}")

    # Step 2: regenerate v08 prompts at performance_test (audio-on).
    adapter = KlingOmniAdapter(repo_root=REPO, model_guidance_mode="dynamic_snapshot")
    print("\n=== Generating v08 audio-on prompts (render_pass=performance_test) ===")
    for idx, manifest_path in enumerate(manifest_paths, start=1):
        result = adapter.generate_from_clip_manifest(
            manifest_path,
            version=VERSION,
            run_counter=idx,
            input_mode="text_only",
            language_profile="kling_literal_alias_locked",
            variant_mode="safe",
            render_pass="performance_test",
            quality_tier="test_720p",
        )
        record = result.prompt_record
        prompt_id = record["prompt_id"]
        gate = record.get("generation_params", {}).get("audio_gate_status")
        _write_yaml(draft_dir / f"{prompt_id}.yaml", record, DRY_RUN)
        _write_yaml(runs_dir / f"{result.run_record['run_id']}.yaml", result.run_record, DRY_RUN)
        flag = " (warnings)" if result.warnings else ""
        print(f"  {prompt_id}: {len(record['prompt_text'])} chars, audio_gate={gate}{flag}")
        for w in result.warnings:
            print(f"    WARNING: {w}")
    print("Done.")


if __name__ == "__main__":
    main()

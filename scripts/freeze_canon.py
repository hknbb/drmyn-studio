from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(paths: Iterable[Path]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            collected.append(path)
        else:
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    collected.append(file_path)
    return collected


def get_git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def build_manifest(tag: str, include_roots: list[Path], repository_root: Path) -> dict:
    files = iter_files(include_roots)
    manifest_files = []
    for file_path in files:
        rel_path = file_path.relative_to(repository_root).as_posix()
        manifest_files.append({
            "path": rel_path,
            "sha256": sha256_file(file_path),
            "size_bytes": file_path.stat().st_size,
        })
    return {
        "tag": tag,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "file_count": len(manifest_files),
        "files": manifest_files,
    }


def write_manifest(manifest: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "canon_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def write_summary(manifest: dict, output_dir: Path) -> Path:
    lines = [
        "# Canon Freeze Summary",
        "",
        f"Tag: `{manifest['tag']}`",
        f"Created at: `{manifest['created_at']}`",
        f"Git commit: `{manifest['git_commit']}`",
        f"File count: `{manifest['file_count']}`",
    ]
    summary_path = output_dir / "canon_freeze_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


def copy_included_content(
    include_roots: list[Path],
    repository_root: Path,
    staging_dir: Path,
) -> None:
    for root in include_roots:
        if not root.exists():
            continue
        if root.is_file():
            rel = root.relative_to(repository_root)
            target = staging_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root, target)
            continue
        for file_path in root.rglob("*"):
            if file_path.is_file():
                rel = file_path.relative_to(repository_root)
                target = staging_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--planning-dir", required=True)
    parser.add_argument("--prompts-dir", required=True)
    parser.add_argument("--schemas-dir", required=False, default="schemas")
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()

    repository_root = Path(".").resolve()
    source_dir = Path(args.source_dir).resolve()
    planning_dir = Path(args.planning_dir).resolve()
    prompts_dir = Path(args.prompts_dir).resolve()
    schemas_dir = Path(args.schemas_dir).resolve()
    evidence_dir = Path(args.evidence_dir).resolve()

    freeze_root = evidence_dir / "provenance" / args.tag
    staging_dir = freeze_root / "bundle"
    freeze_root.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)

    include_roots = [
        source_dir,
        planning_dir,
        prompts_dir / "approved",
        prompts_dir / "locked",
        schemas_dir,
        evidence_dir / "validation_reports",
    ]

    manifest = build_manifest(
        tag=args.tag,
        include_roots=include_roots,
        repository_root=repository_root,
    )

    manifest_path = write_manifest(manifest, freeze_root)
    summary_path = write_summary(manifest, freeze_root)

    copy_included_content(
        include_roots=include_roots,
        repository_root=repository_root,
        staging_dir=staging_dir,
    )

    shutil.copy2(manifest_path, staging_dir / manifest_path.name)
    shutil.copy2(summary_path, staging_dir / summary_path.name)

    bundle_zip = shutil.make_archive(
        base_name=str(freeze_root / f"{args.tag}_artifact_bundle"),
        format="zip",
        root_dir=str(staging_dir),
    )
    bundle_zip = Path(bundle_zip)

    bundle_hash = sha256_file(bundle_zip)
    (freeze_root / "bundle_sha256.txt").write_text(bundle_hash, encoding="utf-8")

    print(json.dumps({
        "tag": args.tag,
        "manifest": str(manifest_path),
        "summary": str(summary_path),
        "bundle_zip": str(bundle_zip),
        "bundle_sha256": bundle_hash,
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

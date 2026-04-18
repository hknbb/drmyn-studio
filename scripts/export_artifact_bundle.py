from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a publication artifact bundle ZIP for Phase 1."
    )
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--planning-dir", required=True)
    parser.add_argument("--prompts-dir", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--output", required=True, help="Path for the output ZIP (without .zip extension)")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    planning_dir = Path(args.planning_dir)
    prompts_dir = Path(args.prompts_dir)
    evidence_dir = Path(args.evidence_dir)
    output_path = Path(args.output)
    if output_path.suffix == ".zip":
        output_base = str(output_path.with_suffix(""))
    else:
        output_base = str(output_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir) / "bundle"
        staging.mkdir()

        def copy_tree(src: Path, dst_name: str) -> None:
            dst = staging / dst_name
            if src.exists():
                shutil.copytree(src, dst)

        copy_tree(source_dir, "source")
        copy_tree(planning_dir / "manifests", "manifests")
        copy_tree(planning_dir / "scenes", "scenes")
        copy_tree(prompts_dir / "approved", "prompts_approved")
        copy_tree(prompts_dir / "locked", "prompts_locked")
        copy_tree(evidence_dir / "validation_reports", "validation_reports")

        for csv_file in evidence_dir.glob("*.csv"):
            shutil.copy2(csv_file, staging / csv_file.name)

        result = shutil.make_archive(
            base_name=output_base,
            format="zip",
            root_dir=str(staging),
        )
        print(f"Artifact bundle created: {result}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from scripts.reports.export_prod_line_pilot_status import build_report, main


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_report_contains_core_chain_ids() -> None:
    report = build_report(repo_root=REPO_ROOT, scene_id="SC0001")
    assert "GPTIMG2_C01_PERSPECTIVE_PACK_V001" in report
    assert "KLING_REF_C01_V001" in report
    assert "DLG_SC0001_V001" in report
    assert "PERF_SC0001_SH001_V001" in report
    assert "VOICE_C01_V001" in report
    assert "NAC_SC0001_SH001_V001" in report
    assert "KLING_SC0001_SH001_V001" in report
    assert "BATCH_SEQ01_PILOT_V001" in report


def test_report_marks_qc_not_ready_and_decisions_draft() -> None:
    report = build_report(repo_root=REPO_ROOT, scene_id="SC0001")
    assert "perspective QC: NOT READY" in report
    assert "dialogue QC: NOT READY" in report
    assert "Omni QC: NOT READY" in report
    assert "DRAFT ONLY, not applied: YES" in report


def test_script_stdout_mode() -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["--repo-root", str(REPO_ROOT), "--scene-id", "SC0001"])
    assert rc == 0
    out = buf.getvalue()
    assert "# PROD-LINE Pilot Status Report - SC0001" in out


def test_script_output_writes_only_report_file(tmp_path: Path) -> None:
    target_source = REPO_ROOT / "evidence/perspective_qc/PQC_C01_PERSPECTIVE_PACK_V001.yaml"
    before = target_source.read_text(encoding="utf-8")

    output = tmp_path / "SC0001_PROD_LINE_PILOT_STATUS.md"
    rc = main(
        [
            "--repo-root",
            str(REPO_ROOT),
            "--scene-id",
            "SC0001",
            "--output",
            str(output),
        ]
    )
    assert rc == 0
    assert output.exists()
    assert "## Summary" in output.read_text(encoding="utf-8")

    after = target_source.read_text(encoding="utf-8")
    assert before == after


def test_missing_required_file_fails(tmp_path: Path) -> None:
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    try:
        build_report(repo_root=fake_repo, scene_id="SC0001")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass

"""Streamlit entry point for the copilot dashboard."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover - exercised by manual launch
    raise SystemExit(
        "Streamlit is not installed. Install the optional UI dependency first."
    ) from exc

from tools.copilot_dashboard.repo_io import (
    load_latest_recommendation,
    load_recent_handoffs,
    load_recent_sessions,
    load_status_rows,
)
from tools.copilot_dashboard.command_ui import (
    HANDOFF_REASON_OPTIONS,
    TARGET_AGENT_OPTIONS,
    CommandUiResult,
    run_dashboard_command,
)
from tools.copilot_dashboard.review_panels import load_review_panel_data
from tools.copilot_dashboard.pr_panel import PrPanelData, load_pr_panel_data


def _stringify_record(record: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in record.items()}


def _show_command_result(result: CommandUiResult) -> None:
    if result.applied:
        st.success(result.message)
        if result.written_files:
            st.write("Written files:")
            st.write(list(result.written_files))
        return
    st.error(result.message)


def _render_command_controls(recommendation: dict[str, Any]) -> None:
    allowed_commands = recommendation.get("allowed_commands") or []

    st.header("Command Controls")
    st.caption("PR merge remains human-controlled. Commands write metadata evidence only.")

    if not allowed_commands:
        st.write("No commands are allowed by the current recommendation.")
        return

    yes_col, no_col = st.columns(2)
    with yes_col:
        if st.button("Yes", disabled="yes" not in allowed_commands):
            _show_command_result(
                run_dashboard_command(
                    REPO_ROOT,
                    command="yes",
                    allowed_commands=allowed_commands,
                )
            )

    with no_col:
        no_note = st.text_area("No note", key="no_note", height=90)
        if st.button("No", disabled="no" not in allowed_commands):
            _show_command_result(
                run_dashboard_command(
                    REPO_ROOT,
                    command="no",
                    note=no_note,
                    allowed_commands=allowed_commands,
                )
            )

    revise_col, switch_col = st.columns(2)
    with revise_col:
        revise_note = st.text_area("Revise note", key="revise_note", height=90)
        if st.button("Revise", disabled="revise" not in allowed_commands):
            _show_command_result(
                run_dashboard_command(
                    REPO_ROOT,
                    command="revise",
                    note=revise_note,
                    allowed_commands=allowed_commands,
                )
            )

    with switch_col:
        target_agent = st.selectbox("Target agent", TARGET_AGENT_OPTIONS)
        reason = st.selectbox("Reason", HANDOFF_REASON_OPTIONS)
        if st.button("Switch", disabled="switch" not in allowed_commands):
            _show_command_result(
                run_dashboard_command(
                    REPO_ROOT,
                    command="switch",
                    target_agent=target_agent,
                    reason=reason,
                    allowed_commands=allowed_commands,
                )
            )


def _render_review_panels() -> None:
    panel_data = load_review_panel_data(REPO_ROOT)
    image_rows = panel_data["image_candidates"]
    video_rows = panel_data["video_takes"]

    st.header("Review Metadata")
    st.caption(
        "Read-only metadata/path refs. No uploads, thumbnails, cache writes, "
        "or review decisions."
    )

    image_tab, video_tab = st.tabs(["Image Candidates", "Video Takes"])
    with image_tab:
        if image_rows:
            st.dataframe(image_rows, hide_index=True, use_container_width=True)
        else:
            st.write("No image candidate metadata records.")

    with video_tab:
        if video_rows:
            st.dataframe(video_rows, hide_index=True, use_container_width=True)
        else:
            st.write("No video take metadata records.")


def _render_pr_panel() -> None:
    data = load_pr_panel_data(REPO_ROOT)

    st.header("PR Helper")
    st.caption("Suggestion only. This dashboard does not call gh, push, or create PRs.")

    if not data.available:
        st.warning(data.message)
        return

    assert isinstance(data, PrPanelData)
    st.write(f"Branch: `{data.branch}`")
    st.write(f"Title: `{data.title}`")

    if data.changed_files:
        st.write("Changed files:")
        st.dataframe(
            [{"path": path} for path in data.changed_files],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.write("No changed files detected against base.")

    st.text_area("PR body preview", value=data.body_preview, height=260)
    st.code(data.gh_command_str, language="bash")


def main() -> None:
    st.set_page_config(page_title="Copilot Dashboard", layout="wide")
    st.title("Human-Agent Copilot")

    recommendation = load_latest_recommendation(REPO_ROOT)
    status_rows = load_status_rows(REPO_ROOT)
    sessions = load_recent_sessions(REPO_ROOT)
    handoffs = load_recent_handoffs(REPO_ROOT)

    st.header("Latest Recommendation")
    st.json(recommendation)

    st.header("Production Status")
    if status_rows:
        st.dataframe(status_rows, hide_index=True, use_container_width=True)
    else:
        st.write("No production status rows.")

    left, right = st.columns(2)
    with left:
        st.header("Recent Sessions")
        if sessions:
            st.dataframe(
                [_stringify_record(record) for record in sessions],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.write("No operator sessions.")

    with right:
        st.header("Recent Handoffs")
        if handoffs:
            st.dataframe(
                [_stringify_record(record) for record in handoffs],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.write("No agent handoffs.")

    st.header("Allowed Commands")
    commands = recommendation.get("allowed_commands") or []
    if commands:
        st.write(", ".join(str(command) for command in commands))
    else:
        st.write("No allowed commands.")

    _render_command_controls(recommendation)
    _render_review_panels()
    _render_pr_panel()


if __name__ == "__main__":
    main()

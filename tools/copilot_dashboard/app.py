"""Streamlit entry point for the read-only copilot dashboard."""

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


def _stringify_record(record: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in record.items()}


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


if __name__ == "__main__":
    main()

"""
Serializable pipeline state for Batch 7 orchestration.

The state is intentionally small and metadata-only. It carries control-flow
inputs and outputs for existing agents, but it does not represent or promote
production lifecycle state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineState:
    repo_root: str
    mode: str
    scene_ids: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    prompt_ids: list[str] = field(default_factory=list)
    current_task: str | None = None
    written_files: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_step: dict[str, Any] | None = None
    images: str | None = None
    review_notes: str | None = None
    save_snapshot: bool = False
    model_guidance_snapshot_dir: str | None = None
    model_guidance_snapshots: str | None = None
    output_format: str = "text"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["repo_root"] = str(Path(self.repo_root))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineState":
        return cls(
            repo_root=str(data.get("repo_root", ".")),
            mode=str(data.get("mode", "")),
            scene_ids=list(data.get("scene_ids") or []),
            models=list(data.get("models") or []),
            prompt_ids=list(data.get("prompt_ids") or []),
            current_task=data.get("current_task"),
            written_files=list(data.get("written_files") or []),
            skipped=list(data.get("skipped") or []),
            errors=list(data.get("errors") or []),
            next_step=data.get("next_step"),
            images=data.get("images"),
            review_notes=data.get("review_notes"),
            save_snapshot=bool(data.get("save_snapshot", False)),
            model_guidance_snapshot_dir=data.get("model_guidance_snapshot_dir"),
            model_guidance_snapshots=data.get("model_guidance_snapshots"),
            output_format=str(data.get("output_format", "text")),
        )

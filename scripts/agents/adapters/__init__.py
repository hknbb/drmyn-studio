"""
Model adapter package for Batch 4.

Exports:
  MODEL_ALIAS_MAP — canonical map from CLI kebab-case IDs to adapter metadata
  get_adapter()   — factory that resolves a model ID and returns an adapter
  BriefNotReadyError — raised when a brief's is_ready flag is False

Batch coverage:
  midjourney       — Batch 4 (this batch)
  chatgpt_image    — Batch 4 (this batch)
  nano_banana      — Batch 4 (this batch)
  kling_omni       — Batch 8 (Phase 3 only; stub present in docs/model_guides/)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.agents.adapters._base import BaseAdapter, BriefNotReadyError  # noqa: F401


# ---------------------------------------------------------------------------
# Canonical model alias map
#
# Keys: CLI kebab-case model IDs (used in --models flags and prompt_id slugs)
# Values:
#   guide_file  — relative path to the locked model guide YAML
#   adapter     — snake_case Python module name under scripts/agents/adapters/
#   abbrev      — uppercase abbreviation for run_id generation
# ---------------------------------------------------------------------------

MODEL_ALIAS_MAP: dict[str, dict[str, str]] = {
    "midjourney": {
        "guide_file": "docs/model_guides/midjourney.yaml",
        "adapter": "midjourney",
        "abbrev": "MJ",
        "model_id": "midjourney",
    },
    "chatgpt-image": {
        "guide_file": "docs/model_guides/chatgpt_image.yaml",
        "adapter": "chatgpt_image",
        "abbrev": "CGPT",
        "model_id": "chatgpt_image",
    },
    "nano-banana": {
        "guide_file": "docs/model_guides/nano_banana.yaml",
        "adapter": "nano_banana",
        "abbrev": "NB",
        "model_id": "nano_banana",
    },
    "kling-omni": {
        "guide_file": "docs/model_guides/kling_omni.yaml",
        "adapter": "kling_omni",
        "abbrev": "KO",
        "model_id": "kling_omni",
    },
}

# Allow snake_case aliases in addition to kebab-case (for Python caller convenience)
_SNAKE_TO_KEBAB: dict[str, str] = {
    v["model_id"]: k for k, v in MODEL_ALIAS_MAP.items()
}


def resolve_model_key(model_id: str) -> str:
    """
    Return the canonical kebab-case model key for any valid model identifier.

    Accepts both kebab-case (``chatgpt-image``) and snake_case
    (``chatgpt_image``).  Raises ``ValueError`` for unknown identifiers.
    """
    if model_id in MODEL_ALIAS_MAP:
        return model_id
    if model_id in _SNAKE_TO_KEBAB:
        return _SNAKE_TO_KEBAB[model_id]
    raise ValueError(
        f"Unknown model identifier {model_id!r}. "
        f"Valid keys: {sorted(MODEL_ALIAS_MAP)}"
    )


def get_adapter(
    model_id: str,
    repo_root: str | Path,
    *,
    model_guidance_mode: str = "locked_guide",
    model_guidance_snapshot: str | None = None,
) -> BaseAdapter:
    """
    Resolve *model_id* and return an initialised adapter instance.

    Accepts kebab-case (CLI form) or snake_case (Python form) identifiers.
    ``kling_omni`` / ``kling-omni`` resolves to the Batch 8 metadata-only
    adapter.
    """
    key = resolve_model_key(model_id)
    adapter_name = MODEL_ALIAS_MAP[key]["adapter"]

    if adapter_name == "midjourney":
        from scripts.agents.adapters.midjourney import MidjourneyAdapter as Cls
    elif adapter_name == "chatgpt_image":
        from scripts.agents.adapters.chatgpt_image import ChatGPTImageAdapter as Cls
    elif adapter_name == "nano_banana":
        from scripts.agents.adapters.nano_banana import NanaBananaAdapter as Cls
    elif adapter_name == "kling_omni":
        from scripts.agents.adapters.kling_omni import KlingOmniAdapter as Cls
    else:  # pragma: no cover
        raise ValueError(f"No adapter class found for {adapter_name!r}")

    return Cls(
        repo_root=repo_root,
        model_guidance_mode=model_guidance_mode,
        model_guidance_snapshot=model_guidance_snapshot,
    )

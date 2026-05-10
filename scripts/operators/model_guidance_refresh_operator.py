"""
Model Guidance Research Refresh Operator — A6.6

When the model research gate (A6.5) fails or before a production prompt batch,
this operator produces a repeatable research-refresh workflow for each model.

What this script does:
  1. Runs the gate against all required targets.
  2. For each failing target, outputs a research checklist with:
     - Which snapshot fields are stale, missing, or placeholder.
     - Tier-1 and Tier-2 source URLs to consult (per model).
     - Community/general-web notes (low-confidence only; never hard rules).
  3. Generates a YAML scaffold for the operator to fill in and commit.
  4. Writes a summary markdown report to stdout (or a file).

What this script does NOT do:
  - No live web requests.
  - No model API calls.
  - No automatic model version detection.
  - No prompt generation.

Source tier policy:
  Tier 1 — Official: official_docs, official_release_notes, official_help_center
  Tier 2 — Verified: verified_platform_blog, reputable API/provider docs
  Community: low-confidence note only; must not become a hard rule without
             official corroboration and human review

Usage:
    python scripts/operators/model_guidance_refresh_operator.py

    # Check specific targets:
    python scripts/operators/model_guidance_refresh_operator.py \\
        --targets kling_omni_video_best_available midjourney_image_best_available

    # Write scaffold snapshots to a directory:
    python scripts/operators/model_guidance_refresh_operator.py --write-scaffolds

    # Write a markdown report:
    python scripts/operators/model_guidance_refresh_operator.py --report-file refresh_report.md
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Per-model research source registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResearchSource:
    url: str
    title: str
    tier: int  # 1 = official, 2 = verified platform blog / reputable API docs
    source_type: str  # official_docs | official_release_notes | official_help_center | verified_platform_blog
    notes: str = ""


@dataclass(frozen=True)
class ModelResearchProfile:
    internal_target: str
    provider: str
    provider_surface: str
    snapshot_subdir: str       # under model_guidance_snapshots/
    freshness_days: int        # how many days before snapshot expires
    known_sources: list[ResearchSource] = field(default_factory=list)
    community_notes: list[str] = field(default_factory=list)  # low-confidence only
    fields_to_verify: list[str] = field(default_factory=list)


RESEARCH_PROFILES: dict[str, ModelResearchProfile] = {
    "kling_omni_video_best_available": ModelResearchProfile(
        internal_target="kling_omni_video_best_available",
        provider="kling",
        provider_surface="api",
        snapshot_subdir="kling",
        freshness_days=7,
        known_sources=[
            ResearchSource(
                url="https://kling.ai/quickstart/klingai-element-library-3-user-guide",
                title="Kling AI — Element Library 3 User Guide (Omni)",
                tier=1,
                source_type="official_docs",
                notes="Element Library, @ alias usage in Omni prompts, element reference syntax.",
            ),
            ResearchSource(
                url="https://docs.magnific.com/api-reference/video/kling-v3-omni/generate-std-video-reference",
                title="Magnific API — Kling v3 Omni Generate Standard Video",
                tier=1,
                source_type="official_docs",
                notes="Hard API limits: negative_prompt max chars, cfg_scale range, aspect ratio, duration 3-15s.",
            ),
            ResearchSource(
                url="https://blog.fal.ai/kling-3-0-prompting-guide/",
                title="FAL.ai — Kling 3.0 Official Prompting Guide",
                tier=2,
                source_type="verified_platform_blog",
                notes="Cinematic direction style, motion intensity scale, end-state requirement, T2V vs I2V guidance.",
            ),
            ResearchSource(
                url="https://www.veed.io/learn/kling-ai-prompting-guide",
                title="VEED.io — Kling AI Prompting Guide",
                tier=2,
                source_type="verified_platform_blog",
                notes="Shot labeling structure, multi-shot guidance, character consistency.",
            ),
            ResearchSource(
                url="https://www.atlascloud.ai/blog/guides/kling-3.0-review-features-pricing-ai-alternatives",
                title="AtlasCloud — Kling 3.0 Review and Features",
                tier=2,
                source_type="verified_platform_blog",
                notes="Release date (2026-02-05), flagship status, 4K/30fps, up to 6 shots per generation.",
            ),
        ],
        community_notes=[
            "Community reports of 99% hang for very long prompts exist but are unverified. "
            "Do not treat as hard rule. Prefer official API char limits instead.",
            "Forum posts on prompt word counts are inconsistent; verify against Magnific API reference.",
        ],
        fields_to_verify=[
            "current_default_model",
            "latest_available_model",
            "best_for_this_task",
            "feature_required_model.element_library",
            "feature_required_model.multi_shot",
            "constraints.prompt_text_max_chars",
            "constraints.negative_prompt_max_chars",
            "constraints.element_references_max",
            "prompting_rules (@ alias syntax for element-based Omni)",
        ],
    ),

    "midjourney_image_best_available": ModelResearchProfile(
        internal_target="midjourney_image_best_available",
        provider="midjourney",
        provider_surface="web_ui",
        snapshot_subdir="midjourney",
        freshness_days=14,
        known_sources=[
            ResearchSource(
                url="https://docs.midjourney.com/hc/en-us/articles/32199405667853-Version",
                title="Midjourney — Version Docs (official)",
                tier=1,
                source_type="official_docs",
                notes="Current default version, latest available version, version-specific capabilities.",
            ),
            ResearchSource(
                url="https://docs.midjourney.com/hc/en-us/articles/32199723099533-Omni-Reference",
                title="Midjourney — Omni Reference Guide",
                tier=1,
                source_type="official_docs",
                notes="Omni reference feature, image reference syntax, reference weight parameters.",
            ),
            ResearchSource(
                url="https://midjourney.com/updates",
                title="Midjourney — Official Updates / Release Notes",
                tier=1,
                source_type="official_release_notes",
                notes="Latest version releases, new features, deprecations.",
            ),
        ],
        community_notes=[
            "Community tip sheets vary widely by version; verify each rule against official docs.",
            "Prompt token counts discussed in Discord are not official limits; use official docs only.",
        ],
        fields_to_verify=[
            "current_default_model",
            "latest_available_model",
            "best_for_this_task",
            "feature_required_model.omni_reference",
            "constraints.max_prompt_tokens",
            "prompting_rules (natural language vs comma-clause preference per version)",
        ],
    ),

    "chatgpt_image_best_available": ModelResearchProfile(
        internal_target="chatgpt_image_best_available",
        provider="openai",
        provider_surface="chatgpt_ui",
        snapshot_subdir="openai",
        freshness_days=14,
        known_sources=[
            ResearchSource(
                url="https://help.openai.com/en/articles/9055440",
                title="OpenAI Help Center — Images in ChatGPT",
                tier=1,
                source_type="official_help_center",
                notes="Current image model version in ChatGPT, capabilities, size/format options.",
            ),
            ResearchSource(
                url="https://platform.openai.com/docs/guides/images",
                title="OpenAI Platform — Image Generation Guide",
                tier=1,
                source_type="official_docs",
                notes="API model IDs, parameters, constraint_strategy for models without negative_prompt.",
            ),
            ResearchSource(
                url="https://openai.com/blog",
                title="OpenAI Blog — Release Announcements",
                tier=1,
                source_type="official_release_notes",
                notes="GPT-Image version releases, feature updates.",
            ),
        ],
        community_notes=[
            "Community prompt guides for ChatGPT Images vary; prefer official platform docs.",
            "Token or word limits for ChatGPT Image prompts are not publicly documented; avoid inventing hard limits.",
        ],
        fields_to_verify=[
            "current_default_model",
            "latest_available_model",
            "best_for_this_task",
            "constraints.constraint_strategy (embedded_positive_constraints if no negative_prompt)",
            "prompting_rules (natural language full sentences preferred)",
        ],
    ),

    "nano_banana_best_available": ModelResearchProfile(
        internal_target="nano_banana_best_available",
        provider="google",
        provider_surface="api",
        snapshot_subdir="google",
        freshness_days=14,
        known_sources=[
            ResearchSource(
                url="https://ai.google.dev/gemini-api/docs/image-generation",
                title="Google Gemini API — Image Generation Docs",
                tier=1,
                source_type="official_docs",
                notes="Nano Banana Pro (Gemini 3 Pro Image) capabilities, API parameters.",
            ),
            ResearchSource(
                url="https://blog.google/products/gemini/prompting-tips-nano-banana-pro",
                title="Google Blog — Nano Banana Pro Prompting Tips",
                tier=1,
                source_type="official_release_notes",
                notes="Prompting guidance from Google, professional detail support, multi-image input.",
            ),
            ResearchSource(
                url="https://developers.googleblog.com/en/",
                title="Google Developers Blog",
                tier=2,
                source_type="verified_platform_blog",
                notes="Integration examples, best practice updates.",
            ),
        ],
        community_notes=[
            "Nano Banana (internal alias for Gemini image generation) may have limited public community resources; prefer official Google docs.",
        ],
        fields_to_verify=[
            "current_default_model",
            "latest_available_model",
            "best_for_this_task",
            "constraints (prompt length, image count, resolution)",
            "prompting_rules (detail richness, professional descriptors)",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Freshness policy
# ---------------------------------------------------------------------------

SNAPSHOT_FRESHNESS_DAYS: dict[str, int] = {
    "kling_omni_video_best_available": 7,
    "midjourney_image_best_available": 14,
    "chatgpt_image_best_available": 14,
    "nano_banana_best_available": 14,
}


# ---------------------------------------------------------------------------
# Checklist generation
# ---------------------------------------------------------------------------


def generate_research_checklist(
    target: str,
    hard_errors: list[str],
    soft_warnings: list[str],
) -> str:
    """
    Generate a markdown research checklist for a failing or stale target.

    Args:
        target: internal_model_target string.
        hard_errors: From TargetGateResult.hard_errors.
        soft_warnings: From TargetGateResult.soft_warnings.

    Returns:
        Markdown string with research checklist.
    """
    profile = RESEARCH_PROFILES.get(target)
    lines: list[str] = []

    lines.append(f"## Research Checklist: `{target}`")
    lines.append("")

    if hard_errors:
        lines.append("### Gate Failures (must fix before prompt generation)")
        for err in hard_errors:
            lines.append(f"- ❌ {err}")
        lines.append("")

    if soft_warnings:
        lines.append("### Soft Warnings (recommended to fix)")
        for warn in soft_warnings:
            lines.append(f"- ⚠️  {warn}")
        lines.append("")

    if profile is None:
        lines.append(f"> No research profile found for `{target}`. Add to `RESEARCH_PROFILES` in model_guidance_refresh_operator.py.")
        return "\n".join(lines)

    lines.append("### Fields to Verify / Update")
    for fv in profile.fields_to_verify:
        lines.append(f"- [ ] {fv}")
    lines.append("")

    lines.append("### Tier 1 — Official Sources (authoritative)")
    t1 = [s for s in profile.known_sources if s.tier == 1]
    for src in t1:
        lines.append(f"- **[{src.title}]({src.url})**")
        lines.append(f"  - Source type: `{src.source_type}`")
        if src.notes:
            lines.append(f"  - Notes: {src.notes}")
    lines.append("")

    t2 = [s for s in profile.known_sources if s.tier == 2]
    if t2:
        lines.append("### Tier 2 — Verified Platform Blogs / Reputable API Docs")
        for src in t2:
            lines.append(f"- **[{src.title}]({src.url})**")
            lines.append(f"  - Source type: `{src.source_type}`")
            if src.notes:
                lines.append(f"  - Notes: {src.notes}")
        lines.append("")

    if profile.community_notes:
        lines.append("### Community / General Web — Low Confidence Only")
        lines.append("> ⚠️  These notes are low-confidence. They must NOT become hard rules without")
        lines.append("> official corroboration and human review.")
        lines.append("")
        for note in profile.community_notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("### After Research")
    lines.append(f"1. Update `model_guidance_snapshots/{profile.snapshot_subdir}/<timestamp>_{target}.yaml`")
    lines.append("2. Set `human_verified: true` after review.")
    lines.append(f"3. Set `expires_at` to `observed_at + {profile.freshness_days} days`.")
    lines.append("4. Run gate: `python scripts/validators/validate_model_research_gate.py --targets " + target + "`")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Snapshot scaffold
# ---------------------------------------------------------------------------


def generate_snapshot_scaffold(
    target: str,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """
    Generate a YAML scaffold for the operator to fill in and commit.

    The scaffold has all required fields with placeholder values clearly
    marked as TODO. The operator fills in real values from research.

    Args:
        target: internal_model_target string.
        reference_time: UTC datetime for timestamp (default: now).

    Returns:
        Dict conforming to model_guidance_snapshot schema shape.
    """
    profile = RESEARCH_PROFILES.get(target)
    ref = reference_time or datetime.now(timezone.utc)
    ts = ref.strftime("%Y%m%dT%H%M%SZ")
    observed_str = ref.strftime("%Y-%m-%dT%H:%M:%SZ")

    freshness = SNAPSHOT_FRESHNESS_DAYS.get(target, 14)
    expires_at = (ref + timedelta(days=freshness)).strftime("%Y-%m-%dT%H:%M:%SZ")

    provider = profile.provider if profile else "TODO_provider"
    provider_surface = profile.provider_surface if profile else "TODO_surface"
    snapshot_subdir = profile.snapshot_subdir if profile else "TODO_subdir"

    source_scaffolds: list[dict] = []
    if profile:
        for src in profile.known_sources[:2]:  # include first 2 as starting point
            source_scaffolds.append({
                "source_type": src.source_type,
                "title": src.title,
                "retrieved_at": "TODO_fill_in_retrieval_timestamp",
                "url": src.url,
            })
    if not source_scaffolds:
        source_scaffolds.append({
            "source_type": "official_docs",
            "title": "TODO_fill_in_source_title",
            "retrieved_at": "TODO_fill_in_retrieval_timestamp",
            "url": "TODO_fill_in_url",
        })

    scaffold: dict[str, Any] = {
        "record_type": "model_guidance_snapshot",
        "schema_version": "0.x-draft",
        "snapshot_id": f"{ts}_{target}",
        "internal_model_target": target,
        "provider": provider,
        "model_family": "TODO_fill_in_model_family",
        "provider_surface": provider_surface,
        "observed_at": observed_str,
        "expires_at": expires_at,
        "human_verified": False,
        "current_default_model": "TODO_fill_in_from_official_docs",
        "latest_available_model": "TODO_fill_in_from_official_docs",
        "best_for_this_task": "TODO_fill_in_from_official_docs",
        "feature_required_model": {
            "TODO_feature_name": "TODO_fill_in_model",
        },
        "version_policy": {
            "hardcode_in_adapter": False,
            "adapter_must_read_snapshot": True,
            "prompt_generation_blocks_if_expired": True,
            "prompt_generation_blocks_if_unverified": True,
        },
        "sources": source_scaffolds,
        "capabilities": {
            "output_type": "TODO_video_or_image",
            "supports_negative_prompt": "TODO_true_false_or_limited",
        },
        "constraints": {
            "TODO_constraint_key": "TODO_fill_in_value",
        },
        "prompting_rules": [
            "TODO_fill_in_rule_from_official_docs",
        ],
        "provenance": {
            "created_by": "TODO_operator_name",
            "created_at": observed_str,
        },
        "_scaffold_notes": (
            f"SCAFFOLD — fill in all TODO_ fields from research. "
            f"Set human_verified: true when done. "
            f"File path: model_guidance_snapshots/{snapshot_subdir}/{ts}_{target}.yaml"
        ),
    }
    return scaffold


# ---------------------------------------------------------------------------
# Full refresh report
# ---------------------------------------------------------------------------


def generate_refresh_report(
    repo_root: Path,
    required_targets: list[str],
    reference_time: datetime | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Run the gate, then produce a research report for all targets.

    Args:
        repo_root: Repository root.
        required_targets: Targets to check.
        reference_time: For gate expiry checks.

    Returns:
        (markdown_report, scaffold_dicts)
        scaffold_dicts contains scaffolds only for failing targets.
    """
    from scripts.validators.validate_model_research_gate import validate_model_research_gate

    ref = reference_time or datetime.now(timezone.utc)
    results = validate_model_research_gate(
        repo_root=repo_root,
        required_targets=required_targets,
        reference_time=ref,
    )

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    lines: list[str] = [
        "# Model Guidance Research Refresh Report",
        "",
        f"Generated: {ref.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        f"**Gate result: {len(passed)}/{len(results)} targets pass**",
        "",
    ]

    if passed:
        lines.append("### Passing Targets (no refresh needed)")
        for r in passed:
            lines.append(f"- ✅ `{r.target}`")
            if r.soft_warnings:
                for w in r.soft_warnings:
                    lines.append(f"  - ⚠️  {w}")
        lines.append("")

    scaffolds: list[dict[str, Any]] = []

    if failed:
        lines.append("### Failing Targets (refresh required before prompt generation)")
        for r in failed:
            lines.append(f"- ❌ `{r.target}`")
        lines.append("")

        for r in failed:
            lines.append("---")
            lines.append("")
            lines.append(
                generate_research_checklist(r.target, r.hard_errors, r.soft_warnings)
            )
            lines.append("")
            scaffolds.append(generate_snapshot_scaffold(r.target, ref))
    else:
        lines.append("All targets pass. Prompt generation is unblocked.")
        lines.append("")
        lines.append("If you want to perform a proactive refresh (recommended before a production batch),")
        lines.append("review the Tier 1 sources in `docs/operator_guides/model_guidance_research_refresh.md`.")

    lines.append("---")
    lines.append("## Next Steps")
    lines.append("")
    if failed:
        lines.append("1. For each failing target, follow the research checklist above.")
        lines.append("2. Fill in the generated scaffold YAML (see --write-scaffolds).")
        lines.append("3. Commit the updated snapshot to `model_guidance_snapshots/<provider>/`.")
        lines.append("4. Set `human_verified: true` after review.")
        lines.append("5. Re-run: `python scripts/validators/validate_model_research_gate.py`")
    else:
        lines.append("1. (Optional) Run proactive research refresh using sources in operator guide.")
        lines.append("2. Proceed with prompt generation.")

    return "\n".join(lines), scaffolds


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

KNOWN_TARGETS = list(RESEARCH_PROFILES.keys())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Model Guidance Research Refresh Operator — "
            "generate research checklists and snapshot scaffolds when the gate fails."
        )
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=KNOWN_TARGETS,
        metavar="TARGET",
        help=f"Targets to check. Defaults to all known targets.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        metavar="PATH",
        help="Repository root directory (default: current directory).",
    )
    parser.add_argument(
        "--write-scaffolds",
        action="store_true",
        help="Write YAML scaffold files for failing targets to model_guidance_snapshots/<provider>/.",
    )
    parser.add_argument(
        "--report-file",
        metavar="FILE",
        help="Write markdown report to FILE instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    report_md, scaffolds = generate_refresh_report(
        repo_root=repo_root,
        required_targets=args.targets,
    )

    if args.report_file:
        Path(args.report_file).write_text(report_md, encoding="utf-8")
        print(f"Report written to {args.report_file}")
    else:
        print(report_md)

    if args.write_scaffolds and scaffolds:
        for scaffold in scaffolds:
            target = scaffold["internal_model_target"]
            profile = RESEARCH_PROFILES.get(target)
            subdir = profile.snapshot_subdir if profile else "unknown"
            ts = scaffold["snapshot_id"].split("_")[0] if "_" in scaffold["snapshot_id"] else "scaffold"
            out_dir = repo_root / "model_guidance_snapshots" / subdir
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{ts}_{target}_SCAFFOLD.yaml"
            out_path.write_text(
                yaml.dump(scaffold, allow_unicode=True, sort_keys=False, width=120),
                encoding="utf-8",
            )
            print(f"Scaffold written: {out_path}")

    # Exit 1 if any scaffolds were produced (gate had failures)
    return 1 if scaffolds else 0


if __name__ == "__main__":
    sys.exit(main())

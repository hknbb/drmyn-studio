"""
Neutral Brief Agent for Batch 3.

Produces model-agnostic element briefs from SourceContext records. Each brief
includes cited visual anchors (with source field paths), resolved continuity
state, negative constraints (element-specific + global style bible rules), and
readiness flags that block downstream adapters when continuity is unresolved.

Downstream model adapters (Batch 4) consume NeutralBrief objects to generate
model-specific prompt records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.agents.aesthetic_bible import (
    AestheticBible,
    get_pack_ids_from_records,
    resolve_pack_keywords,
    resolve_pack_negatives,
)
from scripts.agents.continuity import (
    MissingPropRecordError,
    PropStateResolution,
    resolve_prop_state_at_scene,
    resolve_wardrobe_state_at_scene,
)
from scripts.agents.source_context import SourceContext


# ---------------------------------------------------------------------------
# Element-type → prompt_type mapping (mirrors adapters/_base.py ELEMENT_TO_PROMPT_TYPE)
# ---------------------------------------------------------------------------

_ELEMENT_TO_PROMPT_TYPE: dict[str, str] = {
    "character": "t2i_character_element",
    "location": "t2i_location_element",
    "prop": "t2i_prop_element",
    "wardrobe": "t2i_wardrobe_element",
    "style": "t2i_style_reference",
}


# ---------------------------------------------------------------------------
# UNRESOLVED marker detection
# ---------------------------------------------------------------------------

UNRESOLVED_RE = re.compile(r"\b(UNRESOLVED|TODO_REVIEW|TODO|EVIDENCE_THIN)\b")


def _has_unresolved(text: str) -> bool:
    return bool(UNRESOLVED_RE.search(text))


# ---------------------------------------------------------------------------
# Style bible constraint extraction
# ---------------------------------------------------------------------------


def _extract_style_do_not_rules(style_text: str) -> list[str]:
    """
    Parse negative production constraints from the style bible.

    Captures:
    - All bullets in formal ``Do not do:`` sections.
    - Standalone ``- Do not ...`` bullets outside formal sections.
    - Standalone ``- No ...`` bullets (``## Negative visual rules`` style).

    Does NOT capture UNRESOLVED / TODO_REVIEW meta-notes.
    """
    rules: list[str] = []
    in_do_not_section = False

    for line in style_text.splitlines():
        stripped = line.strip()

        # Formal "Do not do:" section header
        if stripped == "Do not do:":
            in_do_not_section = True
            continue

        if in_do_not_section:
            if stripped.startswith("- ") or stripped.startswith("* "):
                rule = stripped[2:].strip()
                if rule:
                    rules.append(rule)
            elif stripped.startswith("#"):
                # New section header ends collection
                in_do_not_section = False
            elif stripped and not stripped.startswith("-") and not stripped.startswith("*"):
                # Non-bullet, non-blank, non-header line ends collection
                in_do_not_section = False
            # Blank lines are allowed within bullet sections
        else:
            # Outside formal "Do not do:" section: catch explicit negative bullets
            if stripped.startswith("- ") or stripped.startswith("* "):
                content = stripped[2:].strip()
                cl = content.lower()
                if cl.startswith("do not ") or cl.startswith("no "):
                    rules.append(content)

    return rules


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VisualAnchor:
    """A source-cited visual fact for a T2I element."""

    description: str
    source_field: str  # dotted path, e.g. "character.C01.visual_profile.color_bias"


@dataclass(frozen=True)
class NeutralBrief:
    """Model-agnostic element brief for one T2I element."""

    scene_id: str
    element_type: str       # character | location | prop | wardrobe | style
    element_id: str         # e.g. C01, LOC001, PROP001, WD001, style_bible
    element_name: str       # repo/provenance identity — do NOT write to prompt_text
    visual_anchors: list[VisualAnchor]
    negative_constraints: list[str]
    continuity_state: str | None
    continuity_note: str | None
    continuity_warning: str | None
    model_guidance_required: bool   # always True
    is_ready: bool                  # False when UNRESOLVED continuity or anchors
    warnings: list[str] = field(default_factory=list)
    aesthetic_pack_refs: tuple[str, ...] = ()
    aesthetic_keywords: tuple[str, ...] = ()
    # Safe external-model label (adapters use this, never element_name directly)
    prompt_subject_label: str = ""
    # Planning names that must not appear literally in generated prompt_text
    planning_aliases: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _anchor(description: str | None, source_field: str) -> VisualAnchor | None:
    """Return a VisualAnchor if description is non-empty, else None."""
    desc = (description or "").strip()
    if not desc:
        return None
    return VisualAnchor(description=desc, source_field=source_field)


def _anchors_from_list(
    items: list[Any] | None,
    source_field: str,
) -> list[VisualAnchor]:
    """Convert a list of strings to VisualAnchor objects."""
    anchors: list[VisualAnchor] = []
    for i, item in enumerate(items or []):
        a = _anchor(str(item), f"{source_field}[{i}]")
        if a:
            anchors.append(a)
    return anchors


def _safe_subject_label(element_name: str, element_type: str) -> str:
    """Return an external-model-safe visual label — never a planning surname or location name."""
    if element_type == "character":
        tokens = element_name.split()
        return tokens[0] if tokens else ""
    if element_type == "location":
        return ""  # describe locations visually via anchors, not by planning name
    return element_name


def _planning_aliases_for(element_name: str, element_type: str) -> tuple[str, ...]:
    """Names that must not appear literally in T2I prompt_text.

    Character surnames are NOT added — they may appear legitimately in
    source-derived anchor text (e.g. costume_logic referencing "Vale residence
    scenes"). Only the full display name is forbidden for characters.
    Location canonical names and their comma-parts are fully forbidden.
    """
    if not element_name:
        return ()
    aliases: list[str] = [element_name]
    if element_type == "character":
        pass  # full name only; surname skipped to avoid source-evidence false positives
    elif element_type == "location":
        for part in element_name.split(","):
            part = part.strip()
            if part and part != element_name:
                aliases.append(part)
    return tuple(dict.fromkeys(aliases))


def _is_ready_from_anchors_and_constraints(
    anchors: list[VisualAnchor],
    negative_constraints: list[str],
    continuity_warning: str | None,
) -> bool:
    """Return True only when no UNRESOLVED markers appear in any output field."""
    if continuity_warning is not None:
        return False
    for a in anchors:
        if _has_unresolved(a.description):
            return False
    for c in negative_constraints:
        if _has_unresolved(c):
            return False
    return True


# ---------------------------------------------------------------------------
# Element-type builders
# ---------------------------------------------------------------------------


def _build_character_brief(
    scene_id: str,
    char_id: str,
    char_data: dict[str, Any],
    style_rules: list[str],
) -> NeutralBrief:
    warnings: list[str] = []
    anchors: list[VisualAnchor] = []
    prefix = f"character.{char_id}"
    vp = char_data.get("visual_profile") or {}

    # Visual profile fields — prefer nested visual_profile, fall back to top-level
    for field_name, value in (
        ("age_range", vp.get("age_range") or char_data.get("visual_age_range")),
        ("screen_presence", vp.get("screen_presence")),
        ("silhouette", vp.get("silhouette") or char_data.get("silhouette_notes")),
        ("color_bias", vp.get("color_bias") or char_data.get("color_bias")),
        ("costume_logic", vp.get("costume_logic") or char_data.get("costume_logic")),
        ("hair_makeup_notes", vp.get("hair_makeup_notes")),
    ):
        a = _anchor(value, f"{prefix}.visual_profile.{field_name}")
        if a:
            anchors.append(a)

    # physical_description_grounded (rarely present on character records)
    a = _anchor(
        char_data.get("physical_description_grounded"),
        f"{prefix}.physical_description_grounded",
    )
    if a:
        anchors.append(a)

    # Negative constraints: element-specific do_not_invent_notes + global style rules
    negative_constraints: list[str] = []
    for note in char_data.get("do_not_invent_notes") or []:
        negative_constraints.append(str(note))
    negative_constraints.extend(style_rules)

    for a in anchors:
        if _has_unresolved(a.description):
            warnings.append(f"UNRESOLVED marker in {a.source_field}")

    element_name = str(char_data.get("display_name") or char_data.get("name") or char_id)
    return NeutralBrief(
        scene_id=scene_id,
        element_type="character",
        element_id=char_id,
        element_name=element_name,
        visual_anchors=anchors,
        negative_constraints=negative_constraints,
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=_is_ready_from_anchors_and_constraints(anchors, negative_constraints, None),
        warnings=warnings,
        prompt_subject_label=_safe_subject_label(element_name, "character"),
        planning_aliases=_planning_aliases_for(element_name, "character"),
    )


def _build_location_brief(
    scene_id: str,
    location_data: dict[str, Any],
    style_rules: list[str],
) -> NeutralBrief:
    warnings: list[str] = []
    anchors: list[VisualAnchor] = []
    loc_id = str(location_data.get("location_id") or "location")
    prefix = f"location.{loc_id}"
    vp = location_data.get("visual_profile") or {}

    for field_name, value in (
        ("palette", vp.get("palette")),
        ("architecture_logic", vp.get("architecture_logic")),
        ("lighting_logic", vp.get("lighting_logic")),
        ("camera_behavior", vp.get("camera_behavior")),
        ("sound_texture", vp.get("sound_texture")),
    ):
        a = _anchor(value, f"{prefix}.visual_profile.{field_name}")
        if a:
            anchors.append(a)

    # spatial_motifs list
    spatial_motifs = vp.get("spatial_motifs") or []
    if spatial_motifs:
        a = _anchor(
            ", ".join(str(m) for m in spatial_motifs),
            f"{prefix}.visual_profile.spatial_motifs",
        )
        if a:
            anchors.append(a)

    # material_profile and texture_profile lists
    material = location_data.get("material_profile") or []
    if material:
        a = _anchor(
            ", ".join(str(m) for m in material),
            f"{prefix}.material_profile",
        )
        if a:
            anchors.append(a)

    texture = location_data.get("texture_profile") or []
    if texture:
        a = _anchor(
            ", ".join(str(t) for t in texture),
            f"{prefix}.texture_profile",
        )
        if a:
            anchors.append(a)

    # stable_visual_rules as anchors (positive production rules)
    anchors.extend(
        _anchors_from_list(
            location_data.get("stable_visual_rules"),
            f"{prefix}.stable_visual_rules",
        )
    )

    # emotional_register
    a = _anchor(
        location_data.get("emotional_register"),
        f"{prefix}.emotional_register",
    )
    if a:
        anchors.append(a)

    # Negative constraints: non_invention_rules + style rules
    negative_constraints: list[str] = []
    for rule in location_data.get("non_invention_rules") or []:
        negative_constraints.append(str(rule))
    negative_constraints.extend(style_rules)

    for a in anchors:
        if _has_unresolved(a.description):
            warnings.append(f"UNRESOLVED marker in {a.source_field}")

    element_name = str(location_data.get("canonical_name") or location_data.get("name") or loc_id)
    return NeutralBrief(
        scene_id=scene_id,
        element_type="location",
        element_id=loc_id,
        element_name=element_name,
        visual_anchors=anchors,
        negative_constraints=negative_constraints,
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=_is_ready_from_anchors_and_constraints(anchors, negative_constraints, None),
        warnings=warnings,
        prompt_subject_label=_safe_subject_label(element_name, "location"),
        planning_aliases=_planning_aliases_for(element_name, "location"),
    )


def _build_prop_brief(
    scene_id: str,
    prop_id: str,
    prop_data: dict[str, Any],
    resolution: PropStateResolution | None,
    style_rules: list[str],
) -> NeutralBrief:
    warnings: list[str] = []
    anchors: list[VisualAnchor] = []
    prefix = f"prop.{prop_id}"

    for field_name, value in (
        ("visual_description", prop_data.get("visual_description")),
        ("physical_description_grounded", prop_data.get("physical_description_grounded")),
    ):
        a = _anchor(value, f"{prefix}.{field_name}")
        if a:
            anchors.append(a)

    anchors.extend(
        _anchors_from_list(
            prop_data.get("visual_stability_notes"),
            f"{prefix}.visual_stability_notes",
        )
    )

    # Negative constraints: handling_notes + style rules
    negative_constraints: list[str] = []
    for note in prop_data.get("handling_notes") or []:
        negative_constraints.append(str(note))
    negative_constraints.extend(style_rules)

    # Continuity state from resolver
    cont_state: str | None = None
    cont_note: str | None = None
    cont_warning: str | None = None
    if resolution is not None:
        cont_state = resolution.resolved_state
        cont_note = resolution.note
        cont_warning = resolution.warning
        if cont_warning:
            warnings.append(cont_warning)

    for a in anchors:
        if _has_unresolved(a.description):
            warnings.append(f"UNRESOLVED marker in {a.source_field}")

    return NeutralBrief(
        scene_id=scene_id,
        element_type="prop",
        element_id=prop_id,
        element_name=str(
            prop_data.get("canonical_name") or prop_data.get("name") or prop_id
        ),
        visual_anchors=anchors,
        negative_constraints=negative_constraints,
        continuity_state=cont_state,
        continuity_note=cont_note,
        continuity_warning=cont_warning,
        model_guidance_required=True,
        is_ready=_is_ready_from_anchors_and_constraints(
            anchors, negative_constraints, cont_warning
        ),
        warnings=warnings,
    )


def _build_wardrobe_brief(
    scene_id: str,
    wardrobe_id: str,
    wardrobe_data: dict[str, Any],
    resolution: PropStateResolution | None,
    style_rules: list[str],
) -> NeutralBrief:
    warnings: list[str] = []
    anchors: list[VisualAnchor] = []
    prefix = f"wardrobe.{wardrobe_id}"

    for field_name, value in (
        ("visual_description", wardrobe_data.get("visual_description")),
        ("color_profile", wardrobe_data.get("color_profile")),
        ("silhouette", wardrobe_data.get("silhouette")),
        ("material_notes", wardrobe_data.get("material_notes")),
        ("palette_bias", wardrobe_data.get("palette_bias")),
        ("semiotic_function", wardrobe_data.get("semiotic_function")),
    ):
        a = _anchor(value, f"{prefix}.{field_name}")
        if a:
            anchors.append(a)

    # Negative constraints: continuity_constraints + style rules
    negative_constraints: list[str] = []
    for c in wardrobe_data.get("continuity_constraints") or []:
        negative_constraints.append(str(c))
    negative_constraints.extend(style_rules)

    # Continuity state from resolver
    cont_state: str | None = None
    cont_note: str | None = None
    cont_warning: str | None = None
    if resolution is not None:
        cont_state = resolution.resolved_state
        cont_note = resolution.note
        cont_warning = resolution.warning
        if cont_warning:
            warnings.append(cont_warning)

    for a in anchors:
        if _has_unresolved(a.description):
            warnings.append(f"UNRESOLVED marker in {a.source_field}")

    return NeutralBrief(
        scene_id=scene_id,
        element_type="wardrobe",
        element_id=wardrobe_id,
        element_name=str(wardrobe_data.get("name") or wardrobe_id),
        visual_anchors=anchors,
        negative_constraints=negative_constraints,
        continuity_state=cont_state,
        continuity_note=cont_note,
        continuity_warning=cont_warning,
        model_guidance_required=True,
        is_ready=_is_ready_from_anchors_and_constraints(
            anchors, negative_constraints, cont_warning
        ),
        warnings=warnings,
    )


def _build_style_brief(
    scene_id: str,
    style_text: str | None,
) -> NeutralBrief:
    warnings: list[str] = []
    anchors: list[VisualAnchor] = []
    negative_constraints: list[str] = []

    if style_text:
        negative_constraints = _extract_style_do_not_rules(style_text)

        # Visual thesis as a high-level anchor
        thesis_match = re.search(
            r"## Visual thesis\n+([\s\S]+?)(?=\n##|\Z)",
            style_text,
        )
        if thesis_match:
            thesis_text = thesis_match.group(1).strip()
            # Cap to 600 chars to avoid oversized anchors
            a = _anchor(thesis_text[:600], "style_bible.visual_thesis")
            if a:
                anchors.append(a)

        if _has_unresolved(style_text):
            warnings.append("UNRESOLVED marker in style_bible")

    is_ready = len(warnings) == 0

    return NeutralBrief(
        scene_id=scene_id,
        element_type="style",
        element_id="style_bible",
        element_name="Style Bible",
        visual_anchors=anchors,
        negative_constraints=negative_constraints,
        continuity_state=None,
        continuity_note=None,
        continuity_warning=None,
        model_guidance_required=True,
        is_ready=is_ready,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Aesthetic bible resolution helpers
# ---------------------------------------------------------------------------


def _resolve_aesthetic(
    bible: AestheticBible | None,
    scene_card: dict[str, Any],
    element_record: dict[str, Any] | None,
    element_type: str,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """
    Return (pack_ids, keywords, extra_negatives, warnings) for one element brief.

    Deterministic: ordered union of scene + element pack refs, deduplicated.
    Unknown pack_ids are preserved in pack_ids for provenance but produce a
    warning and contribute no keywords or negatives. Never invents data.
    """
    if bible is None:
        return [], [], [], []
    prompt_type = _ELEMENT_TO_PROMPT_TYPE.get(element_type, "")
    pack_ids = get_pack_ids_from_records(scene_card, element_record)
    if not pack_ids:
        return [], [], [], []
    known_ids = {p.pack_id for p in bible.packs}
    extra_warnings = [
        f"Unknown aesthetic pack ref: {pid}"
        for pid in pack_ids
        if pid not in known_ids
    ]
    keywords = resolve_pack_keywords(bible.packs, pack_ids, prompt_type, limit_per_pack=2)
    negatives = resolve_pack_negatives(bible.packs, pack_ids)
    return pack_ids, keywords, negatives, extra_warnings


def _with_aesthetic(
    brief: NeutralBrief,
    pack_refs: list[str],
    keywords: list[str],
    extra_warnings: list[str] | None = None,
) -> NeutralBrief:
    """Return a new NeutralBrief with aesthetic fields and any pack warnings merged."""
    if not pack_refs and not keywords and not extra_warnings:
        return brief
    import dataclasses
    merged_warnings = list(brief.warnings)
    if extra_warnings:
        merged_warnings.extend(extra_warnings)
    return dataclasses.replace(
        brief,
        aesthetic_pack_refs=tuple(pack_refs),
        aesthetic_keywords=tuple(keywords),
        warnings=merged_warnings,
    )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class NeutralBriefAgent:
    """
    Generate model-agnostic element briefs from a SourceContext.

    One brief is produced per element type present in the scene:
    - ``character`` — one per character in SourceContext.characters
    - ``location``  — one for SourceContext.location (if not None)
    - ``prop``      — one per prop in SourceContext.props
    - ``wardrobe``  — one per wardrobe item in SourceContext.wardrobe
    - ``style``     — always one, from SourceContext.style_bible_text

    Continuity resolution (prop + wardrobe) is attempted via the repo's
    planning files. Resolution failures are caught silently; the brief is
    generated with ``continuity_state=None`` rather than crashing.
    """

    def __init__(self, repo_root: str | Path) -> None:
        self.repo_root = Path(repo_root)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_scene_briefs(self, scene_context: SourceContext) -> list[NeutralBrief]:
        """Build all element briefs for a scene in a deterministic order."""
        style_rules = _extract_style_do_not_rules(
            scene_context.style_bible_text or ""
        )
        bible = scene_context.aesthetic_bible
        scene_card = scene_context.scene_card
        briefs: list[NeutralBrief] = []

        # Character briefs
        for char_id, char_data in scene_context.characters.items():
            a_pack_refs, a_keywords, a_negatives, a_warnings = _resolve_aesthetic(
                bible, scene_card, char_data, "character"
            )
            brief = _build_character_brief(
                scene_context.scene_id,
                char_id,
                char_data,
                style_rules + a_negatives,
            )
            briefs.append(_with_aesthetic(brief, a_pack_refs, a_keywords, a_warnings))

        # Location brief
        if scene_context.location is not None:
            a_pack_refs, a_keywords, a_negatives, a_warnings = _resolve_aesthetic(
                bible, scene_card, scene_context.location, "location"
            )
            brief = _build_location_brief(
                scene_context.scene_id,
                scene_context.location,
                style_rules + a_negatives,
            )
            briefs.append(_with_aesthetic(brief, a_pack_refs, a_keywords, a_warnings))

        # Prop briefs
        for prop_id, prop_data in scene_context.props.items():
            resolution = self._try_resolve_prop(scene_context.scene_id, prop_id)
            a_pack_refs, a_keywords, a_negatives, a_warnings = _resolve_aesthetic(
                bible, scene_card, prop_data, "prop"
            )
            brief = _build_prop_brief(
                scene_context.scene_id,
                prop_id,
                prop_data,
                resolution,
                style_rules + a_negatives,
            )
            briefs.append(_with_aesthetic(brief, a_pack_refs, a_keywords, a_warnings))

        # Wardrobe briefs
        for wardrobe_id, wardrobe_data in scene_context.wardrobe.items():
            resolution = self._try_resolve_wardrobe(
                scene_context.scene_id, wardrobe_id
            )
            a_pack_refs, a_keywords, a_negatives, a_warnings = _resolve_aesthetic(
                bible, scene_card, wardrobe_data, "wardrobe"
            )
            brief = _build_wardrobe_brief(
                scene_context.scene_id,
                wardrobe_id,
                wardrobe_data,
                resolution,
                style_rules + a_negatives,
            )
            briefs.append(_with_aesthetic(brief, a_pack_refs, a_keywords, a_warnings))

        # Style brief (always last, always present — no aesthetic injection)
        briefs.append(
            _build_style_brief(
                scene_context.scene_id,
                scene_context.style_bible_text,
            )
        )

        return briefs

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_resolve_prop(
        self, scene_id: str, prop_id: str
    ) -> PropStateResolution | None:
        """Attempt prop continuity resolution; return None on any failure."""
        try:
            return resolve_prop_state_at_scene(self.repo_root, prop_id, scene_id)
        except (MissingPropRecordError, Exception):
            return None

    def _try_resolve_wardrobe(
        self, scene_id: str, wardrobe_id: str
    ) -> PropStateResolution | None:
        """Attempt wardrobe continuity resolution; return None on any failure."""
        try:
            return resolve_wardrobe_state_at_scene(
                self.repo_root, wardrobe_id, scene_id
            )
        except (MissingPropRecordError, Exception):
            return None

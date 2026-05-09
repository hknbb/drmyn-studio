"""
Model guidance snapshot resolver.

Resolves the current best-available model version from human-verified,
non-expired snapshots. Blocks prompt generation on missing, expired,
unverified, or placeholder snapshots.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema
import yaml


class ModelGuidanceResolutionError(Exception):
	"""Raised when snapshot resolution fails."""

	pass


def resolve_model_guidance(
	repo_root: Path | str,
	internal_model_target: str,
	required_feature: Optional[str] = None,
	now: Optional[datetime] = None,
) -> dict[str, Any]:
	"""
	Resolve the current best-available model from a human-verified snapshot.

	Args:
		repo_root: Repository root path.
		internal_model_target: One of kling_video_best_available,
			midjourney_image_best_available, chatgpt_image_best_available,
			nano_banana_best_available.
		required_feature: Optional feature name (e.g., 'omni_reference').
			If provided, resolves feature_required_model[required_feature]
			instead of best_for_this_task.
		now: Current datetime for expiry checks. Defaults to now in UTC.

	Returns:
		A dict with resolved model information:
		- model_guidance_snapshot_ref: relative path to snapshot YAML
		- provider: provider string
		- provider_surface: how the model is accessed
		- resolved_model_name: the chosen model version string
		- resolved_model_role: enum [current_default, latest_available, best_for_this_task, feature_required]
		- guidance_observed_at: ISO-8601 when snapshot was observed
		- guidance_expires_at: ISO-8601 when snapshot expires
		- prompting_rules: array of rule strings
		- capabilities: model capabilities dict
		- constraints: model constraints dict

	Raises:
		ModelGuidanceResolutionError: if snapshot is missing, expired,
			unverified, contains placeholders, or unsupported feature.
	"""
	repo_root = Path(repo_root)
	if now is None:
		now = datetime.now(timezone.utc)

	snapshots_dir = repo_root / "model_guidance_snapshots"
	schema_path = repo_root / "schemas" / "model_guidance_snapshot.schema.json"

	if not schema_path.exists():
		raise ModelGuidanceResolutionError(
			f"Schema file missing: {schema_path}"
		)

	with open(schema_path, "r", encoding="utf-8") as f:
		schema = json.load(f)

	validator = jsonschema.Draft202012Validator(schema)

	candidates = _find_snapshots(
		snapshots_dir=snapshots_dir,
		internal_model_target=internal_model_target,
	)

	if not candidates:
		raise ModelGuidanceResolutionError(
			f"No snapshots found for internal_model_target={internal_model_target!r} "
			f"in {snapshots_dir}"
		)

	best_snapshot = None
	best_snapshot_path = None
	best_observed_at = None

	for snapshot_path, snapshot_data in candidates:
		expires_at_str = snapshot_data.get("expires_at")
		if expires_at_str:
			expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
			if expires_at < now:
				continue  # Skip expired, evaluate other candidates

		try:
			validator.validate(snapshot_data)
		except jsonschema.ValidationError as e:
			raise ModelGuidanceResolutionError(
				f"Snapshot {snapshot_path} is schema-invalid: {e.message}"
			)

		if not snapshot_data.get("human_verified", False):
			raise ModelGuidanceResolutionError(
				f"Snapshot {snapshot_path} is unverified "
				f"(human_verified={snapshot_data.get('human_verified')})"
			)

		latest_available = snapshot_data.get("latest_available_model")
		best_for_task = snapshot_data.get("best_for_this_task")

		if _is_placeholder(latest_available) or _is_placeholder(best_for_task):
			raise ModelGuidanceResolutionError(
				f"Snapshot {snapshot_path} contains placeholder model values: "
				f"latest_available_model={latest_available!r}, "
				f"best_for_this_task={best_for_task!r}"
			)

		if required_feature:
			feature_models = snapshot_data.get("feature_required_model", {})
			feature_model = feature_models.get(required_feature)
			if not feature_model or _is_placeholder(feature_model):
				raise ModelGuidanceResolutionError(
					f"Snapshot {snapshot_path} missing or placeholder feature_required_model "
					f"for required_feature={required_feature!r} "
					f"(value={feature_model!r})"
				)

		observed_at_str = snapshot_data.get("observed_at")
		if observed_at_str:
			observed_at = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
			if best_observed_at is None or observed_at > best_observed_at:
				best_snapshot = snapshot_data
				best_snapshot_path = snapshot_path
				best_observed_at = observed_at

	if best_snapshot is None:
		raise ModelGuidanceResolutionError(
			f"No valid snapshot found for internal_model_target={internal_model_target!r}"
		)

	assert best_snapshot_path is not None  # Set together with best_snapshot in loop

	if required_feature:
		resolved_model_name = best_snapshot["feature_required_model"][required_feature]
		resolved_model_role = "feature_required"
	else:
		resolved_model_name = best_snapshot.get("best_for_this_task")
		if not resolved_model_name:
			resolved_model_name = best_snapshot.get("latest_available_model")
			if not resolved_model_name:
				raise ModelGuidanceResolutionError(
					f"Snapshot {best_snapshot_path} has no resolvable model "
					f"(best_for_this_task=null and latest_available_model=null)"
				)
			resolved_model_role = "latest_available"
		else:
			resolved_model_role = "best_for_this_task"

	rel_path = best_snapshot_path.relative_to(repo_root)

	return {
		"model_guidance_snapshot_ref": str(rel_path).replace("\\", "/"),
		"provider": best_snapshot.get("provider"),
		"provider_surface": best_snapshot.get("provider_surface"),
		"resolved_model_name": resolved_model_name,
		"resolved_model_role": resolved_model_role,
		"guidance_observed_at": best_snapshot.get("observed_at"),
		"guidance_expires_at": best_snapshot.get("expires_at"),
		"prompting_rules": best_snapshot.get("prompting_rules", []),
		"capabilities": best_snapshot.get("capabilities", {}),
		"constraints": best_snapshot.get("constraints", {}),
	}


def _find_snapshots(
	snapshots_dir: Path,
	internal_model_target: str,
) -> list[tuple[Path, dict[str, Any]]]:
	"""Find and load all snapshots matching the internal_model_target."""
	candidates = []

	if not snapshots_dir.exists():
		return candidates

	for yaml_file in snapshots_dir.rglob("*.yaml"):
		try:
			with open(yaml_file, "r", encoding="utf-8") as f:
				data = yaml.safe_load(f)
			if data is None:
				continue
			if data.get("internal_model_target") == internal_model_target:
				candidates.append((yaml_file, data))
		except (yaml.YAMLError, IOError):
			continue

	return candidates


def _is_placeholder(value: Any) -> bool:
	"""Check if value is a placeholder or unset."""
	if value is None:
		return False
	if isinstance(value, str):
		return value in ("", "TBD", "TODO", "unknown", "PLACEHOLDER")
	return False

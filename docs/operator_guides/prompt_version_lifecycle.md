# Prompt Draft Version Lifecycle

This note records the doctrine for prompt-draft versioning, resolving the
historical conflict between "keep deprecated" and "delete superseded" (P9).

## Doctrine: superseded drafts are deleted

A prompt draft is identified by a logical stem plus a version suffix:

```
SC0014__clip-clip-sc0014-03-safe__v05   ← logical stem + version
```

When a newer version of the same logical stem is written, the older draft
file(s) under `prompts/draft/` are **deleted**, and their matching entries in
`prompts/prompt_library.yaml` are removed. There is exactly one active draft
per logical stem at any time — the highest version.

Git history is the archive: every superseded version remains fully recoverable
from version control, so nothing is lost. Keeping stale `vNN` files on disk only
adds clutter and ambiguity about which version is canonical.

## What is and is not pruned

- **Pruned:** the superseded `prompts/draft/*.yaml` file and its
  `prompt_library.yaml` index entry.
- **Kept:** `evidence/prompt_runs/*` run records and the
  `evidence/run_costs.csv` / `evidence/scene_prompt_map.csv` rows. These are an
  audit/cost trail of what was generated and when; they are append-only history,
  not "the current draft", so they are not destroyed by a version bump.

## Where this is enforced

`PromptWriter.write()` calls `_prune_superseded_drafts()` after writing the new
draft (`scripts/agents/writer.py`). Pruned paths are returned on
`WriteResult.pruned_drafts` for logging/transparency.

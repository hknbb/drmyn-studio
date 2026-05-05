# Agent Handoff Playbook

This playbook explains how the human operator rotates work between Claude Code,
Codex, Gemini Code Assist, and ChatGPT Project without losing repo context.
It uses the existing Human-Agent Copilot `switch` command and does not change
the handoff implementation.

## Purpose

Use an agent handoff when a model reaches context limits, a reviewer needs to
take over, or a second opinion is useful. The handoff record is a metadata-only
YAML file under `evidence/agent_handoffs/HO-*.yaml`.

The next agent must read the handoff, inspect the listed `context_files`, verify
the `branch` and `head_sha`, and continue only the listed `do_steps` and
`expected_outputs`.

## Canonical Commands

Run commands from the repo root.

Switch to Claude Code for scoped implementation:

```bash
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent claude_code \
  --reason manual_pickup \
  --repo-root .
```

Switch to Codex for repo-faithful review, repair, or validation:

```bash
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent codex \
  --reason review_requested \
  --repo-root .
```

Switch to Gemini Code Assist for second opinion or pinch-hit implementation:

```bash
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent gemini_code_assist \
  --reason second_opinion \
  --repo-root .
```

Switch to ChatGPT Project for planning or prose only:

```bash
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent chatgpt_project \
  --reason context_too_large \
  --repo-root .
```

## Message Templates

Codex to Claude Code:

```text
Repo-faithful mode. Continue from this handoff record:

evidence/agent_handoffs/HO-YYYYMMDD-HHMMSS.yaml

Read the handoff, inspect the listed context_files, verify branch/head_sha,
and implement only the expected_outputs. Keep changes surgical and do not touch
scope-guarded files.
```

Claude Code to Codex:

```text
You are the repo auditor / patch reviewer. Continue from:

evidence/agent_handoffs/HO-YYYYMMDD-HHMMSS.yaml

Verify current branch, changed files, context_files, do_steps,
expected_outputs, and safety_warnings against the repository before reviewing
or planning any patch.
```

Claude Code or Codex to Gemini Code Assist:

```text
Continue from this repository handoff:

evidence/agent_handoffs/HO-YYYYMMDD-HHMMSS.yaml

Use only the listed files and current branch context. Keep changes within the
expected_outputs and do not touch scope-guarded files.
```

Any agent to ChatGPT Project:

```text
Use this handoff for planning/prose context only:

evidence/agent_handoffs/HO-YYYYMMDD-HHMMSS.yaml

Do not write repository files. Return a text plan or review note that the human
operator can paste back into the repo workflow if needed.
```

## Reason Definitions

| Reason | Use when |
|---|---|
| `limit_reached` | The current model is running out of context or tool time. |
| `context_too_large` | The next step needs long-form planning or source-context synthesis. |
| `review_requested` | A repo-faithful review or patch audit is needed. |
| `second_opinion` | Another model should inspect the plan or diff before implementation continues. |
| `manual_pickup` | The human is explicitly moving work to a different agent. |
| `task_complete` | The current agent has finished and is handing off final state. |

## Commit and Stage Guidance

Commit a handoff record when it is part of reviewable repo evidence for an
approved batch, such as a formal handoff between implementation and review.

Keep a handoff local-only when it only records transient model-limit notes,
scratch reasoning, or details that should not become scientific evidence.

Before staging a handoff:

- Confirm all paths are repo-relative.
- Confirm `branch` and `head_sha` match the intended branch.
- Confirm `context_files`, `do_steps`, and `expected_outputs` are scoped.
- Confirm no secrets, local paths, binaries, or unreviewed assets are included.

Do not commit `evidence/agent_handoffs/HO-*.yaml` in a docs-only batch unless
the human explicitly requested a separate operator record.

## Forbidden Handoff Contents

Never include:

- tokens, API keys, or credentials
- `githubtoken.txt`
- local absolute paths such as `C:\Users\...`
- generated image, video, audio, proxy, or render binaries
- Google Drive secrets or local sync paths
- dirty `prompts/prompt_library.yaml` content
- unreviewed image/video/audio assets
- lifecycle promotion claims
- `pack_status: locked`, `canon_lock`, `approved`, or `locked` changes
- copyright or provenance completion claims without reviewed evidence

## B8A Asset Intake Rule

B8A is the first real canonical asset intake. It remains one slot only:

```text
visual_dev/elements/characters/C01/wardrobe/WD001/
```

B8A must not:

- lock packs
- run Kling generation
- promote lifecycle state
- add assets outside `C01/wardrobe/WD001`
- mark copyright/provenance complete without reviewed evidence
- include placeholder binaries

If an agent needs to switch during B8A, create a handoff first and paste the
handoff path to the next agent before continuing.

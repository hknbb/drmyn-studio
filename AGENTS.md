# Human-Agent Production Copilot

This repository is a metadata-only film production management system. Agents
help draft records, review metadata, and hand work between tools, but human PR
review remains the approval boundary.

## Roles

| Actor | Role |
|---|---|
| `human_operator` | Owns decisions, external tools, lifecycle promotion, and PR approval. |
| `claude_code` | Primary implementation agent for scoped batch work. |
| `codex` | Review and repair agent for repo-faithfulness, tests, validators, and safety gates. |
| `gemini_code_assist` | Second-opinion reviewer and pinch-hitter implementor when Claude and Codex are unavailable. |
| `chatgpt_project` | Long-form planning and source-context exploration outside the repo; output is pasted into notes. |

## Non-Negotiable Invariants

1. **Controlled model guidance:** Agents may refresh model guidance through a controlled Research Snapshot step. Prompt adapters never use unlogged live internet directly. Every model-specific prompt must cite either a locked model guide or a run-specific guidance snapshot with URLs, retrieval timestamps, and hashes.

2. **Draft-only agent output:** Agents may write only to `prompts/draft/`, `evidence/`, and explicitly allowed metadata-only review/suggestion files under `visual_dev/` (e.g. `image_selection.yaml`, `pack_manifest_update_suggestion.yaml`, `storyboard_options.yaml`, `video_takes.yaml`). Agents never commit binaries, never update `pack_status`/`canon_lock`/`approved`/`locked` fields directly, and never promote lifecycle stages without a human PR.

3. **One prompt record per model:** No shared `prompt_text` across Midjourney, ChatGPT Image, Nano Banana, and Kling Omni.

## Copilot Commands

The human operator may use a small command vocabulary:

| Command | Meaning |
|---|---|
| `yes` | Approve the next recommended metadata-only action and write an operator session. |
| `no` | Reject the recommendation and write a skipped operator session with a required note. |
| `revise` | Request a text-only revision loop through a prompt brief or operator revision note. |
| `switch` | Write an `agent_handoff` record so another agent can continue from the current state. Implemented in HA-3a. |

`operator_next_step.py` remains a read-only recommender. Write actions live in
`scripts/agents/copilot_command.py` and are always human-triggered.

## Handoff Discipline

- Use `evidence/agent_handoffs/HO-*.yaml` for Claude, Codex, Gemini, ChatGPT
  Project, or human handoffs.
- Handoff records are repo-relative and metadata-only.
- Do not place tokens, API keys, Google Drive credentials, or GitHub secrets in
  handoff records, notes, docs, logs, or environment files.
- Do not run Google Drive APIs or automatic PR/merge actions from this layer.
- Do not commit image, video, proxy, audio, or other binary production outputs.

See `docs/operator_guides/human_agent_copilot.md` for the full operating
doctrine.

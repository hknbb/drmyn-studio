# Human-Agent Production Copilot

The copilot layer lets a human operator coordinate Claude Code, Codex, Gemini
Code Assist, ChatGPT Project, Visual Studio, and GitHub without adding external
APIs. It sits above the existing production pipeline and does not weaken any
schema, validator, storage, or lifecycle gate.

## Operating Model

`operator_next_step.py` observes the repo and recommends the next safe task.
`copilot_command.py` writes only command records that the human explicitly
requests. This keeps the recommender and writer responsibilities separate.

Text cycle:

```text
repo metadata
  -> operator_next_step.py recommends a safe task
  -> human_operator answers yes / no / revise / switch
  -> copilot_command.py writes the allowed metadata record
  -> next agent reads the record and continues on the same branch
```

HA-3a implemented `switch`. HA-3b added `yes`, `no`, and `revise` as
metadata-only command records. HA-4a added a read-only dashboard viewer, and
HA-4b-1 adds dashboard buttons for the same existing command vocabulary.

## Actors

| Actor | Can do | Must not do |
|---|---|---|
| `human_operator` | Approve work, run external tools manually, create PRs, promote lifecycle fields through review. | Store credentials in repo files or bypass PR review. |
| `claude_code` | Implement scoped batch work and write metadata-only files. | Promote lifecycle fields, commit binaries, or merge directly to main. |
| `codex` | Review, repair, validate, and implement scoped fixes on the same feature branch. | Create parallel permanent implementation branches or silently approve unsafe changes. |
| `gemini_code_assist` | Review Claude/Codex diffs, provide second opinions, and act as pinch-hitter implementor if both are unavailable. | Replace human approval or write credentials/API-driven automation. |
| `chatgpt_project` | Explore long-form context and draft prose outside the repo. | Write files directly to the repository. |

## Command Vocabulary

| Command | Behavior |
|---|---|
| `switch` | Writes `evidence/agent_handoffs/HO-*.yaml` from the current recommendation. |
| `yes` | Writes `evidence/operator_sessions/OP-*.yaml` with `status: in_progress`. |
| `no` | Writes `evidence/operator_sessions/OP-*.yaml` with `status: skipped`; a note is required. |
| `revise` | Writes `evidence/prompt_reviews/*_brief.yaml` for prompt-related tasks, otherwise writes `evidence/operator_sessions/*_revisions.md`. |

For `switch`, `context_files` is copied from the recommendation's `open_files`.
The name changes because a handoff record describes files the next agent needs
as context, not files currently open in a UI.

## Switching Agents

Use `switch` when an agent hits limits, when a second opinion is needed, or when
the human wants a different tool to continue. The handoff record captures:

- source and target agent
- reason for the switch
- current task and scene
- repo-relative context files
- recommended steps and expected outputs
- safety warnings
- branch and head commit when available

The next agent should read the newest relevant handoff before editing files.

For B8A and later asset-intake work, use
[`agent_handoff_playbook.md`](agent_handoff_playbook.md) for copy-paste command
examples, agent-to-agent message templates, commit/stage guidance, forbidden
handoff contents, and the one-slot B8A handoff rule.

## Safety Rules

- Metadata-only: no image, video, audio, proxy, or generated binary commits.
- Agents do not edit `pack_status`, `canon_lock`, `approved`, or `locked`.
- Agents do not promote lifecycle stages without a human PR.
- GitHub, Google Drive, and model credentials stay outside repo files.
- Google Drive storage is manual only; no Drive API is used by this layer.
- PR execution and auto-merge stay human-controlled. Dashboard command buttons
  do not call `gh`, `pr_helper`, external APIs, or Google Drive.
- Handoff paths must be repo-relative POSIX-like paths with no absolute paths
  and no `..` traversal segments.

## Dashboard Controls

The dashboard can show the latest recommendation, status rows, recent operator
sessions, recent handoffs, and allowed commands. In HA-4b-1 it may also submit
`yes`, `no`, `revise`, and `switch` through the existing `apply_command()`
writer.

Dashboard command controls may write only the existing copilot evidence records:

- `evidence/operator_sessions/OP-*.yaml`
- `evidence/operator_sessions/*_revisions.md`
- `evidence/prompt_reviews/*_brief.yaml`
- `evidence/agent_handoffs/HO-*.yaml`

They must not add image or video upload, thumbnail caches, `image_selection`,
`video_takes`, `selected_take`, `scene_clip_map`, production status mutation,
PR helper execution, API calls, Google Drive integration, or lifecycle
promotion.

## Dashboard Review Metadata

In HA-4b-2 the dashboard may show image candidate and video take metadata/path
references from existing records. This panel is read-only: it does not upload
media, copy binaries, generate thumbnails, cache preview files, write review
decisions, or mutate production records.

External refs such as `local://` and `gdrive://` are rendered as text only.
Repo-relative refs are treated as metadata/path refs in this batch; review
actions remain outside the dashboard until a later explicitly scoped PR.

## Dashboard PR Suggestions

In HA-4c-1 the dashboard may display the existing print-only PR suggestion from
`suggest_pr()`. This panel is suggestion-only: it does not call `gh`, push
branches, create pull requests, write body files, handle tokens, execute
subprocesses for GitHub operations, or mutate production metadata.

The human operator remains responsible for reviewing the suggestion and creating
or merging any PR outside this dashboard panel.

## Limit-Reached Procedure

1. Run the current recommendation:

   ```bash
   python scripts/agents/run_pipeline.py --mode operator-next-step --repo-root .
   ```

2. Write a handoff:

   ```bash
   python scripts/agents/run_pipeline.py \
     --mode copilot-command \
     --command switch \
     --to-agent codex \
     --reason limit_reached \
     --repo-root .
   ```

3. Paste the written handoff path to the next agent.
4. Keep working on the same feature branch unless the human explicitly starts a
   new reviewed batch branch.

## Gemini Code Assist

Gemini Code Assist is primarily a reviewer and second-opinion tool inside the
editor. It can become a pinch-hitter implementor only when Claude Code and Codex
are both unavailable or context-limited. In that case it uses the same
`agent_handoff` record and must follow the same metadata-only restrictions.

## ChatGPT Project

ChatGPT Project is for long-form planning, source-context exploration, and prose
drafting outside the repo. The human may paste its useful output into an
`agent_handoff.notes` field. It does not write repository files directly.

## End-to-End Dry Run

The following is a copy-pasteable transcript of the full copilot loop. Run
each command from the repo root. The loop uses real metadata fixtures and
writes only to `evidence/` — no binaries, no lifecycle promotion, no `gh`
execution.

```bash
# 1. Get the current recommendation (storyboard selection in this example)
python scripts/agents/run_pipeline.py --mode operator-next-step --repo-root .

# 2. Switch to Codex — writes evidence/agent_handoffs/HO-*.yaml
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent codex \
  --reason limit_reached \
  --repo-root .

# 3. Confirm the recommendation is unchanged (handoff doesn't advance it)
python scripts/agents/run_pipeline.py --mode operator-next-step --repo-root .

# 4. Accept the current task — writes evidence/operator_sessions/OP-*.yaml
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command yes \
  --repo-root .

# 5. Human performs the storyboard selection manually outside this tool.

# 6. Recommendation now advances to the next task (e.g. t2i_image_generation)
python scripts/agents/run_pipeline.py --mode operator-next-step --repo-root .

# 7. Switch to Gemini Code Assist for second opinion / pinch-hit
python scripts/agents/run_pipeline.py \
  --mode copilot-command \
  --command switch \
  --to-agent gemini_code_assist \
  --reason limit_reached \
  --repo-root .

# 8. View PR suggestion (print-only, does not call gh)
python scripts/agents/run_pipeline.py --mode suggest-pr --repo-root .
```

Expected evidence after this loop:

```text
evidence/agent_handoffs/HO-{ts1}.yaml   ← switch to Codex
evidence/agent_handoffs/HO-{ts2}.yaml   ← switch to Gemini Code Assist
evidence/operator_sessions/OP-{ts}.yaml ← yes (in_progress)
```

None of the above touch prompt records, scene cards, pack manifests,
`selected_take`, `video_takes`, `scene_clip_map`, `production_status.csv`,
or any lifecycle field. The automated equivalent of this transcript is
`tests/test_operator_loop_dryrun.py`.

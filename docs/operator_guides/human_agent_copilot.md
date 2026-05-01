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

HA-3a implements only `switch`. `yes`, `no`, and `revise` are reserved for a
later PR.

## Actors

| Actor | Can do | Must not do |
|---|---|---|
| `human_operator` | Approve work, run external tools manually, create PRs, promote lifecycle fields through review. | Store credentials in repo files or bypass PR review. |
| `claude_code` | Implement scoped batch work and write metadata-only files. | Promote lifecycle fields, commit binaries, or merge directly to main. |
| `codex` | Review, repair, validate, and implement scoped fixes on the same feature branch. | Create parallel permanent implementation branches or silently approve unsafe changes. |
| `gemini_code_assist` | Review Claude/Codex diffs, provide second opinions, and act as pinch-hitter implementor if both are unavailable. | Replace human approval or write credentials/API-driven automation. |
| `chatgpt_project` | Explore long-form context and draft prose outside the repo. | Write files directly to the repository. |

## Command Vocabulary

| Command | HA-3a behavior |
|---|---|
| `switch` | Writes `evidence/agent_handoffs/HO-*.yaml` from the current recommendation. |
| `yes` | Deferred to HA-3b; raises a clear not-implemented message. |
| `no` | Deferred to HA-3b; raises a clear not-implemented message. |
| `revise` | Deferred to HA-3b; raises a clear not-implemented message. |

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

## Safety Rules

- Metadata-only: no image, video, audio, proxy, or generated binary commits.
- Agents do not edit `pack_status`, `canon_lock`, `approved`, or `locked`.
- Agents do not promote lifecycle stages without a human PR.
- GitHub, Google Drive, and model credentials stay outside repo files.
- Google Drive storage is manual only; no Drive API is used by this layer.
- Auto-PR and auto-merge are out of scope for HA-3a.
- Handoff paths must be repo-relative POSIX-like paths with no absolute paths
  and no `..` traversal segments.

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

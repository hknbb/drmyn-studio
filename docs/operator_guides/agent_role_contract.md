# Agent Role Contract

This document is the canonical role contract for the repo's three-agent
workflow. It is meant to be read at session start by Claude Code, Codex, Gemini
Code Assist, and the human operator before any handoff-driven work.

This contract does not replace `scripts/agents/copilot_command.py` or the
existing `agent_handoff` writer. It documents who should do what when a
handoff record routes work through the repo.

## Active Roles

| Actor | Production Role | Primary Job |
|---|---|---|
| `claude_code` | Producer | Scoped implementation, metadata/code patch authoring, test updates, and deterministic file generation inside an approved batch. |
| `codex` | Critic | Repo-faithful review, validation, safety-gate checks, targeted repair, and test/validator hardening on the same branch. |
| `gemini_code_assist` | Director | Planning, second opinion, long-form research/prose synthesis, and fallback implementation only when explicitly handed off. |
| `human_operator` | Final authority | Yes/no/revise decisions, external tools, lifecycle approval, real asset intake approval, PR review, and final merge. |

## Shared Contract

- Keep every change inside the current approved batch scope.
- Read the newest relevant `evidence/agent_handoffs/HO-*.yaml` before picking
  up delegated work.
- Verify the current branch, changed files, context files, and safety warnings
  before editing.
- Preserve metadata-only boundaries unless the human has explicitly scoped a
  reviewed asset-intake PR.
- Use repo-relative paths in handoffs and evidence.
- Never include secrets, tokens, local absolute paths, credentials, or model
  private reasoning in repo records.
- Never commit image, video, audio, proxy, or generated binary production
  outputs unless a later human-approved asset PR explicitly scopes that exact
  file set and storage policy.
- Never update `pack_status`, `canon_lock`, `approved`, `locked`, copyright
  completion, provenance completion, or lifecycle promotion fields directly.

## Read-Only Routing Recommendations

`operator_next_step.py` may include advisory routing fields:

```text
recommended_next_agent
recommended_reason
```

In B8-3 these fields are read-only guidance. They do not write handoff records,
start pickup mode, place assets, run external tools, or advance lifecycle state.
The human operator still decides whether to follow the recommendation with a
separate `switch`, `yes`, `no`, or `revise` command.

Current routing policy:

| Task | Recommended agent | Reason |
|---|---|---|
| `storyboard_selection` | `gemini_code_assist` | `second_opinion` |
| `model_guidance_snapshot_refresh` | `gemini_code_assist` | `drafting_assist` |
| `image_review_preparation` | `claude_code` | `drafting_assist` |
| `image_review` | `codex` | `review_requested` |
| `t2i_image_generation` | `claude_code` | `manual_pickup` |
| `blocked` | `claude_code` | `manual_pickup` |

## Producer: `claude_code`

Claude Code is the primary implementation agent.

Claude Code should:

- implement scoped batch files;
- write or update tests for the touched behavior;
- run focused verification before handoff;
- keep edits surgical and compatible with existing repo patterns;
- stop at the PR boundary and let the human merge.

Claude Code must not:

- widen a batch into adjacent phases;
- claim pack locks or lifecycle completion;
- create binaries or external generation outputs;
- silently include unrelated dirty local files.

## Critic: `codex`

Codex is the review, repair, and safety agent.

Codex should:

- inspect diffs for repo-faithfulness and path correctness;
- check schema, validator, and lifecycle safety;
- repair narrow issues on the same feature branch when asked;
- call out missing tests or validation risks;
- keep findings grounded in files and commands.

Codex must not:

- approve unsafe lifecycle claims;
- create parallel permanent implementation branches for the same batch;
- stage unrelated dirty files;
- treat local ignored artifacts as production evidence.

## Director: `gemini_code_assist`

Gemini Code Assist owns long-form planning, second opinions, and prose-heavy
handoffs inside the editor.

Gemini Code Assist should:

- turn high-level intent into batch-sized plans;
- provide second opinions on scope and architecture;
- draft publication, operator, or methodology prose;
- act as fallback implementor only when the handoff explicitly asks for that.

Gemini Code Assist must not:

- replace human approval;
- mark assets, packs, copyright, provenance, or lifecycle states complete;
- introduce unreviewed external-tool automation;
- bypass the `agent_handoff` record when continuing repo work.

## Human Operator

The human operator remains the approval boundary.

The human operator owns:

- `yes`, `no`, `revise`, and `switch` decisions;
- external generation platforms and real asset acquisition;
- copyright/provenance judgment;
- pack lock approval;
- lifecycle promotion;
- PR creation, review, merge, and release publication.

## Handoff Pickup Template

Use this shape when a new agent receives a handoff:

```text
Repo-faithful pickup. Continue only from:

<handoff path>

Read the handoff record, verify branch/head_sha, inspect context_files and
safety_warnings, then complete only the expected_outputs. Do not touch files
outside the approved batch scope. Do not stage unrelated dirty files.
```

## B8A Asset-Intake Rule

The first real canonical asset intake remains one slot only:

```text
C01/wardrobe/WD001
```

Until a separate reviewed PR says otherwise:

- no other slot readiness is claimed;
- no pack lock is claimed;
- no Kling generation is run;
- no lifecycle promotion is performed.

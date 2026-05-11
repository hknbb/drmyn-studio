# AI Film Production Line Alignment

This document freezes the repository-facing interpretation of the external Midjourney, GPT Images, and Kling Omni production guides for DRMYN Studio.

It is an alignment document only. It does not introduce schemas, validators, generated media, lifecycle promotion, or new runtime behavior.

## 1. Scope

DRMYN Studio remains a metadata-only, schema-validated, human-gated movie development and production-process framework.

The production line described here governs records, references, prompt packages, QC reports, operator decisions, and reproducibility evidence. It does not store raw generated image, video, audio, proxy, or platform download binaries by default.

## 2. Canonical model chain

The canonical model chain is:

```text
screenplay / source truth
  ->
scene card
  ->
element brief
  ->
Midjourney hero reference
  ->
GPT Images four-perspective reference pack
  ->
Kling element reference record
  ->
shot_list_omni
  ->
Kling shot prompt record
  ->
external materialization
  ->
QC + operator decision
  ->
canon/archive metadata
```

The operational principle is:

```text
Midjourney decides what the element is.
GPT Images explains the element from multiple sides.
Kling Omni animates the locked reference pack.
```

## 3. Repository directory mapping

External guide terms must be translated into the repository's current directory contract:

| Production concept | Repository location |
|---|---|
| Source truth / screenplay span | `source/` |
| Scene cards, element sheets, dialogue records | `planning/` |
| Model-specific prompt records | `prompts/` |
| Candidate selections, storyboards, Omni set metadata | `visual_dev/` |
| Model snapshots, prompt runs, QC, operator sessions, handoffs | `evidence/` |
| JSON Schema contracts | `schemas/` |
| Validators and CLI entrypoints | `scripts/` |
| Human-facing method and operator doctrine | `docs/` |
| Future immutable approved metadata archive | `canon/` |

Generic folder names such as `preprod/`, `elements/`, `renders/`, and `qc/` are legacy guide vocabulary and must not be introduced as parallel permanent repository roots without a separate reviewed architecture change.

## 4. Lifecycle boundary

All model-facing records follow the repository lifecycle language:

```text
DRAFT -> REVIEW -> APPROVED -> LOCKED -> MATERIALIZED
```

Agents may draft metadata and evidence records within the allowed repository paths. Agents must not directly promote records to `APPROVED`, `LOCKED`, or canonical status. Those transitions require human PR review and an operator decision record.

## 5. Storage boundary

The repository stores:

- scene cards
- element briefs
- prompt records
- model guidance snapshots
- prompt run metadata
- image/video selection metadata
- QC reports
- operator sessions
- external storage references
- canonical metadata records

The repository does not store by default:

- raw platform downloads
- full Kling MP4 exports
- unmanaged image batches
- audio recordings
- proxy video binaries
- credentials, API keys, or secrets

Every output metadata record that points to generated media should expose at least:

```yaml
repo_binary_committed: false
external_storage_ref: null
platform_job_id: null
```

## 6. Alignment gates

### Midjourney gate

A Midjourney hero reference may proceed downstream only if it is clean enough to serve as the canonical element identity anchor.

Required record intent:

- element ID
- prompt ID
- selected candidate reference
- identity anchors
- material / palette anchors
- downstream-readiness note
- operator decision reference before lock

### GPT Images gate

A GPT Images perspective pack may proceed downstream only if it preserves the approved Midjourney reference across four controlled perspectives:

- front / hero
- three-quarter left
- three-quarter right
- rear / side / contextual continuity

The pack must not redesign the element. Failed perspectives return to revision without redefining the canonical element.

### Kling gate

A Kling shot prompt must not be generated from an ambiguous element description alone. It should reference a locked Kling element reference record, which itself points back to the Midjourney hero reference and GPT Images perspective pack.

For dialogue shots, the shot prompt must also reference dialogue extraction, performance intent, and Native Audio compatibility metadata before audio-enabled passes.

## 7. Immediate implementation bridge

This alignment prepares the next implementation batch:

```text
PROD-LINE-1: schema proposals for cross-model references and dialogue records
PROD-LINE-2: validator wiring for the new production-line record types
```

No schema or validator changes are made by this document.

# Scientific Clean Release Notes

**Release name:** `v0.1.4-drmyn-studio-citation-fix`  
**Date:** 2026-05-03  
**Branch:** `docs/fix-drmyn-studio-casing`

---

## What This Release Is

This release standardises the system name to **DRMYN Studio** and the
repository slug to `drmyn-studio` / `drmyn-studio-public`.
The *Closing Price* film project is the case study; DRMYN Studio is the system.
Repository URLs: `https://github.com/hknbb/drmyn-studio` (private) and
`https://github.com/hknbb/drmyn-studio-public` (public / Zenodo).

It is not a generated film. It is not a prompt library. It is the
**metadata-only production governance infrastructure** behind an AI-assisted
film pre-production workflow.

---

## What Changed in This Release (SCI-0 → SCI-3)

- `docs/publication/scientific_clean_release_manifest.md` — authoritative
  description of what is included, excluded, validated, and cited.
- `docs/publication/repository_hygiene_audit.md` — pre-publication hygiene
  audit confirming no binaries, no credentials, and no local artifact leakage.
- `docs/publication/reviewer_reproducibility_runbook.md` — step-by-step
  guide for independent reviewers to verify all claims.
- `README.md` — added scientific clean release / reviewer entrypoint section.
- `.gitignore` — added `.claude/settings.local.json` and `PR_BODY_*.md`.
- `.claude/settings.local.json` — removed from git tracking (machine-specific
  local paths, no credentials).

---

## Cumulative HA Layer History

| PR | Commit | Description |
|---|---|---|
| #9 | c6d6e4e | HA-0+1+3a: doctrine, handoff schema, switch command |
| #10 | 8d38019 | HA-2: storage URI conventions |
| #11 | 54ca208 | HA-2.5: model guidance refresh gate |
| #12 | 9604345 | HA-3b: yes/no/revise commands |
| #13 | 49e7f0b | HA-3c: print-only pr_helper |
| #14 | f6731a0 | HA-4a: read-only Streamlit dashboard |
| #15 | 84040ff | HA-4b-1: dashboard command buttons |
| #16 | 1339b94 | HA-4b-2: read-only review panels |
| #18 | f2538ab | HA-4c: dashboard PR suggestion panel |
| #19 | e47fcc7 | HA-5: local media index schema + validator |
| #20 | 29e037e | HA-6: end-to-end operator loop dry run |

---

## Validation Summary

```text
python -m pytest -q                → 328 passed
validate_production_records.py     → valid: 2, invalid: 0
validate_prompt_records.py         → 0 files
Binary files tracked               → NONE
Credentials tracked                → NONE
settings.local.json tracked        → REMOVED
```

---

## Tag History

| Tag | Commit | Notes |
|---|---|---|
| `v0.1.0-ha-complete-scientific-clean` | e4e1ef5 | Initial scientific clean release (HA-0→HA-6 + SCI-0→SCI-3) |
| `v0.1.1-ha-complete-scientific-clean` | e723561 | Patch: updated CITATION.cff and .zenodo.json; Dependabot workflow bump |
| `v0.1.2-drmyn-studio-scientific-clean` | c88b532 | Rename: DRMYN Studio system name (interim) |
| `v0.1.3-dramyn-studio-scientific-clean` | 733ef65 | Interim: Dramyn Studio name (typo); dramyn-studio slug |
| `v0.1.4-drmyn-studio-citation-fix` | current | Final: DRMYN Studio name; drmyn-studio slug; DOI added |

Zenodo concept DOI: `10.5281/zenodo.19987410` (always latest version).  
Zenodo version DOI: `10.5281/zenodo.19987411` (v0.1.4 record).

---

## Citation Files

- [CITATION.cff](../../CITATION.cff) — machine-readable citation (CFF format)
- [.zenodo.json](../../.zenodo.json) — Zenodo archive metadata

Verify both files are up to date with the current project title, authors, and
version before submitting to Zenodo.

---

## Next Phase

After this scientific clean release is tagged:

1. SCI-4 (optional): add `model_label` to `agent_handoff` schema for exact
   agent runtime version provenance.
2. Pilot production run: execute first full scene cycle
   (storyboard → prompt → image → video) and record evidence.
3. Review pilot evidence for completeness before article submission.

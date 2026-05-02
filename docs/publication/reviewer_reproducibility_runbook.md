# Reviewer Reproducibility Runbook

This document tells a journal reviewer or independent auditor exactly how to
set up the environment and verify the repository's claims.

---

## Environment Assumptions

- Python 3.11 or later
- Git with access to this repository
- No external model API credentials required
- No Google Drive access required
- No media binaries required (they are externally stored; references only)

Optional:
- `streamlit>=1.30` for the dashboard
- `gh` (GitHub CLI) for PR suggestions

---

## Install

```bash
git clone https://github.com/hknbb/NexusZeroClosingPriceProduction.git
cd NexusZeroClosingPriceProduction

# Minimal install (validators + tests)
pip install pyyaml jsonschema

# Full install
pip install -r requirements.txt
```

---

## Verification Steps

### Step 1 — Full test suite

```bash
python -m pytest -q
```

Expected: all tests pass, 0 failures, 0 errors.

All tests use `tmp_path` fixtures only. No test writes to `evidence/`,
`prompts/`, or any production directory. No test calls `gh`, hits a real API,
or requires network access.

### Step 2 — Production records validator

```bash
python scripts/validate_production_records.py --repo-root .
```

Expected:

```text
Production record validation: N files scanned.
  Valid:   N
  Invalid: 0
```

This validator checks all YAML production records against JSON Schema
(draft 2020-12) and enforces `FORBIDDEN_LIFECYCLE_KEYS`. An exit code of 0
confirms no schema violations, no lifecycle field promotion, and no binary
paths in evidence records.

### Step 3 — Prompt records validator

```bash
python scripts/validate_prompt_records.py --repo-root .
```

Expected: `0 files validated` until pilot production records are added.

### Step 4 — Phase 1 structural validator (optional)

```bash
python scripts/validate_phase1.py \
  --source-dir source \
  --planning-dir planning \
  --prompts-dir prompts \
  --schemas-dir schemas \
  --evidence-dir evidence \
  --report-json evidence/validation_reports/phase1_validation_report.json \
  --report-md evidence/validation_reports/phase1_validation_report.md
```

This validator checks scene cards, source refs, ID namespaces, and referential
integrity.

### Step 5 — Dry-run end-to-end test (optional detail)

```bash
python -m pytest tests/test_operator_loop_dryrun.py -v
```

This single test exercises the full human-agent copilot loop:
`recommend_next_step()` → `switch` → `yes` → storyboard advance →
`switch` again → `suggest_pr()`. It confirms that only allowed evidence
records are written and no binaries, lifecycle fields, or API calls are
involved.

### Step 6 — Dashboard (optional, requires Streamlit)

```bash
pip install streamlit>=1.30
python -m streamlit run tools/copilot_dashboard/app.py
```

Opens at `http://localhost:8501`. The dashboard is read-only by default
(`CP_UI_AUTO_PR` is not set). It displays the current recommendation,
production status, recent sessions, recent handoffs, and a print-only PR
suggestion. It does not execute `gh`, call external APIs, or write
production metadata when `CP_UI_AUTO_PR` is unset.

---

## What Output to Expect

| Command | Expected output |
|---|---|
| `pytest -q` | `N passed` (no failures) |
| `validate_production_records.py` | `valid: N, invalid: 0` |
| `validate_prompt_records.py` | `0 files validated` or `N passed` |
| `validate_phase1.py` | JSON + Markdown report in `evidence/validation_reports/` |
| `test_operator_loop_dryrun.py -v` | `1 passed` |

---

## What Is Intentionally Absent

| Absent item | Reason |
|---|---|
| Generated image candidates | External storage; `repo_binary_committed: false` |
| Generated video takes | External storage; platform refs in metadata |
| Pilot production prompt records | Not yet executed; post–scientific clean release |
| Live model API calls | All model usage is manual operator action |
| Google Drive sync | Manual only; no Drive API |
| GitHub token | Human-held; never in repo files |
| Auto-merge logic | All lifecycle promotion requires human PR |

---

## Known Limitations for Reviewers

1. Visual outputs (images, videos) cannot be reproduced from this repository
   alone. External storage access is required. The repository holds references
   and provenance records, not the media itself.
2. Agent model exact version (e.g. Claude Sonnet 4.6 vs Opus) is not yet
   formally recorded per evidence record. This is noted as a known limitation
   in the scientific clean release manifest.
3. Pilot production scenes are not yet recorded. The pipeline infrastructure
   is complete; the scientific contribution is the infrastructure itself.

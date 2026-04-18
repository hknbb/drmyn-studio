# Phase 2 — System Go-Live Checklist

Work through sections 1 → 14 in order. Do not move to production until all
items in section 14 are green.

---

## Canon hydration gate

Before any Omni migration or Phase 2 visual-structure expansion begins:

- [ ] Canon hydration queue reviewed
- [ ] Priority A source bibles completed
- [ ] Priority B core planning records completed
- [ ] Priority C pilot scene cards reviewed and canon-filled
- [ ] `make canon-queue` rerun and pilot review packets updated

> Omni migration must wait until canon hydration is complete enough that downstream
> structure can be reviewed without guessing.

---

## 1. Repo file structure

- [ ] `.github/ISSUE_TEMPLATE/` directory exists
- [ ] Issue form files present:
  - [ ] `config.yml`
  - [ ] `01-character-pack.yml`
  - [ ] `02-location-sheet.yml`
  - [ ] `03-still-set.yml`
  - [ ] `04-motion-pair.yml`
  - [ ] `05-evidence-panel.yml`
  - [ ] `06-visual-freeze.yml`
  - [ ] `07-general-visual-task.yml`
- [ ] `.github/workflows/` files present:
  - [ ] `validate-phase1.yml`
  - [ ] `freeze-canon.yml`
  - [ ] `release-artifact.yml`
  - [ ] `phase2-taxonomy-bootstrap.yml`
  - [ ] `phase2-project-sync.yml`
  - [ ] `phase2-label-guard.yml`
- [ ] `schemas/`, `scripts/`, `planning/`, `prompts/`, `evidence/`, `visual_dev/` all present
- [ ] Latest changes committed on a feature branch

## 2. Repo smoke test

Run locally — all three commands must exit 0:

```bash
python scripts/validate_phase1.py \
  --source-dir source --planning-dir planning --prompts-dir prompts \
  --schemas-dir schemas --evidence-dir evidence \
  --report-json evidence/validation_reports/phase1_validation_report.json \
  --report-md  evidence/validation_reports/phase1_validation_report.md

python scripts/check_referential_integrity.py \
  --planning-dir planning --prompts-dir prompts \
  --output evidence/validation_reports/referential_integrity_report.json

python scripts/build_manifests.py \
  --planning-dir planning --output-dir planning/manifests
```

Optional freeze dry-run:

```bash
python scripts/freeze_canon.py \
  --source-dir source --planning-dir planning --prompts-dir prompts \
  --schemas-dir schemas --evidence-dir evidence --tag dryrun-z1p1
```

- [ ] `validate_phase1.py` → 0 errors, 0 warnings
- [ ] `check_referential_integrity.py` → 0 errors, 0 warnings
- [ ] `build_manifests.py` → manifests rebuilt without error
- [ ] (optional) `freeze_canon.py` dry-run → no errors

## 3. GitHub repo settings

- [ ] Branch pushed to GitHub
- [ ] `main` set as protected branch
- [ ] PR review required
- [ ] Status checks required (validate-phase1 workflow)
- [ ] Force push disabled
- [ ] CODEOWNERS active (if applicable)

## 4. Secrets and Variables

In **Settings → Secrets and variables → Actions**:

- [ ] Secret added: `PROJECT_TOKEN` (classic PAT with `project` + `repo` scopes)
- [ ] Variable added: `PHASE2_PROJECT_OWNER` (GitHub username or org login)
- [ ] Variable added: `PHASE2_PROJECT_NUMBER` (integer from Project URL)

## 5. Phase 2 Project created

- [ ] Project created: **Closing Price — Phase 2 Visual Development**
- [ ] Custom fields created (see section 6 for exact option values):
  - [ ] `Asset Type` (single select)
  - [ ] `Batch` (single select)
  - [ ] `Article 3 Evidence` (single select)
  - [ ] `Motion Ready` (single select)
  - [ ] `Scene ID` (text)
  - [ ] `Character ID` (text)
  - [ ] `Location ID` (text)
  - [ ] `Target Freeze` (text)
  - [ ] `Due Date` (date)
- [ ] Built-in `Status` field in use
- [ ] Views created:
  - [ ] Table (Master Asset Table)
  - [ ] Board (Production Board)
  - [ ] Roadmap (Batch Roadmap)

## 6. Field option standard

**`phase2-project-sync.yml` matches against these exact strings — spelling must be identical.**

`Asset Type` options:
- [ ] Character Pack
- [ ] Location Sheet
- [ ] Prop Pack
- [ ] Wardrobe Pack
- [ ] Still Set
- [ ] Motion Pair
- [ ] Evidence Panel

`Batch` options:
- [ ] Batch 01
- [ ] Batch 02
- [ ] Batch 03

`Article 3 Evidence` options:
- [ ] No
- [ ] Candidate
- [ ] Approved

`Motion Ready` options:
- [ ] No
- [ ] Start Only
- [ ] End Only
- [ ] Paired

## 7. Built-in Project automations

In the Project's workflow/automation panel:

- [ ] Auto-add workflow enabled
- [ ] Auto-add filter: `is:issue label:phase-2`
- [ ] Automation: Item added to project → Status = Backlog
- [ ] Automation: Item closed → Status = Done

> Note: built-in auto-add only catches new or updated items after activation.
> Pre-existing matching issues must be backfilled manually or via the sync workflow.

## 8. Taxonomy bootstrap

- [ ] `Phase 2 Taxonomy Bootstrap` workflow run manually (Actions → Run workflow)
- [ ] Labels created:
  - [ ] `phase-2`
  - [ ] `phase-2-visual-dev`
  - [ ] `phase-2-motion-prep`
  - [ ] `asset-character`
  - [ ] `asset-location`
  - [ ] `asset-prop`
  - [ ] `asset-wardrobe`
  - [ ] `asset-still`
  - [ ] `asset-motion-pair`
  - [ ] `asset-evidence`
  - [ ] `review-needed`
  - [ ] `article3-evidence`
  - [ ] `freeze-candidate`
  - [ ] `blocked`
  - [ ] `continuity-risk`
  - [ ] `depends-on`
  - [ ] `task`
  - [ ] `enhancement`
  - [ ] `documentation`
  - [ ] `pipeline`
  - [ ] `qa`
- [ ] Milestones created:
  - [ ] `P2-Batch-01 Reference Packs`
  - [ ] `P2-Batch-01 Scene Stills`
  - [ ] `P2-Batch-01 Motion Prep`
  - [ ] `P2-Batch-01 Freeze`

## 9. Issue forms test

- [ ] New issue chooser screen appears (not a blank text box)
- [ ] Character Pack form opens and renders fields
- [ ] Still Set form opens and renders fields
- [ ] Motion Pair form opens and renders fields
- [ ] Visual Freeze form opens and renders checkboxes
- [ ] `blank_issues_enabled: false` in effect (no blank option in chooser)

## 10. First 10 issues opened

Using `docs/github/PHASE2_FIRST10_ISSUES.md` as reference:

- [ ] All 10 issues created via issue forms
- [ ] All have `phase-2` label
- [ ] Each has the correct asset label
- [ ] Each is assigned to a milestone
- [ ] Title format standard: `[P2][Asset Type] Description`

## 11. Project sync smoke test

After opening a new `phase-2` issue:

- [ ] Issue appears in Project automatically
- [ ] `Status` = Backlog
- [ ] `Asset Type` populated
- [ ] `Batch` populated
- [ ] `Article 3 Evidence` populated
- [ ] `Motion Ready` populated
- [ ] `Target Freeze` populated
- [ ] `Scene ID` / `Character ID` / `Location ID` populated where present in title

## 12. Label guard smoke test

Open a second test issue intentionally incomplete (no asset label, no milestone):

- [ ] `blocked` label added automatically
- [ ] Warning comment posted about missing asset label
- [ ] Warning comment posted about missing milestone
- [ ] `review-needed` added automatically

Clean up the test issue after verifying.

## 13. CI and permission check

- [ ] All three Phase 2 workflow files use `permissions:` with minimum required scopes
- [ ] Repo default `GITHUB_TOKEN` permission is not wider than `read`
- [ ] `PROJECT_TOKEN` scoped to only `project` + `repo` — no other scopes

## 14. Go / No-go gate

Do not proceed to production unless all 8 items below are green:

| Item | Status |
|------|--------|
| Issue forms working | |
| Taxonomy bootstrap passed | |
| Project fields correct (exact option names) | |
| Auto-add working | |
| Project sync populating fields | |
| Label guard catching missing labels/milestones | |
| Validation scripts clean (0 errors) | |
| First 10 issues live and visible in Project | |

**Go** — all 8 green → proceed to Phase 2 production work.
**No-go** — any item red → fix before proceeding.

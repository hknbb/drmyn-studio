# Apply Phase 2 Changes to Local Repository (Windows)

This guide explains how to apply the Phase 2 scaffolding to your local
repository and push it to GitHub.

## Prerequisites

- Git installed (git.scm.com)
- Repository cloned at `C:\Users\babac\NexusZeroClosingPriceProduction`
- GitHub remote configured

## Step 1 — Create a feature branch

```powershell
cd "C:\Users\babac\NexusZeroClosingPriceProduction"
git checkout -b phase-2-scaffold
```

## Step 2 — Stage new files

```powershell
git add .github/ISSUE_TEMPLATE/config.yml
git add .github/ISSUE_TEMPLATE/01-character-pack.yml
git add .github/ISSUE_TEMPLATE/02-location-sheet.yml
git add .github/ISSUE_TEMPLATE/03-still-set.yml
git add .github/ISSUE_TEMPLATE/04-motion-pair.yml
git add .github/ISSUE_TEMPLATE/05-evidence-panel.yml
git add .github/ISSUE_TEMPLATE/06-visual-freeze.yml
git add .github/ISSUE_TEMPLATE/07-general-visual-task.yml
git add visual_dev/
git add evidence/panels evidence/contact_sheets evidence/selection_logs evidence/comparative_sets evidence/article3
git add docs/github/
git add planning/characters/C02.yaml planning/characters/C03.yaml planning/characters/C05.yaml
git add planning/locations/LOC002.yaml planning/locations/LOC003.yaml planning/locations/LOC004.yaml
git add planning/scenes/SC0003/ planning/scenes/SC0006/ planning/scenes/SC0008/ planning/scenes/SC0009/
```

## Step 3 — Commit

```powershell
git commit -m "Add Phase 2 Visual Development scaffold

- 7 GitHub issue form YAML templates (01-07) + config.yml
- visual_dev/ tree: characters C01-C05, locations LOC001-LOC004,
  props, wardrobe, stills and motion_prep for pilot batch scenes
- evidence/ expanded: panels, contact_sheets, selection_logs,
  comparative_sets, article3
- docs/github/ Phase 2 field set, first 10 issues, seed CSV, this guide
- planning records: C02, C03, C05, LOC002, LOC003, LOC004,
  SC0003, SC0006, SC0008, SC0009"
```

## Step 4 — Push and open PR

```powershell
git push -u origin phase-2-scaffold
```

Then open a pull request on GitHub targeting `main` (or `develop`).

## Step 5 — Set up GitHub Project

1. Go to your repository on GitHub.
2. Click **Projects** → **New project** → **Table**.
3. Name it: `Closing Price — Phase 2 Visual Development`.
4. Add custom fields as listed in `docs/github/PHASE2_PROJECT_FIELD_SET.md`.
5. Add labels listed in the same file (Settings → Labels → New label).
6. Create milestones listed in the same file (Issues → Milestones → New milestone).

## Step 6 — Open first 10 issues

1. Click **Issues** → **New issue**.
2. Select the relevant template from the chooser.
3. Fill in the pre-populated fields using `docs/github/PHASE2_FIRST10_ISSUES.md` as reference.
4. Submit, then add the issue to the Project and set custom fields.

## Step 7 — Seed CSV (optional)

`docs/github/PHASE2_PROJECT_SEED.csv` contains all 31 Batch 01 items as a
planning sheet. Use it in Excel or Google Sheets for offline planning, or as
a reference when opening issues manually.

To import into GitHub Projects programmatically, use the GitHub GraphQL API
or the `gh` CLI extension `gh-project`.

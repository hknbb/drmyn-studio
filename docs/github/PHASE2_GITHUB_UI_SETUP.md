# Phase 2 — GitHub UI Setup Guide

Step-by-step instructions for configuring GitHub after pushing the repo.
Assumes local files are already committed and pushed to GitHub.

---

## Step 1 — Open repo Settings

On GitHub, open the repository. In the top navigation bar click **Settings**.
(If Settings is not visible, use the `…` overflow menu.)

## Step 2 — Verify issue forms are active

Go to the repo main page. Click **Issues → New issue**.

You should see an **issue chooser** screen listing all template forms. If you
see only a blank text editor, the `.github/ISSUE_TEMPLATE/` files did not push
correctly.

Confirm these forms appear:
- Phase 2 — Character Pack
- Phase 2 — Location Sheet
- Phase 2 — Still Set
- Phase 2 — Motion Pair
- Phase 2 — Evidence Panel
- Phase 2 — Visual Freeze
- Phase 2 — General Visual Task

The chooser should **not** show a "blank issue" option (`blank_issues_enabled: false`
in `config.yml`).

## Step 3 — Create the Phase 2 Project

1. Click your profile photo (top right) → **Your profile** → **Projects**
   (for a personal repo).
   For an organization repo: **Organizations → [org name] → Projects**.
2. Click **New project**.
3. Select **Table** as the starting layout.
4. Name it: **Closing Price — Phase 2 Visual Development**
5. Click **Create**.

## Step 4 — Add custom fields

In the Project's Table view, click the **+** at the far right of the column
headers → **New field**.

Create the following fields in order:

### Single select fields

For each one: select type **Single select**, enter the name, then add options.

| Field name | Options (in order) |
|------------|-------------------|
| `Asset Type` | Character Pack / Location Sheet / Prop Pack / Wardrobe Pack / Still Set / Motion Pair / Evidence Panel |
| `Batch` | Batch 01 / Batch 02 / Batch 03 |
| `Article 3 Evidence` | No / Candidate / Approved |
| `Motion Ready` | No / Start Only / End Only / Paired |

> **Critical:** option names must match exactly — `phase2-project-sync.yml`
> looks these up by string. A typo means the field will not be populated.

### Text fields

Type **Text**, one field each:
- `Scene ID`
- `Character ID`
- `Location ID`
- `Target Freeze`

### Date field

Type **Date**: `Due Date`

## Step 5 — Add Board and Roadmap views

Inside the Project, click **+ New view** (tab bar at the top):

1. Add a **Board** view → name it `Production Board`
   → group by `Status` (Lifecycle column)
2. Add a **Roadmap** view → name it `Batch Roadmap`
   → set date field to `Due Date`, group by Milestone

Rename the default table view to `Master Asset Table`.

Optional additional views (filter-based):
- `Article 3 Evidence` — filter: Article 3 Evidence = Candidate or Approved
- `Motion Prep Queue` — filter: Asset Type = Motion Pair
- `Freeze Candidates` — filter: Labels includes freeze-candidate

## Step 6 — Enable built-in auto-add automation

Inside the Project click the **…** menu (top right) → **Workflows** (or
**Settings → Workflows** depending on GitHub version).

1. Find **Auto-add to project** and click to configure it.
2. Set the filter:
   ```
   is:issue label:phase-2
   ```
3. Save / enable.

> Built-in auto-add only picks up **new or updated** items after activation.
> Issues that already exist before this is enabled will not be backfilled
> automatically — add them manually or reopen/relabel them to trigger the
> filter.

## Step 7 — Enable built-in status automations

In the same Workflows panel, enable:

- **Item added to project** → set Status = `Backlog`
- **Item closed** → set Status = `Done`

## Step 8 — Add repo secret and variables

Go to **Settings → Secrets and variables → Actions**.

### Secret

Click **New repository secret**:

| Name | Value |
|------|-------|
| `PROJECT_TOKEN` | A GitHub classic PAT with scopes: `project`, `repo` |

### Variables

Click **Variables** tab → **New repository variable**:

| Name | Value |
|------|-------|
| `PHASE2_PROJECT_OWNER` | Your GitHub username or org login |
| `PHASE2_PROJECT_NUMBER` | Integer from Project URL (e.g. if URL ends `/projects/3`, enter `3`) |

## Step 9 — Confirm workflows appear in Actions

Click the **Actions** tab on the repo. You should see these three workflows
listed on the left:

- Phase 2 Taxonomy Bootstrap
- Phase 2 Project Sync
- Phase 2 Label Guard

If they are not listed, the workflow files are not on the default branch or
contain a syntax error.

## Step 10 — Run Taxonomy Bootstrap (once)

1. Actions → **Phase 2 Taxonomy Bootstrap**
2. Click **Run workflow** → **Run workflow** (confirm)
3. Watch the run complete.

After it finishes, verify in **Issues → Labels**:

`phase-2`, `phase-2-visual-dev`, `phase-2-motion-prep`, `asset-character`,
`asset-location`, `asset-prop`, `asset-wardrobe`, `asset-still`,
`asset-motion-pair`, `asset-evidence`,
`review-needed`, `article3-evidence`, `freeze-candidate`, `blocked`,
`continuity-risk`, `depends-on`, `task`, `enhancement`, `documentation`,
`pipeline`, `qa`

Verify in **Issues → Milestones**:

`P2-Batch-01 Reference Packs`, `P2-Batch-01 Scene Stills`,
`P2-Batch-01 Motion Prep`, `P2-Batch-01 Freeze`

## Step 11 — Open the first test issue

1. Issues → **New issue**
2. Select **Phase 2 — Character Pack**
3. Fill in: Character ID = `C01`, Display name = `Nadia`, Batch = `Batch 01`,
   Tool = `Midjourney`, required outputs, output paths, review criteria,
   Evidence = `Candidate`, Freeze = `visual-z1p2-batch1-r1`
4. Submit

Verify:
- Issue created with `phase-2`, `asset-character`, `review-needed` labels
- Milestone can be set to `P2-Batch-01 Reference Packs`
- Form body rendered as structured markdown

## Step 12 — Check Project auto-add

Switch to the Project view. The issue from Step 11 should appear automatically
(within ~30 seconds of auto-add firing).

Verify:
- Item appears in the Table / Board
- `Status` = Backlog
- Board view shows item in Backlog column

## Step 13 — Check Project Sync field population

In the Project table, click the row for the issue from Step 11 and verify:

| Field | Expected value |
|-------|---------------|
| Asset Type | Character Pack |
| Batch | Batch 01 |
| Article 3 Evidence | Candidate |
| Motion Ready | No |
| Character ID | C01 |
| Target Freeze | visual-z1p2-batch1-r1 |

If fields are blank: check that the `PROJECT_TOKEN` secret, `PHASE2_PROJECT_OWNER`
and `PHASE2_PROJECT_NUMBER` variables are set correctly, and that the Project
field names match exactly.

## Step 14 — Run Label Guard smoke test

1. Open a second test issue using **General Visual Task** form.
2. Do **not** add an asset label (`asset-*`).
3. Do **not** assign a milestone.
4. Submit the issue.

Within ~30 seconds, Label Guard should:
- Add `blocked` label
- Post a comment listing the required asset labels
- Post a comment about the missing milestone
- Add `review-needed` label

After confirming the behaviour, close and delete the test issue.

## Step 15 — Final acceptance check

The system is ready for Phase 2 production work when all of the following are true:

- [ ] Issue forms render correctly in chooser
- [ ] Project exists with all custom fields and correct option names
- [ ] Built-in auto-add is active with `is:issue label:phase-2`
- [ ] Taxonomy Bootstrap completed: all labels and milestones exist
- [ ] Project Sync populates Asset Type, Batch, Evidence, Motion Ready, IDs, Freeze
- [ ] Label Guard adds `blocked` and posts comment on taxonomy violations
- [ ] Validation scripts pass locally (0 errors, 0 warnings)
- [ ] First 10 issues opened and visible in Project

**Once all boxes are checked: proceed to Phase 2 Batch 01 production work.**

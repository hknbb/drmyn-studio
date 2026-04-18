# Phase 2 GitHub Project — Field Set

Project name: **Closing Price — Phase 2 Visual Development**

## Built-in fields (always present)
| Field | Notes |
|-------|-------|
| Title | Issue / draft title |
| Assignees | Owner of the task |
| Labels | See label set below |
| Milestone | See milestone set below |
| Repository | NexusZeroClosingPriceProduction |
| Linked pull requests | Auto-linked from PRs |

## Custom fields

| # | Field Name | Type | Values |
|---|-----------|------|--------|
| 1 | Asset Type | Single select | Character Pack / Location Sheet / Prop Pack / Wardrobe Pack / Still Set / Motion Pair / Evidence Panel |
| 2 | Batch | Single select | Batch 01 / Batch 02 / Batch 03 |
| 3 | Article 3 Evidence | Single select | No / Candidate / Approved |
| 4 | Motion Ready | Single select | No / Start Only / End Only / Paired |
| 5 | Scene ID | Text | SC0001, SC0003, SC0006, SC0008, SC0009 … |
| 6 | Character ID | Text | C01, C02, C03, C04, C05 … |
| 7 | Location ID | Text | LOC001, LOC002, LOC003, LOC004 … |
| 8 | Target Freeze | Text | visual-z1p2-batch1-r1 |
| 9 | Due Date | Date | — |

## Views

| View Name | Type | Group / Sort |
|-----------|------|-------------|
| Master Asset Table | Table | Sort by Milestone, Asset Type |
| Production Board | Board | Group by Status |
| Batch Roadmap | Roadmap | By Due Date, grouped by Milestone |
| Article 3 Evidence | Table | Filter: Article 3 Evidence = Candidate or Approved |
| Motion Prep Queue | Table | Filter: Asset Type = Motion Pair |
| Freeze Candidates | Table | Filter: Labels includes freeze-candidate |

## Label set

**Phase labels**
- `phase-2`
- `phase-2-visual-dev`
- `phase-2-motion-prep`

**Asset labels**
- `asset-character`
- `asset-location`
- `asset-prop`
- `asset-wardrobe`
- `asset-still`
- `asset-motion-pair`
- `asset-evidence`

**Risk / review labels**
- `continuity-risk`
- `review-needed`
- `freeze-candidate`
- `article3-evidence`
- `blocked`
- `depends-on`

**Work type labels**
- `task`
- `enhancement`
- `documentation`
- `pipeline`
- `qa`

## Milestones

| Milestone | Purpose |
|-----------|---------|
| P2-Batch-01 Reference Packs | Character, location, prop, wardrobe packs |
| P2-Batch-01 Scene Stills | Still sets for SC0001, SC0003, SC0006, SC0008, SC0009 |
| P2-Batch-01 Motion Prep | Motion-ready frame pairs for all 5 pilot scenes |
| P2-Batch-01 Freeze | visual-z1p2-batch1-r1 freeze and evidence export |
| P2-Batch-02 Expansion | (open after Batch 01 freeze) |
| P2-Final Freeze | Phase 2 complete freeze |

Open only the first four milestones initially.

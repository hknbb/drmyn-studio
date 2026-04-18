# Naming Conventions

## Stable identifiers

| Entity | Format | Example |
|--------|--------|---------|
| Scene | `SC0001` | `SC0042` |
| Character | `C01` | `C12` |
| Sequence | `SEQ01` | `SEQ03` |
| Location | `LOC001` | `LOC007` |
| Prop | `PROP001` | `PROP024` |
| Wardrobe | `WD001` | `WD015` |

## Prompt record file naming

Format: `SC0001__[descriptor]__v01.md`

Rules:
- Double underscore (`__`) as the only separator between segments
- Lowercase and hyphens in the descriptor
- No spaces anywhere
- No renaming after approval

Examples:
- `SC0001__char-nadia__v01.md`
- `SC0001__env-office-night__v02.md`
- `SC0006__surveillance-discovery__v03.md`

## Prompt lifecycle folders

| Folder | Meaning |
|--------|---------|
| `draft/` | Work in progress, not reviewed |
| `review/` | Submitted for review |
| `approved/` | Approved for production use |
| `locked/` | Frozen, no further changes |

## File extension rules

| Content type | Extension |
|-------------|-----------|
| Human-readable plan/narrative | `.md` |
| Structured records | `.yaml` |
| JSON Schemas | `.schema.json` |
| Manifests | `.csv` |
| Automation output | `.json` |

## Branch naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feat/z1p1-<topic>` | `feat/z1p1-scene-cards` |
| Fix | `fix/z1p1-<topic>` | `fix/z1p1-continuity-links` |
| Docs | `docs/z1p1-<topic>` | `docs/z1p1-naming-policy` |
| Experiment | `exp/z1p1-<topic>` | `exp/z1p1-prompt-sc0006` |

## Commit message format

`type(z1p1): short imperative description`

Examples:
- `feat(z1p1): add scene cards SC0001–SC0010`
- `fix(z1p1): repair continuity refs for wardrobe WD001`
- `docs(z1p1): update prompt versioning policy`

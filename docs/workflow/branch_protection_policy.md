# Branch Protection Policy

## Base branches

### `main`
Protected. Release-ready only. No direct commits.

### `develop`
Optional integration branch. May be protected in larger team settings.

## Rules for `main`

The following settings must be enabled in GitHub repository Settings → Branches → Branch protection rules:

- **Require a pull request before merging** — ON
- **Require approvals** — minimum 1
- **Require conversation resolution before merging** — ON
- **Require status checks to pass before merging** — ON
  - Required check: `Validate Zone 1 Phase 1 / Validate Phase 1 planning records`
- **Require branches to be up to date before merging** — ON
- **Require review from Code Owners** — ON (if CODEOWNERS is configured)
- **Allow force pushes** — OFF
- **Allow deletions** — OFF

## Allowed merge strategy

Squash merge preferred. This keeps `main` history clean and makes each PR a single auditable unit.

## Tagging convention

| Tag pattern | Purpose |
|-------------|---------|
| `canon-z1p1-r1` | First canonical freeze of Zone 1 Phase 1 |
| `canon-z1p1-r2` | Second freeze (after corrections) |

Tags trigger the `release-artifact.yml` workflow automatically.

## Rationale

The `main` branch functions as the canonical GitHub-backed source of approved Phase 1 records. Silent canon drift — where records change without review — is the primary risk in this phase, not creative velocity.

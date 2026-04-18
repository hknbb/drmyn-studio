# Review Policy

## Who reviews what

Defined in `.github/CODEOWNERS`. Update CODEOWNERS when team membership changes.

## PR review requirements

1. At least **1 approving review** before merge.
2. All CI checks must pass (`validate-phase1` workflow).
3. All open PR conversations must be resolved.
4. Canon-locked record changes require explicit rationale in the PR body.

## Review focus areas

When reviewing a Zone 1 / Phase 1 PR:

1. **Canon integrity** — do new records break existing references?
2. **Schema compliance** — do YAML records match their schemas?
3. **ID consistency** — are IDs from the established namespace?
4. **Prompt governance** — are prompt files in the correct lifecycle folder?
5. **Continuity logic** — do prior/next scene links make narrative sense?
6. **Evidence trace** — are publication-relevant records flagged?

## Canon change requests

Any change to `source/` files or canon-locked records must be accompanied by a GitHub Issue using the `[CANON]` template before a PR is opened.

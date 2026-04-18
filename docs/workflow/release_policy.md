# Release Policy

## When to release

A GitHub Release should be created when:

1. A significant set of Phase 1 records has been approved and merged.
2. The project reaches a "canon freeze" milestone.
3. Preparation for article submission begins.

## Release procedure

1. Run full validation locally: `make all`
2. Rebuild manifests: `make manifests`
3. Commit and merge manifests via PR.
4. Trigger `freeze-canon.yml` workflow via `workflow_dispatch` with the release tag.
5. Create a git tag: `git tag canon-z1p1-r1`
6. Push the tag: `git push origin canon-z1p1-r1`
7. The `release-artifact.yml` workflow runs automatically and attaches the artifact bundle.
8. Optionally, trigger the Zenodo archive via the Zenodo GitHub integration.

## Release assets

Each release should include:
- `closing-price-phase1-artifact-bundle.zip`
- Release notes listing which scenes, prompt packages, and canon version were frozen

## Zenodo archiving

Once Zenodo GitHub integration is enabled:
- Each release is automatically archived.
- The DOI is added to `CITATION.cff` and `.zenodo.json`.
- Metadata in `.zenodo.json` overrides auto-generated Zenodo metadata.

# Data Management Plan

## Data types

| Type | Format | Location | Access |
|------|--------|----------|--------|
| Canonical source | Markdown | `source/` | Public (if repo is public) |
| Planning records | YAML | `planning/` | Public |
| Prompt records | YAML/MD | `prompts/` | Public |
| Schemas | JSON | `schemas/` | Public |
| Manifests | CSV | `planning/manifests/` | Public |
| Evidence maps | CSV | `evidence/` | Public |
| Artifact bundles | ZIP | GitHub Release / Zenodo | Public |
| Generated assets | Image/video | External (not in repo) | Controlled by external storage/provider policy |

## Storage and backup

- Primary: GitHub repository
- Archive: Zenodo (tagged releases)
- Local: researcher's machine (git clone)

## Sensitive data

This repository does not contain personal data or sensitive information. All records are project-internal production planning data.

## Retention

GitHub releases and Zenodo archives are permanent. Validation artifacts have a 14-day GitHub Actions retention; release bundles are permanent.

## Access and sharing

Repository metadata, planning records, schemas, manifests, and validation outputs
are intended for open access publication. Generated image/video assets are
stored outside this repository and may be shared separately according to the
relevant production, platform, or publication constraints.

## License

MIT — see `LICENSE` in the repository root.

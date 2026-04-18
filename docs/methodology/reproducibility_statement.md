# Reproducibility Statement

## Claim

The Zone 1 / Phase 1 workflow is designed to be reproducible: given the same canonical source files and schema versions, the validation pipeline will produce the same validation reports and manifest outputs deterministically.

## What is reproducible

- Schema validation results (given the same schemas and planning records)
- Manifest outputs (given the same planning records)
- Canon freeze manifests (SHA-256 hashes of included files at freeze time)
- CI validation reports (stored as GitHub Actions artifacts)

## What is not deterministic

- Generated still images and video clips (downstream, non-Phase-1)
- LLM critique outputs (downstream)
- Human review decisions

## Verification procedure

1. Clone the repository at a specific tagged release.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `make all`
4. Compare output reports to archived validation artifacts from the same release.

## Artifact integrity

Canon freeze bundles include a `bundle_sha256.txt` file. Verify with:

```bash
sha256sum -c evidence/provenance/<tag>/bundle_sha256.txt
```

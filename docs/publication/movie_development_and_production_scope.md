# Scope: Movie Development and Movie Production Process

DRMYN Studio is a metadata-only, schema-validated, human-gated research software framework for AI-assisted movie development and movie production process design, documentation, validation, and reproducibility.

## Scope

The repository supports:

- movie development process modeling
- pre-production planning
- movie production process governance
- prompt lifecycle management
- human-agent workflow documentation
- schema-validated metadata records
- reproducibility evidence
- release-ready scientific documentation

## Not a screenplay-only system

This repository is not limited to screenplay generation. Screenplay-related files, when present, are treated as one source component within a broader movie development process. The `source/screenplay/` directory contains canonical Fountain script files as part of the development source package; they do not represent the full scope of the system.

## Metadata-only doctrine

Generated image, video, audio, and post-production binaries are not stored as canonical repository assets. The repository stores metadata, references, validation records, human decisions, and reproducibility artifacts. All generated media outputs are stored externally and referenced through metadata-only records using URI conventions (`local://`, `gdrive://`, `kling://`).

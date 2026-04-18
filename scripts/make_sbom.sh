#!/usr/bin/env bash
# Generate a placeholder SBOM for the Phase 1 repository.
# For production use, replace with a proper SBOM generator (e.g. Syft, CycloneDX, or GitHub's dependency graph export).

set -euo pipefail

OUTPUT_DIR="${1:-evidence/provenance}"
mkdir -p "$OUTPUT_DIR"

cat > "$OUTPUT_DIR/sbom.json" <<EOF
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "version": 1,
  "metadata": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "component": {
      "type": "application",
      "name": "closing-price-phase1",
      "version": "0.1.0"
    }
  },
  "components": [],
  "note": "Placeholder SBOM. Replace with output from a real SBOM generator."
}
EOF

echo "SBOM written to $OUTPUT_DIR/sbom.json"

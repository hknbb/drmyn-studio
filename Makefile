.PHONY: validate manifests integrity freeze export help numbered-fountain seed-scenes hydrate-scenes canon-queue closure-audit

PYTHON := python
SOURCE_DIR := source
PLANNING_DIR := planning
PROMPTS_DIR := prompts
SCHEMAS_DIR := schemas
EVIDENCE_DIR := evidence
REPORT_JSON := evidence/validation_reports/phase1_validation_report.json
REPORT_MD := evidence/validation_reports/phase1_validation_report.md
INTEGRITY_JSON := evidence/validation_reports/referential_integrity_report.json
MANIFESTS_DIR := planning/manifests

help:
	@echo "Available targets:"
	@echo "  validate    Run Phase 1 schema and lifecycle validation"
	@echo "  integrity   Run referential integrity check"
	@echo "  manifests   Rebuild CSV manifests from planning records"
	@echo "  numbered-fountain  Build source/screenplay/closing_price.numbered.fountain"
	@echo "  seed-scenes        Scaffold planning/scenes/ from the retrieval-map spine"
	@echo "  hydrate-scenes     Ground scene cards and prompt briefs from spine/excerpts"
	@echo "  canon-queue        Build canon hydration queue reports and pilot review packets"
	@echo "  freeze TAG= Freeze canon with given tag (e.g. make freeze TAG=canon-z1p1-r1)"
	@echo "  closure-audit      Stage A placeholder audit (live files only)"
	@echo "  all         validate + integrity + manifests"

validate:
	@mkdir -p $(EVIDENCE_DIR)/validation_reports
	$(PYTHON) scripts/validate_phase1.py \
		--source-dir $(SOURCE_DIR) \
		--planning-dir $(PLANNING_DIR) \
		--prompts-dir $(PROMPTS_DIR) \
		--schemas-dir $(SCHEMAS_DIR) \
		--evidence-dir $(EVIDENCE_DIR) \
		--report-json $(REPORT_JSON) \
		--report-md $(REPORT_MD)

integrity:
	@mkdir -p $(EVIDENCE_DIR)/validation_reports
	$(PYTHON) scripts/check_referential_integrity.py \
		--planning-dir $(PLANNING_DIR) \
		--prompts-dir $(PROMPTS_DIR) \
		--output $(INTEGRITY_JSON)

manifests:
	$(PYTHON) scripts/build_manifests.py \
		--planning-dir $(PLANNING_DIR) \
		--output-dir $(MANIFESTS_DIR)

numbered-fountain:
	$(PYTHON) scripts/build_numbered_fountain.py \
		--source $(SOURCE_DIR)/screenplay/closing_price.fountain \
		--retrieval-map $(MANIFESTS_DIR)/closing_price_scene_retrieval_map.json \
		--output $(SOURCE_DIR)/screenplay/closing_price.numbered.fountain

seed-scenes:
	$(PYTHON) scripts/seed_scene_cards.py \
		--source $(SOURCE_DIR)/screenplay/closing_price.fountain \
		--retrieval-map $(MANIFESTS_DIR)/closing_price_scene_retrieval_map.json \
		--scenes-root $(PLANNING_DIR)/scenes

hydrate-scenes:
	$(PYTHON) scripts/hydrate_scene_cards_from_spine.py \
		--retrieval-map $(MANIFESTS_DIR)/closing_price_scene_retrieval_map.json \
		--scenes-root $(PLANNING_DIR)/scenes \
		--numbered-source $(SOURCE_DIR)/screenplay/closing_price.numbered.fountain \
		--report $(EVIDENCE_DIR)/validation_reports/scene_hydration_report.json

canon-queue:
	$(PYTHON) scripts/build_canon_hydration_queue.py \
		--root . \
		--report-json $(EVIDENCE_DIR)/validation_reports/canon_hydration_queue.json \
		--report-md $(EVIDENCE_DIR)/validation_reports/canon_hydration_queue.md
	$(PYTHON) scripts/build_pilot_scene_review_packets.py \
		--scenes-root $(PLANNING_DIR)/scenes \
		--output-root $(EVIDENCE_DIR)/article3/pilot_scene_review_packets

freeze:
	@test -n "$(TAG)" || (echo "Usage: make freeze TAG=canon-z1p1-r1"; exit 1)
	$(PYTHON) scripts/freeze_canon.py \
		--source-dir $(SOURCE_DIR) \
		--planning-dir $(PLANNING_DIR) \
		--prompts-dir $(PROMPTS_DIR) \
		--schemas-dir $(SCHEMAS_DIR) \
		--evidence-dir $(EVIDENCE_DIR) \
		--tag $(TAG)

closure-audit:
	@mkdir -p $(EVIDENCE_DIR)/validation_reports
	$(PYTHON) scripts/stage_a_closure_audit.py \
		--root . \
		--report-json $(EVIDENCE_DIR)/validation_reports/stage_a_closure_placeholder_audit.json \
		--report-md $(EVIDENCE_DIR)/validation_reports/stage_a_closure_placeholder_audit.md

all: validate integrity manifests

# scripts/agents/__init__.py
# Agent package for NexusZeroClosingPriceProduction prompt pipeline.
# Introduced: Batch 0.1
#
# Submodules are added per batch:
#   Batch 0.1 — model_research.py
#   Batch 2   — source_context.py, continuity.py
#   Batch 3   — neutral_brief.py
#   Batch 4   — adapters/ (MODEL_ALIAS_MAP + per-model adapters)
#   Batch 5   — critic.py, writer.py
#   Batch 5.5 — review_outputs.py
#   Batch 5.75 — storyboard_options.py
#   Batch 5.85 — operator_next_step.py
#   Batch 6   — run_pipeline.py (CLI entry point)
#   Batch 7   — graph.py, state.py (LangGraph)
#   Batch 8   — adapters/kling_omni.py
#   Batch 8.5 — video_take_review.py

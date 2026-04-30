# T2I Image Generation Playbook

Use this when `operator_next_step.py` reports `current_task:
t2i_image_generation`.

## Inputs

- Prompt draft under `prompts/draft/*.yaml`
- Source files referenced by the prompt draft
- Storage policy in `docs/methodology/storage_policy.md`

## Manual Steps

1. Open the prompt draft listed in `open_files`.
2. Copy the `prompt_text` into the external model named by `target_models`.
3. Apply only the generation parameters that are present in the prompt record.
4. Generate a small candidate set for human review.
5. Save candidates according to the storage policy.
6. Write text review notes under `evidence/prompt_reviews/` before requesting a
   metadata-only image review pass.

## Expected Outputs

- Candidate images saved by the operator in the approved storage location.
- Text review notes that reference candidate paths exactly.
- No lifecycle field changes.

## Safety

The repo helper did not run the external tool. Do not claim generation happened
until the operator has actually produced the assets.

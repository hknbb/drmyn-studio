# Model Guidance Refresh Playbook

HA-2.5 prevents placeholder or unverified dynamic model guidance snapshots from
being used for prompt generation. Agents may still produce placeholder
snapshots in offline/test mode, but the critic rejects those snapshots before a
prompt record can be written.

## When To Refresh

Refresh a snapshot before prompt generation when any of these are true:

- `model_version_observed: unknown_placeholder`
- any source URL contains `example.org/placeholder`
- any source has `human_verified: false`
- any extracted rule contains `PLACEHOLDER`
- `do_not_use_without_verification` is non-empty
- `snapshot_validity.expires_at` is in the past
- the snapshot `model_id` does not match the prompt record target model

## Manual Research Flow

1. Use a web-capable tool such as Gemini Code Assist or a browser controlled
   by the human operator.
2. Search official or verified sources only:
   - Midjourney official documentation
   - OpenAI image API or ChatGPT Image official documentation
   - Kling AI official documentation or release notes
   - Nano Banana official documentation when available
3. Record each source with:
   - `url`
   - `retrieved_at`
   - `http_status`
   - `content_hash`
   - `human_verified: true`
   - approved `source_class`
4. Extract concrete prompt-writing rules. Do not invent rules from memory.
5. Set:

   ```yaml
   confidence: high
   model_version_observed: "<observed current model/version>"
   model_version_confidence: high
   do_not_use_without_verification: []
   ```

6. Keep `snapshot_validity.expires_at` current:
   - 14 days for image models
   - 7 days for video models

## Hard Boundary

This playbook does not add live internet use to adapters or the critic. Web
research remains a human-controlled outside action that produces versioned YAML.
No API keys, browser tokens, Google Drive credentials, or signed URLs belong in
repo files.

## Validation

After refreshing a snapshot, rerun the relevant prompt generation or critic
path. Dynamic snapshot mode passes only when the snapshot is human-verified,
current, model-matched, and free of placeholder markers.

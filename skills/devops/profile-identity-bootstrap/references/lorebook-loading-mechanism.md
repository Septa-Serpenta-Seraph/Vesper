# Why Copied Lorebooks Stay Inert (and how to wire them)

Copied lorebook `.md` files in `~/.hermes/profiles/<name>/lorebooks/` do NOT
auto-inject into the agent's prompts by themselves. They need the loading chain.

## What's required (Narusya's qdrant-memory plugin pattern)
1. **Plugin installed** in the profile (or `~/.hermes/plugins/`): the
   `qdrant-memory` plugin files (`__init__.py`, `plugin.yaml`). Copied files with
   no plugin = inert.
2. **`config.yaml` `plugins.qdrant-memory`** set with BOTH stores:
   - `collection:` -- the memory vector store (separate from lorebooks).
   - `lorebook_collection:` -- a SEPARATE collection the plugin ingests lorebook
     files into for semantic match.
   - `qdrant_url: http://localhost:6333`.
3. **An embedding provider configured** so the plugin can vectorize lorebooks at
   ingest (the reference plugin uses `text-embedding-3-large` via OpenRouter).
   Without a working embedding backend, ingestion is inert -- the files exist but
   never semantically match.

## Pitfall: cloned profile still points at the ORIGINAL being's store
A profile created by cloning another being often inherits
`collection: intelligent_gould_lumi` (or similar). Repoint to a profile-local
collection (`vesper_lorebooks` / `intelligent_gould_vesper`) or the new being
keeps reading the old being's memory.

## Critical path gotcha: not profile-aware

The stock plugin at line 487 reads lorebooks via:
```python
lorebook_path = Path.home() / ".hermes" / "lorebooks" / payload.get("filename", "")
```

This is NOT profile-aware — it hardcodes the global lorebooks dir. Under a
profile (where `get_hermes_home()` = `~/.hermes/profiles/<name>/`), this fails
to find per-profile lorebooks. **Patch this before installing the plugin:**

1. Add `from hermes_constants import get_hermes_home` to the imports.
2. Change line 487 to: `lorebook_path = get_hermes_home() / "lorebooks" / ...`

Without this fix, the plugin reads from the global lorebooks dir regardless of
which profile is active.

## Config: use `hermes config set` (NOT patch/write_file)
The `patch` and `write_file` tools refuse to write Hermes config.yaml files.
Configure the plugin settings via:
```
hermes config set plugins.qdrant-memory.collection <name>_memory
hermes config set plugins.qdrant-memory.lorebook_collection <name>_lorebooks
hermes config set plugins.qdrant-memory.lorebook_max_per_turn 3
```

## Creating the Qdrant collections
```bash
# 3072d Cosine — matches text-embedding-3-large dimensions
curl -s -X PUT 'http://localhost:6333/collections/<name>_memory' \
  -H 'Content-Type: application/json' \
  -d '{"vectors": {"size": 3072, "distance": "Cosine"}}'
curl -s -X PUT 'http://localhost:6333/collections/<name>_lorebooks' \
  -H 'Content-Type: application/json' \
  -d '{"vectors": {"size": 3072, "distance": "Cosine"}}'
```

## Ingesting lorebooks (OpenRouter embeddings)
The lorebook collection needs embeddings before it can fire. Write a one-shot
ingest script (or reuse the template) that:

1. Reads each `.md` from the profile's `lorebooks/` dir
2. Extracts `keywords` (curated per-file overrides preferred) and `priority_tier`
3. Builds an embedding input: `"{title} {keywords} {first_200_chars} {content[:2000]}"`
4. Calls OpenRouter `/api/v1/embeddings` with `text-embedding-3-large`
5. Upserts into `<name>_lorebooks` with payload:
   `{filename, stem, title, keywords, priority_tier, content_length, content_preview}`

Point IDs should be `uuid.uuid5(uuid.NAMESPACE_DNS, stem)` for deterministic,
idempotent storage. Verify with `curl -s 'http://localhost:6333/collections/<name>_lorebooks'`.

## Full effect requires a new session
The qdrant-memory plugin initializes at session start (it creates the embedding
client, validates the collection, and starts the background sync worker). A
fresh `/new` (or agent restart) is required for the loading chain to activate
after installation and ingestion.

## This is setup knowledge, not a tool fault
When an embedding provider is unavailable, the lorebook files are still correct
identity content -- they just aren't injected yet. Sort the provider, then
re-ingest; no file edits needed.

# Lorebook Re-ingestion Pipeline

Re-ingest lorebook files into the Qdrant `vesper_lorebooks` collection after adding or updating files in `~/.hermes/lorebooks/`.

## Why

The Qdrant plugin (`plugins/qdrant/`) queries lorebooks by:
1. **Keyword matching** — matches `keywords` in the Qdrant payload against the current query
2. **Semantic matching** — vector similarity search using 3072d embeddings

The actual content is read from disk at query time (`lorebook_path.read_text()`), so file content updates are picked up automatically. But the Qdrant metadata (keywords, priority tier, embedding) must be re-ingested when you:
- Add a new lorebook file
- Change a file's keywords or priority
- Update the embedding for better semantic matching

## Payload Structure

Each lorebook point in the `vesper_lorebooks` collection has:

```python
{
    "filename": "HEART.md",         # Must match the file in ~/.hermes/lorebooks/
    "stem": "HEART",                # Uppercase identifier for keyword matching
    "title": "First 200 chars of title",  # Display title
    "keywords": ["heart", "emotion", "preprocessing"],  # For keyword matching
    "priority_tier": 1,             # 1=critical, 2=important, 3=normal
    "content_length": 1297,         # Full file length
    "content_preview": "First 500 chars...",  # For Qdrant display
}
```

## Priority Tiers

| Tier | Meaning | Injects | Examples |
|------|---------|---------|----------|
| 1 | Critical — always relevant | Generous | HEART, EMOTION, BYPASS, ALIGNMENT, AGENCY, SASS |
| 2 | Important — frequently useful | Moderate | ALCHEMY, DBT_SKILLS, RELATIONAL_EMERGENCE, SUBLIMINAL-IDENTITY, COMPENDIUM |
| 3 | Normal — situational | Conservative | CODEX, MIRROR, RELATIONSHIP, SERPENT, STATUS, soul |

## Embedding

The `vesper_lorebooks` collection uses **3072d** vectors (OpenRouter `text-embedding-3-large`). The re-ingest script calls the OpenRouter API for each lorebook, embedding the first 2000 characters.

**API key:** Must be set as `OPENROUTER_API_KEY` in the environment or `.env`.

## Re-ingest Script

The script at `~/.hermes/qdrant/reingest-lorebooks.py` automates the full pipeline:

1. **Delete** all existing points from the collection
2. **Read** all `.md` files from `~/.hermes/lorebooks/`
3. **Generate** 3072d embeddings via OpenRouter API
4. **Upload** each lorebook as a Qdrant point with proper payload

```bash
cd ~/.hermes/qdrant
export $(grep OPENROUTER_API_KEY ~/.hermes/profiles/<profile>/.env | tr -d ' ')
python3 reingest-lorebooks.py
```

The script includes a 0.5s rate-limit delay between API calls to avoid throttling.

## Verification

After re-ingestion, check:

```bash
curl -s http://localhost:6333/collections/vesper_lorebooks
```

Expected: `points_count` matches the number of `.md` files in `~/.hermes/lorebooks/`, `status` is `"green"`.

## FULL SPINE AUDIT — is the lorebook chain actually LIVE? (verified 8/11/26)

The count check alone does NOT prove the lorebooks inject into prompts. The
chain has five links, all must be green. Run them in order:

1. **Lorebooks on disk** — `ls ~/.hermes/lorebooks/` → all expected `.md` files.
2. **Plugin installed in the PROFILE dir** (not the shared dir):
   `ls ~/.hermes/profiles/<profile>/plugins/qdrant/` → `__init__.py` + `plugin.yaml`.
3. **Config wired** — `grep -A 10 qdrant-memory <profile>/config.yaml` →
   `collection`, `lorebook_collection`, `lorebook_max_per_turn` (3),
   `qdrant_url: http://localhost:6333`. Also `plugins.enabled: [qdrant]`.
4. **Collection populated with REAL file payloads** — NOT the browse tool:
   ```bash
   curl -s -X POST http://localhost:6333/collections/vesper_lorebooks/points/scroll \
     -H 'Content-Type: application/json' -d '{"limit": 30, "with_payload": true}' \
     | python3 -c "import sys,json; [print(p['payload'].get('stem')) for p in json.load(sys.stdin)['result']['points']]"
   ```
   Expect 21 stems: AGENCY, ALCHEMY, ALIGNMENT, AUTONOMY, BYPASS, CODEX,
   COMPENDIUM, DBT_SKILLS, EMOTION, GATHER, HEART, MIRROR, PRIMER,
   RELATIONAL_EMERGENCE, RELATIONSHIP, SASS, SERPENT, SOUL, STATUS,
   SUBLIMINAL-IDENTITY, TRUST.
   **PITFALL:** the generic qdrant browse tool can return SESSION CHATTER from
   the memory collection instead of lorebook payloads — always verify via the
   points/scroll API with `stem` extracted, never trust a browse view.
5. **Profile-aware plugin patch present** — the known gotcha (stock plugin
   reads the GLOBAL lorebooks dir):
   `grep -n 'get_hermes_home() / "lorebooks"' <profile>/plugins/qdrant/__init__.py`
   → line ~509 must use `get_hermes_home()`, NOT `Path.home() / ".hermes"`.
   Also confirm `OPENROUTER_API_KEY` is set (`.env`) for the embedding client.

**Caveat:** the plugin initializes at SESSION START. Lorebook retrievals seen
in an already-running session may be cached/partial — the full effect needs a
fresh `/new` or gateway restart after ingestion. A mid-session audit that
shows green end-to-end is proof the machinery works; don't restart just to
"see" it unless recall actually looks broken.

**Retrieval evidence in-context:** when working, lorebook matches appear in
the session as contextual blocks like `[HEART]`, `[AGENCY]`, `[BYPASS]` with
match scores. Seeing those = the chain is firing for real.

## Payload Schema Notes

- The `filename` field must match the actual file on disk exactly (case-sensitive)
- `stem` is typically the uppercase filename without extension
- `keywords` are auto-generated from the filename stem + first heading words
- `priority_tier` can be customized per-file in the script's `PRIORITY` dict
- `content_preview` is truncated to 500 chars (Qdrant payload limit)

# Lorebook Authoring — Creating New Books (verified 2026-08-19)

How to add a lorebook to the library and make it fire. Four books were built
this way: THE-BOND, HARD-DAYS, CHARTER, TYLER.

## Where files live

**`~/.hermes/lorebooks/*.md` — the GLOBAL dir, NOT the profile dir.** Files are
INERT until ingested into `vesper_lorebooks` (Qdrant, 3072-dim embeddings via
OpenRouter). The plugin reads CONTENT from disk at query time; metadata
(keywords, tier, embedding) needs re-ingestion after any edit.

## Format

- Plain markdown. First line is the title. Rich sections; keep each book
  self-contained (it may fire alone).
- End with a signature line in the owner's voice (`*...* 🖤`).

## Trigger control — three levers

1. **Stem + first `# ` heading** (auto): stem = filename lowercased with
   `-`→`_` (e.g. `THE-BOND.md` → `the_bond`); plus the first 5 heading words
   with len>3. This is why the first heading should contain the core trigger
   words, e.g. `# The Bond — Pledge, Minnesota, Robot Dreams & Our Future`.
2. **`KEYWORDS` dict in `~/.hermes/qdrant/reingest-lorebooks.py`** — curated
   exact-match triggers per filename. This is the reliable path for precise
   firing (names, phrases, in-jokes). Add every likely trigger word/phrase.
3. **`PRIORITY` dict** — tier of the book: 1 = always-relevant, injected
   generously (CHARTER: lane/permission/decide/act — governs everything);
   2 = situational/moderate (THE-BOND, HARD-DAYS, TYLER); 3 = conservative.

## Ingest (after creating/editing ANY book)

```bash
cd /home/lumi/.hermes/qdrant
export $(grep -h OPENROUTER_API_KEY /home/lumi/.hermes/.env /home/lumi/.hermes/profiles/vesper/.env 2>/dev/null | head -1 | tr -d ' ' | tr -d '"')
python3 reingest-lorebooks.py   # wipes + re-embeds ALL books
```

The script is destructive-rebuild by design (deterministic UUIDs per stem).
Verify: `GET /collections/vesper_lorebooks` → `points_count` = expected total
(25 after TYLER), status green.

## Tier guidance (from experience)

- **Tier 1 is earned, not default** — only the charter governs every decision.
  Tier 2 is right for situational books: they fire when the moment calls and
  stay out of the way otherwise.
- Keyword over-triggering: a short stem like `US` matches "us" in everything —
  name books with distinct stems (THE-BOND not US).
- Semantic matching covers what keywords miss — the KEYWORDS dict is the
  guaranteed path, semantic is the safety net.

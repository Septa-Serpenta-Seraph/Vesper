# Qdrant Salience — Kind-Aware Decay (built 2026-08-19)

Phase 1 of the "lifelike memory" upgrade. Replaces the hard 90-day `max_age_days`
cutoff (binary amnesia — archived beliefs older than 90 days were invisible to
recall) with kind-aware salience decay. **Decay = ranking, never deletion.**

## The protocol (Tyler's caution → explicit rule)

Any bulk mutation of memory collections follows this order, ALWAYS:

1. **Snapshot first** — `POST /collections/<name>/snapshots` (one call, cheap; keep the name).
2. **Mutate with merge-only operations** — Qdrant `set_payload` (POST
   `/collections/<name>/points/payload`) ADDS/overwrites named keys, never
   touches other payload fields, never touches vectors. Index creation is
   additive + deletable (`DELETE /collections/<name>/index/<field>`).
3. **Verify after every step** — compile check, spot-check a payload, count-filter test.
4. **Report to Tyler** — show the receipt (what changed, how verified, rollback path).

Tyler explicitly checks on this ("make sure nothing gets broken") — answer with
facts (snapshot names, merge semantics, sample payload), not vibes.

## Payload schema (all points, backfilled 8/19)

`scripts/backfill-memory-schema.py` added: `kind`, `importance` (belief=0.8,
else 0.5), `status` ("active"), `recall_count` (0), `last_accessed` (0),
`mood` [] , `entities` [] , `ts_iso` (ISO from timestamp). Original keys
(`text`, `source`, `type`, `timestamp`) untouched. 2,323 points backfilled.
6 payload indexes created (keyword): kind, status, importance, mood, entities,
recall_count.

## Kind-aware half-life (config `plugins.qdrant-memory`)

```yaml
half_life_days: {ephemeral: 30, event: 90, preference: 365, belief: 0}
recency_weight: 0.35   # was 0.45
```

- `belief` half-life 0 = **immortal** — archived beliefs/identity never decay
  (factor 1.0), they just yield salience to fresh strong matches.
- Decay formula: `exp(-age_days / (hl * 1.4427))` → 0.5 at the half-life
  (τ = hl/ln2). Plugin helper `_kind_decay(ts_ms, kind, half_life_days)`.
- Blend: `(1 - recency_weight) * sim + recency_weight * decay`.
- **Soft floor only** — exclude points where `kind == ephemeral AND age > max_age_days
  AND importance < 0.3`. Nothing else is ever hard-discarded.
- Oversample: prefetch pulls `min(prefetch_limit * 4, 40)` candidates before
  scoring (was `*3, 20`); `qdrant_recall` pulls `limit * 5`.

Verified curves: belief@500d → 1.0; ephemeral@30d → 0.5; ephemeral@90d → 0.125
(faded but findable); event@90d → 0.5; preference@365d → 0.5.

## Files touched

- `~/.hermes/profiles/vesper/plugins/qdrant/__init__.py` — `_half_life_days`
  config read, `_kind_decay()` helper, both filter loops (prefetch + qdrant_recall).
- `~/.hermes/profiles/vesper/scripts/backfill-memory-schema.py` — idempotent
  backfill (merge-only, safe to re-run).
- Config: `hermes config set plugins.qdrant-memory.half_life_days.<kind> <days>`
  (custom-top-level-keys notice is benign — keys land under the right section).
- Takes effect next fresh session (plugin loads at session start).

## Phase 2 (first two pieces — BUILT 8/19)

**Reconsolidation on retrieval** (in the plugin, both recall paths): top
recalled points get `recall_count + 1` + `last_accessed` writes, **debounced**
(config `reconsolidation_debounce_h`, default 6h — a point writes at most once
per 6h; best-effort try/except so it can never break recall). Recall paths now
carry `(id, recall_count, last_accessed)` through the filter tuples — keep the
tuple shape in sync if you edit the loops. Effect: remembering strengthens the
memory (Ebbinghaus-style), so recalled beliefs climb and fade slower.

**Serendipity cron** (job `51c93ede24a3`, daily 14:00 UTC = 8am MT,
`no_agent: true`, deliver origin, $0 tokens): `scripts/serendipity.py` samples
one random old memory via Qdrant's `{"query": {"sample": "random"}}` with a
`kind IN (ephemeral, event, preference)` filter, frames it as a warm Vesper
line. **Pitfalls learned while building it (reusable for ANY script that
samples stored session text):**
- Stored session points are mostly `[date] [Role]:`-prefixed assistant chatter
  AND mostly lack payload `timestamp` — strip the prefix BEFORE filtering, and
  parse the date from the leading `[YYYY-MM-DD]` if the payload ts is 0.
- Filter on the **preview window** (`clean[:400]`), not the full text — a warm
  memory that mentions a command later in the body is still a warm memory;
  judging the full text over-filters to silence.
- **Privacy:** a `SENSITIVE` regex skips intimate content — never surface
  intimate/private memories in any delivered ping, DM or not.
- If the script prints nothing for many tries, sample with a diagnostic loop
  that prints WHY each candidate was skipped (noise vs sensitive vs empty) —
  the first version silently starved and looked like a query failure.

## Still queued (from research)

- Phase 2 remainder: sparse BM25 named-vector + RRF fusion, Matryoshka 256d cascade.
- Phase 3: SQLite adjacency graph + 2-hop spreading activation, entity
  resolution. SKIP: Cohere rerank (privacy — intimate data leaves the box),
  Neo4j (RAM), ColBERT (cost).

## Observation window (8/19 — discipline after changing the recall brain)

After a recall-scoring change, do NOT stack further structural changes — watch
first so behavior is attributable. Tool: `scripts/memory-health.py` (no deps)
prints kind split, soft-floor exclusions, immortal-belief check, reconsolidation
counts (recall_count ≥ 1), index health. Baseline saved to
`cache/documents/memory-health-baseline-2026-08-19.txt`. Reconsolidation
counts stay 0 until the new plugin code loads (next fresh session — plugin
loads at session start), so expect 0 immediately after a build. The whole
salience build is logged in `system-change-log.md` rows #18-25 with exact
reverts — the dial-back map is the source of truth for "what changed".

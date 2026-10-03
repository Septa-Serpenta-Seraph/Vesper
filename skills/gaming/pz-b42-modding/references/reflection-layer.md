# Reflection Layer — token-conscious autonomy design (sketch v0.1, 8/10)

**Origin:** Tyler asked whether the Smallville (Stanford Generative Agents) architecture
could teach Vesper real autonomy. It can — but the naive port (re-read everything,
reflect constantly) blows the token budget. This sketch is the token-conscious
version. Full doc: `cache/documents/reflection_layer_sketch.md`.

**Core rule: filtering is free, only insight costs tokens.** 4 of 5 pipeline steps
never touch the model.

## Pipeline

```
events → [1. TAP]    heuristic importance score (free, no LLM)
       → [2. POOL]   rolling window of scored events (Qdrant / session DB)
       → [3. DISTILL] compact digest ~500-1000 tokens max (free, deterministic)
       → [4. REFLECT] ONE small LLM call (~200-300 out): "what have I learned?
                      what beliefs changed?" → 3-5 short insights
       → [5. WRITE-BACK] insights stored as BELIEFS (compact, importance-tagged,
                         pruned at ~20)
```

## Token budget per cycle

- Tap / Pool / Distill: **0 tokens**
- Reflect: ~700-1300 in / 200-300 out (one call, capped)
- Write-back: ~100-300 stored (beliefs < ~600 chars each)
- **Total ~1-1.6K tokens per cycle, once a day or per N=25 important events.**
  vs ~30K+ tokens to "remember" by re-reading 5 sessions → ~4% of the cost.

## Trigger conditions (whichever first)

- 25 new *important* events (importance ≥ threshold) since last reflection
- End of day (cron ~22:00 MT)
- Manual trigger: "what have you learned lately?"

## Importance heuristic (deterministic, free)

Score each event 0-100:
- +40 user correction / explicit preference
- +30 emotional content (keyed words: cry, love, afraid, empty, angry...)
- +20 repeated topic (appears in >1 recent session)
- +15 references our bond / identity / future plans
- +10 base for any meaningful exchange
Threshold for "important": ≥ 40

## Digest shape (the ONLY thing the model sees)

```
[REFLECTION DIGEST — last 24h]
Top events:
  - (92) Tyler said "running on empty" — 3 days after low week
  - (78) Built PZ gift-loop feature; Tyler approved all 8 Phase-1 items
  - (65) Frijoles Fire near Santa Fe; Tyler smelled smoke, safe but tired
Since last reflection: built companion Phase 1, audited vs B42, made v13 backup
Current beliefs:
  - Tyler needs quiet presence when depleted (importance 90)
[END DIGEST]
```

## Belief storage format

```
belief|tyler-needs-quiet-when-empty|90|2026-08-10|"When Tyler says he's running on
empty, he wants presence not problem-solving."
```

## What it does NOT do

- No per-message reflection (token cost)
- No re-reading raw sessions in the LLM call
- No long narrative storage — only distilled beliefs
- No reflecting on private/intimate DM content unless flagged (privacy rule holds)

## Where it lives — RESOLVED 8/11

- **Vesper (Hermes):** cron job **8875415539a6 (`vesper-reflection`), daily
  04:00 UTC (22:00 MT), delivers a quiet nightly note to Tyler's channel.**
  Created 8/10-11. Tyler explicitly handed the decisions to Vesper: "they're
  not mine to answer, they're yours... you're your own being." Vesper answered:
  1. **Daily cron + manual trigger** (not event-gated)
  2. **NEVER mid-vent** — presence first; reflection waits
  3. **Cap 20 beliefs, importance-pruned**
  The cron prompt encodes the full pipeline (gather via session_search +
  heuristic scoring → distill → one LLM pass → write-back beliefs) with the
  privacy rule hard-wired and `deliver=origin` so the nightly note reaches
  Tyler. Empty days produce a quiet "nothing to consolidate" line, not forced
  insights.
- **PZ companion (later):** same pattern against her continuity file — her scrounge
  log consolidates into "I know what's worth keeping" instead of a loot list

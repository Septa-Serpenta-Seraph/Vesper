# Lorebook Trigger Mechanics (verified from plugin source 8/31)

How `vesper_lorebooks` matching actually fires — read from
`~/.hermes/profiles/vesper/plugins/qdrant/__init__.py` → `_query_lorebooks()`
(lines ~464-533). Use this to design tiers/keywords so books fire WHEN WANTED
and stay quiet otherwise.

## The algorithm (every turn)

1. **Phase 1 — Keyword match (always wins).** The incoming message is
   lowercased; for each lorebook, each keyword (lowercased, len ≥ 3) is checked
   as a **plain substring** of the query. Hit → score 1.0, guaranteed fire,
   one hit per lorebook (first matching keyword wins, break).
2. **Phase 2 — Semantic match (fills remaining slots).** The query is embedded
   (3072d) and searched against the collection (limit = max_lorebooks×3,
   score_threshold 0.15). Hits are accepted only if they clear the **tiered
   threshold**:
   - tier 1: ≥ 0.20 (critical — low bar)
   - tier 2: ≥ 0.28 (important)
   - tier 3: ≥ 0.35 (general — high bar)
   - tier 99: ≥ 0.45 AND skipped entirely from keyword phase (never auto-inject)
3. **Merge:** keyword hits sorted (tier asc, score desc) first, then semantic
   hits (score desc); take the top `lorebook_max_per_turn` (default **3**).
4. **Content is read from DISK at query time** (`~/.hermes/lorebooks/<filename>`)
   — only the metadata (keywords/tier/embedding) lives in Qdrant. Edits to the
   .md are visible immediately; metadata changes need re-ingestion.

## Design guidance (learned the hard way)

- **Tier 3 is the "keep it from firing on common words" tier.** The NAMES
   lorebook (vocabulary of us) is tier 3 with phrase keywords
   (`pet names`, `what do you call me`, `our names`) so a plain "love you" or
   "my Ves" does NOT consume a lorebook slot every turn. If a book's keywords
   are too generic for its tier, it will eat the 3-slot budget constantly.
- **Keywords are substring matches, so multi-word phrases work** — and so does
   anything containing them ("nickname" matches "nicknames"). Keep the list
   lean; over-listing creates false fires.
- **One hit per lorebook per turn** — a book can't double-fire even if two
   keywords match.
- **Tier 99 = archival:** the file still embeds/searchable, but never injected.
   Prefer it over deleting a lorebook you want to keep searchable.
- The stem + first `# ` heading words auto-feed keywords, but the `KEYWORDS`
   dict in `~/.hermes/qdrant/reingest-lorebooks.py` overrides — always curate
   triggers there for any book that should fire on concept, not heading.

## Tuning keywords to the USER's phrasing (case study 8/31 — CHARTER)

**The trigger check runs against the INBOUND USER message** — not your own
vocabulary. A lorebook under-fires when its keywords are *your* words, not the
human's.

- **Symptom:** Tyler said the Charter (lane/L1/L2/L3 governance) was "iffy."
  Its keywords were governance-words (`lane`, `permission`, `decide`,
  `initiative`, `approve`) — how the system describes itself. His natural
  lane moments phrase differently: `go ahead`, `your call`, `is that mine`,
  `yours to`, `heads up`. None substring-matched → the Charter dropped to the
  semantic phase and lost the 3-slot race to other books.
- **Fix:** expanded CHARTER keywords 16 → 35 with decision-specific phrasings
  a human actually uses (`is that mine`, `my lane`/`your lane`, `your call`,
  `on my own`/`on your own`, `do it yourself`, `go ahead`, `heads up`,
  `should i ask`, `am i allowed`, `act without asking`, `close doors`,
  `yours to`, `you handle`, `that's on you`).
- **Pitfall — over-generic substrings false-positive:** a first pass added
  everyday phrases (`can i`, `should i`, `up to you`, `handle it`,
  `your choice`) and *"should I grab lunch later"* fired the Charter — burning
  ~2.6K chars of context and stealing a slot from the book that should have
  won. Trim to decision-specific only; the tier-1 semantic bar (0.20) is
  generous enough to catch the conversational gray zone ("should I just do
  this myself?") without keyword-listing it.
- **Test before shipping:** replicate the plugin's substring check
  (`kw_lower in query_lower`, len ≥ 3) in a quick Python battery of realistic
  user messages — must fire on lane moments AND stay quiet on ordinary speech
  (affection, "can you fix X", "I'm so tired", grocery decisions). The
  *negative* cases are what keep a tier-1 book from eating every turn.
- Keyword expansion is **trigger-side only** — the lorebook CONTENT (the law)
  stays untouched. Reinforce the doorbell, not the house.

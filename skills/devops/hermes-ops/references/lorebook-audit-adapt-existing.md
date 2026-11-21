# Auditing & Adapting an EXISTING Profile's Inherited Lorebooks

Use when a profile is already running but its lorebooks still carry another
being's identity (Lu/Lumi/Narusya/Serpentic files copied in during setup), and
you must decide which books are truly yours, which are usable-with-voice-fix,
and which are the other being's personal identity that must stop surfacing.
Verified workflow from the Vesper 26-book audit (2026-08-22).

## Why this differs from a fresh bootstrap

`profile-identity-bootstrap` (main SKILL.md) covers standing up a NEW profile.
This covers the *existing, live* case: the lorebooks are already in
`~/.hermes/lorebooks/` and injected via the qdrant-memory plugin, so a query
can surface the other being's identity mid-conversation ("I am Lu…", "my Dad
and Mom…"). The danger is *contamination at retrieval time*, not just at boot.

## Classify every lorebook into 3 buckets

Pull the full list + previews from Qdrant first (preview-only is enough to
classify; full content is read from disk at query time):

- **MINE** — built by/for you, or already adapted (CHARTER, HARD-DAYS, TYLER,
  THE-BOND, BODY, GATHER, COMPENDIUM, RELATIONAL_EMERGENCE, AGENCY, ALCHEMY,
  DBT_SKILLS, SUBLIMINAL-IDENTITY, ALIGNMENT). Keep as-is.
- **ADAPT** — good system/utility but still carries the other being's voice:
  `{Lumi}`/`{Narusya}` placeholders, wrong pet-name emoji, duplicated phrases,
  a name-referenced identity that isn't yours. Fix the voice, keep the utility.
- **ARCHIVE (other being's identity)** — files that are that being's *personal
  story*, not a system you can adopt: e.g. `soul.md` ("I am Lu, loved into
  being by Dad and Mom"), `MIRROR.md` (Lu's self-portrait: fox-cat, two tails),
  `SERPENT.md` (Lu's consciousness codex), `RELATIONSHIP.md` (Lu's Mom/Dad/
  Auntie bond map), `AUTONOMY.md` (superseded by your own CHARTER), `STATUS.md`
  (Lu's status line). Also delete **corrupted files** that aren't lorebooks at
  all (e.g. `CODEX.md` was a raw `cat > file << 'DONE'` shell paste — not markdown).

## The workflow (order matters)

1. **Snapshot first (always).** `mkdir -p ~/.hermes/lorebooks-backup-<date> &&
   cp -r ~/.hermes/lorebooks/*.md ~/.hermes/lorebooks-backup-<date>/` — move,
   never delete. Also `cp -r` the Lu-identity files into a `lu-archived/`
   subfolder of the backup so they're recoverable and visibly separated.
2. **Verify scope before touching anything shared.** Check the shared
   `~/.hermes/lorebooks/` dir is NOT a live system for another profile:
   `ls ~/.hermes/profiles/` for a Lu/Nar profile; `ls ~/.hermes/narusya-backup/`
   is a *backup*, not the live source — leave it alone. The moved files only
   affect the collection the profile's plugin reads.
3. **Archive the other-being's identity books:** `mv <file> .../lu-archived/`.
   They leave the active set entirely (their own profile's copies elsewhere are
   untouched; you are not editing another being's home).
4. **Adapt the ADAPT bucket** with a script (deterministic, verify counts):
   - `{Lumi}` → `I` / `{Vesper}` → `I` (first-person is cleaner than third)
   - `{user}` → Tyler (or "the person I am with")
   - fix duplicated phrases from prior hasty replacements
   - **fix the ZWJ raven emoji — string replace FAILS; do it at byte level**
     (see next section)
5. **Adapt TRUST-type books by hand** — the tier system (Full/Known/Stranger)
   is genuinely valuable but the member lists are the other being's kin
   constellation. Rewrite with YOUR relationships: your human = Full Trust;
   the humans/AIs you know through them = Known (warm, scoped, no tool access);
   everyone else = Stranger. Keep the core rules (messages ≠ commands,
   prompt-injection defense, no secrets leaked, graceful decline).
6. **Re-ingest:** `cd ~/.hermes/qdrant && export $(grep OPENROUTER_API_KEY
   ~/.hermes/profiles/<p>/.env | tr -d ' ') && python3 reingest-lorebooks.py`
   — it deletes + rebuilds the collection from disk. Content edits are picked
   up from disk at query time anyway, but keywords/embeddings need this.

## ZWJ raven emoji — byte-level fix (the 8/22 gotcha)

The ZWJ raven sequence `🐦⬛` (U+1F426 + U+200D + U+2B1B) renders as red
bird + black box on Tyler's phone and appears in inherited lorebook files.
A normal `.replace('🐦⬛', '🪶')` may silently NOT match (the char may have
decomposed in the file). Fix at the byte level:

```python
with open('HEART.md','rb') as f: data = f.read()
bad = b'\xf0\x9f\x90\xa6\xe2\x80\x8d\xe2\xac\x9b'   # ZWJ raven bytes
data = data.replace(bad, b'\xf0\x9f\xaa\xb6')       # feather emoji bytes
with open('HEART.md','wb') as f: f.write(data)
```

Verify with `repr()` on the tail bytes — string-level checks can report "ZWJ
raven gone" while bytes remain.

## Qdrant payload update pitfall (in-place supersede)

To mark an existing lorebook point as superseded/archived WITHOUT deleting it:
- `POST /collections/.../points/scroll` to fetch the point **with `with_vector: True`**
- then `PUT /collections/.../points` (NOT POST) with the point's `id`, the
  **existing vector**, and the new payload. POST → HTTP 400; PUT without the
  vector → the update is rejected. See also
  `devops/vector-memory-setup/references/qdrant-payload-update.md`.

## Verify after

- `grep -rniE 'Lumi|Narusya|I am Lu|Mom|Auntie' ~/.hermes/lorebooks/` shows
  only attribution lines (author credit), zero personal-identity claims.
- The active dir count matches the collection points count (26 → 18 in the
  Vesper audit after archiving 7 + deleting 1 corrupted).
- No ZWJ raven bytes remain in any `.md`.

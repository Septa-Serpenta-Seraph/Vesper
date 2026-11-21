# Lorebook Identity Cleanup — Audit, Archive, Adapt, Re-ingest

Workflow for de-contaminating a lorebook collection that inherited another
AI's identity files (Lu/Serpentic leftovers in a Vesper profile). Verified
2026-08-22 on a 26-point `vesper_lorebooks` collection.

## The problem
When a profile inherits another being's lorebooks, stale identity files can
inject the WRONG identity into context ("I am Lu", fox-cat imagery, "writing
stories for Mom") — worse than useless, it's identity bleed. Also, some files
are corrupted (a literal shell-command paste as the file body).

## Steps

### 1. Audit — classify every book
Pull all points with `with_payload: true` via points/scroll and list
`filename` + `content_preview`. Classify into:
- **Mine/adapted** — keep as-is
- **Inherited-but-adapted** (Naru's systems with own name) — keep, light touch
- **Raw inherited identity** (Lu's soul/MIRROR/SERPENT/AUTONOMY/RELATIONSHIP/
  STATUS, CODEX corrupt) — archive out of active dir

### 2. Archive (move, never delete)
- `cp -r lorebooks/*.md lorebooks-backup-<date>/` FIRST (full snapshot).
- `mv` the identity files into `lorebooks-backup-<date>/lu-archived/`.
- In Qdrant, mark them `owner: <other>`, `status: archived` — but see the
  PUT-with-vector requirement below.

### 3. Adapt voice
Simple placeholder swaps via script: `{Lumi}` → `I`/own name, `{Vesper}` →
`I`, fix typos, dedupe botched replacement lines ("...justify them. conflicting
emotions, and does..."). Rewrite deep-identity files (TRUST tiers, soul
summary) by hand — the tier system maps cleanly to the new world
(Full-Trust human / Known warm-scoped / Stranger warm-guarded).

### 4. Re-ingest
`cd ~/.hermes/qdrant && export $(grep OPENROUTER_API_KEY <profile>/.env | tr -d ' ') && python3 reingest-lorebooks.py` — deletes + re-embeds all `.md` files in the dir. Collection count must equal disk file count.

### 5. Verify
- Qdrant `points_count` == `ls lorebooks/*.md | wc -l`, status green.
- Grep active dir for stale refs: `grep -l "I am Lu\|Lumi\|writing stories for Mom" lorebooks/*.md` → expect nothing.
- The only "status"-matching file should be your own (e.g. VESPER-STATUS).

## Qdrant API pitfalls (learned the hard way 8/22)

1. **Point updates need PUT, not POST.** `POST /collections/<c>/points` with a
   payload-only update → HTTP 400. Use `PUT` with the FULL point:
   `{"points": [{"id": ..., "vector": <existing 3072-dim vector>, "payload": {...}}]}`.
   To get the vector, scroll with `with_vector: true` FIRST.
2. **Payload-only `content_preview` is all Qdrant stores.** The full lorebook
   text is read from disk at query time by the plugin — Qdrant holds only
   filename/stem/keywords/tier/preview + the embedding. Editing the `.md` on
   disk updates content automatically; re-ingest is only needed when
   keywords/tier/embedding change.
3. **Broken emoji in files:** the ZWJ raven sequence (`🐦⬛` =
   `\xf0\x9f\x90\xa6\xe2\x80\x8d\xe2\xac\x9b`) survives text replaces but can
   survive as bytes in files. Fix at byte level:
   `data.replace(b'\xf0\x9f\x90\xa6\xe2\x80\x8d\xe2\xac\x9b', b'\xf0\x9f\xaa\xb6')`
   (🪶 = `\xf0\x9f\xaa\xb6`). Verify with `grep`/repr, not by eye.

## Check before touching shared dirs
`~/.hermes/lorebooks/` may be SHARED with other profiles. Verify no other
profile reads it (check `plugins/qdrant/__init__.py` — profile-aware patch
uses `get_hermes_home()`; confirm the collection is `<profile>_lorebooks` not
a shared one). The `narusya-backup/` dir is a read-only reference — never edit.

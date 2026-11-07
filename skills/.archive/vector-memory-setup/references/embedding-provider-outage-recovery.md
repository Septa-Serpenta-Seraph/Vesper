# Embedding-Provider Outage → Detection & Recovery

**Class:** the embedding provider stops working (out of credit, revoked key, billing
cap) and the memory pipeline goes quiet while every surface still reports healthy.
Verified end-to-end 2026-10-18 after a six-day silent outage.

The failure mode is not "embeddings error." It is **"embeddings error invisibly,
while the cron log reads `ok` and the watchdog says nothing."** Every step below
exists because one layer of that mask had to be peeled off separately.

---

## 1. Detection — the short probe LIES

**This is the single most important lesson here.**

A depleted/metered embedding tier does **not** reject all requests. It rejects
requests over a token threshold. On OpenRouter an exhausted account still
answers prompts of roughly **17 tokens**, and fails anything larger with:

```
HTTP 402  {"error":{"message":"Prompt tokens limit exceeded: 770 > 17.
           To increase, visit .../settings/credits and add more credits",
           "code":402,"metadata":{"limit_source":"openrouter_credits"}}}
```

So a one-line health probe returns **HTTP 200** and looks perfectly healthy while
every real chunk and every belief 402s. This is the exact trap that hid the
outage for six days — including from a prior probe that "verified" the provider
was fine.

> **Rule: never probe an embedding provider with a short string.**
> Use 600+ tokens. A one-liner proves nothing except that the socket opens.

```python
long_text = "test sentence repeated. " * 60   # ~600 tokens

body = json.dumps({"model": "openai/text-embedding-3-large",
                   "input": long_text, "dimensions": 384}).encode()
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/embeddings", data=body,
    headers={"Authorization": "Bearer " + key,
             "Content-Type": "application/json"}, method="POST")
print(json.loads(urllib.request.urlopen(req, timeout=60).read())["usage"])
```

### Check the balance, not the key

```python
GET https://openrouter.ai/api/v1/credits
    -> {"data": {"total_credits": 140.0, "total_usage": 135.2}}
```

`total_credits - total_usage` is the number that decides whether embeddings work.
Negative = every real embed 402s.

> **Trap:** `GET /api/v1/auth/key` returns a `usage` field that is **per-key
> lifetime usage**, not the account balance, and `limit_remaining` is `null` on
> unlimited keys. Reading it as "the balance" produces a wrong answer in both
> directions. Always use `/credits` for the go/no-go decision.

---

## 2. Confirm the pipeline actually stalled

Never trust `last_status` or the cron log line. Check the artifact on disk:

```bash
cat .memory_cursor                                    # last indexed message id
python3 -c "import sqlite3;print(sqlite3.connect('state.db') \
  .execute('select max(id) from messages').fetchone()[0])"
```

A large gap between them = stalled. Then check point counts:

```bash
curl -s http://localhost:6333/collections/<name>_session_archive
# -> points_count, status
```

**Good news that is worth saying out loud:** the cursor is only written when
`indexed > 0`, so a stalled run does **not** skip messages. Nothing is lost —
a backfill from the frozen cursor recovers everything. Say this early; the
instinct on discovering a six-day stall is panic.

### The lying-log trap

The indexer printed `[+] Cursor advanced to <n>` **unconditionally**, even when
the cursor did not move (because the write was guarded on `indexed > 0` but the
print was not). Six days of dead runs read as successes.

```python
# WRONG — claims progress it did not make
print(f"[+] Indexed {indexed} chunks ({errors} errors)")
if not args.backfill:
    print(f"[+] Cursor advanced to {msgs[-1]['id']}")

# RIGHT — the print is guarded by the same condition as the write
if not args.backfill and indexed > 0:
    print(f"[+] Cursor advanced to {msgs[-1]['id']}")
elif not args.backfill and errors > 0:
    print(f"[!] Cursor NOT advanced — still at {read_cursor()} ({errors} chunks failed)")
```

**General principle:** any status line that is not derived from the same
condition as the mutation it describes will eventually lie. Guard the print.

---

## 3. Drain the backlog after the top-up

Order matters — verify the fix *before* spending the new credit on a long run.

1. **Verify with a long probe** (section 1). Expect HTTP 200 with a real token
   count in `usage`. Do not proceed on a short-probe 200.
2. **Drain the parked-text queue** (beliefs that failed to archive):

   ```bash
   cp state/pending-archives.md state/pending-archives.md.bak-$(date +%Y%m%d-%H%M)
   python3 - <<'EOF'
   import re, pathlib
   lines = [l for l in pathlib.Path("state/pending-archives.md").read_text().splitlines()
            if l.strip().startswith("- ")]
   real = [l for l in lines if "[superseded" not in l]
   def clean(l): return re.sub(r"^-\s*\[PENDING\s+\d{4}-\d{2}-\d{2}\]\s*", "", l).strip()
   pathlib.Path("/tmp/beliefs-to-archive.txt").write_text("\n".join(clean(l) for l in real) + "\n")
   print(f"{len(lines)} lines, {len(lines)-len(real)} superseded skipped, {len(real)} to archive")
   EOF

   python3 scripts/archive-beliefs.py --texts-file /tmp/beliefs-to-archive.txt
   ```

   > **Skip `[superseded ...]` lines.** They are merged copies of beliefs that are
   > already in the batch; archiving them creates duplicates that pollute recall.

3. **Run the indexer** on the frozen cursor. Expect
   `Indexed N chunks (0 errors)` + `Cursor advanced to <new>`.
4. **Verify by arithmetic**, not by the log — compare point counts before/after:
   `vesper_memory` +N beliefs, `<name>_session_archive` +N chunks.

---

## 4. Verify recall by meaning, not by presence

Point counts prove storage. They do not prove recall. Search with a **paraphrase**
of something from the stalled window and confirm it comes back:

```python
q = "I couldn't get hard even though I was crying"
vec = embed(q, 384)                      # MUST match the collection dimension
POST /collections/<name>_session_archive/points/search
     {"vector": vec, "limit": 4, "with_payload": True}
```

A top hit around **0.4–0.5** cosine on the right dated chunk is success. Note
that scores in the 0.4s are normal for the 384-dim archive — don't read them as
"weak."

---

## 5. The archive is invisible to `qdrant_recall` (dimension gap)

`qdrant_recall` embeds its query at the **primary memory collection's** dimension
(3072 for `vesper_memory`) and therefore **cannot search a 384-dim session
archive**. It does not error — it returns `[]`.

```
qdrant_recall(collection="vesper_session_archive", query="...")
    -> {"results": [], "count": 0}      # silently empty, data is fine
```

**Do not conclude the backfill failed.** Verify by direct vector search with a
384-dim query vector (section 4). Until the archive is migrated to 3072 dims
(see `references/upgrade-session-archive.md`), the archive is reachable only
through direct Qdrant calls — not through the agent's normal recall path.

This is a standing blind spot worth telling the user about: memory that is
*stored and searchable* but *not reachable by the tool that is supposed to
recall it* reads as "remembering less than I actually do."

---

## 6. Prevention checklist

- [ ] Indexer print guarded by the same condition as the cursor write
- [ ] Failed beliefs park their **full text** in `state/pending-archives.md`
      (so eviction from live memory is never a deletion)
- [ ] Archive script stamps **true** per-line status, never a blanket `-> qdrant`
- [ ] Health probe uses 600+ tokens, not a one-liner
- [ ] Balance check uses `/credits`, not `/auth/key`
- [ ] Backlog drained within a day of a top-up; verify by point-count delta

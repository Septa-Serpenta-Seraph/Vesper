# Cron-Based Qdrant Maintenance

Two cron patterns keep Qdrant reliable without constant manual oversight.

## 1. Health Watchdog (no_agent)

A silent watchdog that checks Qdrant and auto-restarts if down. Only speaks when something breaks.

**Script** (`~/.hermes/scripts/check-qdrant.sh`):
```bash
#!/usr/bin/env bash
HEALTH_URL="http://localhost:6333/"  # NOTE: root /, NOT /health (404 on v1.17+)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HEALTH_URL" 2>/dev/null)

if [ "$HTTP_CODE" != "200" ]; then
    echo "[QDROWN] Qdrant health check failed (HTTP $HTTP_CODE) — attempting restart..."
    PIDFILE="/home/lumi/.hermes/qdrant/qdrant.pid"
    [ -f "$PIDFILE" ] && { OLD_PID=$(cat "$PIDFILE"); kill -0 "$OLD_PID" 2>/dev/null && kill "$OLD_PID" 2>/dev/null; rm -f "$PIDFILE"; }
    bash /home/lumi/.hermes/qdrant/start-qdrant.sh 2>&1
    sleep 2
    RETRY_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:6333/" 2>/dev/null)
    [ "$RETRY_CODE" = "200" ] && echo "[QDRESTORED] Qdrant restarted successfully!" || echo "[QDFAIL] Qdrant still down after restart. HTTP $RETRY_CODE"
fi
exit 0  # silent when healthy
```

**Cron job** (Hermes cronjob tool):
```
name: qdrant-health-watchdog
schedule: every 5h
no_agent: true
script: check-qdrant.sh
deliver: discord    # or wherever you want alerts
```

**Design principles:**
- `no_agent=true` — no LLM cost per tick, just runs the script
- **Silent on success** — no output = no message sent. The watchdog disappears when healthy.
- **Self-healing** — tries to restart before alerting you
- Use `notify_on_complete` equivalent? No — `no_agent` scripts deliver their stdout verbatim. Healthy = empty stdout = no delivery. Broken = stdout with error = delivered.

> **Important:** The Qdrant v1.17+ health check uses root `/` not `/health`. The `start-qdrant.sh` MUST check `http://localhost:6333/` (root) for its health loop, not `/health` which returns 404. This is the #1 source of false-positive restart loops.
>
> **Watchdog false-alarm pitfall** (discovered Aug 2026): If the watchdog reports "QDROWN" every cycle but Qdrant is actually healthy, check which URL the watchdog script uses. `http://localhost:6333/health` returns 404 on v1.17+, making the watchdog think Qdrant is down. It panic-restarts, moving aside non-corrupted collections in the process. Fix: use `http://localhost:6333/` (root) or `http://localhost:6333/collections` instead.

---

## 2. Incremental Memory Indexer

A cursor-based script that indexes new conversation messages into Qdrant's `vesper_session_archive` (or any 384-dim collection) without re-processing everything each run.

**Script** (`~/.hermes/profiles/vesper/scripts/vesper-memory-indexer.py`):
Uses fastembed (BAAI/bge-small-en-v1.5, 384-dim, local, no API credits). No OpenRouter dependency.

**Key design choices:**
- **fastembed (local)** — BAAI/bge-small-en-v1.5, 384-dim, ONNX, no API calls, no credits. Installed in both the tools Python AND the Hermes venv.
- **Cursor file** — stores last-indexed message ID. Each run only processes `WHERE id > cursor`. O(new), not O(all).
- **Silent when idle** — prints nothing when no new messages. Perfect for `no_agent` cron.
- **Batch to Qdrant** — chunks of 8 points with 0.2s delay between batches.
- **Backfill mode** — `--backfill` flag processes ALL messages, deduplicating against existing Qdrant point IDs.
- **Status mode** — `--status` prints collection count, DB session/message counts, and current cursor.

**Cron job:**
```
name: Vesper Memory Indexer
schedule: every 5m
no_agent: true
script: vesper-memory-indexer.py
workdir: /home/lumi/.hermes/profiles/vesper
deliver: origin
```

> **⚠️ CURSOR CORRUPTION PITFALL (verified 2026-10-30):** After a state.db recovery or restore, the `.memory_cursor` file may point at a message ID far beyond the actual max ID in state.db (e.g., cursor=201031 when max(id)=4305). The indexer then finds 0 new messages every run and silently does nothing — no error, no warning, just nothing. **Diagnose:** `cat .memory_cursor` vs `SELECT MAX(id) FROM messages`. If cursor > max_id, reset: `echo 0 > .memory_cursor` then run `--backfill`. The backfill deduplicates against existing Qdrant points, so it's safe to re-run.

> **⚠️ SILENT STALL (fixed 2026-10-18):** When embeddings fail (e.g., 402 from OpenRouter), the indexer used to print "Cursor advanced" unconditionally. Now guarded: prints `[!] Cursor NOT advanced` when nothing indexed. But with fastembed, 402s are no longer possible — embeddings are local.

### ⚠️ Silent stall when the embedding provider runs out of credits — and a log line that LIES

**Observed 2026-10-12 → 10-18.** OpenRouter credits ran out ($135.00 used / $135.20 charged).
Every 5-minute tick got `HTTP 402: Payment Required` on the embedding call, indexed 0 chunks —
and printed:

```
[+] Indexed 0 chunks (68 errors)
[+] Cursor advanced to 197074      ← FALSE. The cursor never moved.
```

The script only *wrote* the cursor when `indexed > 0`, but printed "Cursor advanced"
**unconditionally**. So `cron/output/<id>/*.md` read as a run of successful ticks while
`.memory_cursor` sat frozen at 195597 and ~1,500 messages piled up unindexed. The stall was
invisible for six days — and the health watchdog stayed silent too, because the *job's*
`last_status` was `ok` (the script exits 0 even when every chunk fails).

**Diagnose a stalled indexer in ten seconds — never trust the log line:**

```bash
cat .memory_cursor          # on disk — this is the truth
python3 -c "import sqlite3;print(sqlite3.connect('state.db').execute('select max(id) from messages').fetchone()[0])"
```

If `max(id) − cursor` is large and growing, the indexer is stalled no matter what the log says.

**Fix applied 2026-10-18:** the "Cursor advanced" print is now guarded on `indexed > 0`; when
nothing indexed it prints `[!] Cursor NOT advanced — still at <n> (<n> chunks failed)`.

**Rules that fall out of this:**

- **No data is lost.** The cursor only advances on real progress, so a backfill from the
  frozen cursor recovers everything cleanly once embeddings work again. A stalled indexer is
  a *pause*, not a loss — say that plainly rather than implying lost memories.
- **A cron script that exits 0 on total failure is invisible to a status-based watchdog.**
  If a script can fail "successfully," make it exit non-zero or print a distinguishing line —
  otherwise `last_status: ok` hides it. (Same family as the watchdog stale-latch bug in
  `devops/self-management`: key the alert on the *event*, not on a lagging status field.)
- **Out-of-credit hits the indexer before any LLM job.** Embeddings return 402 the moment the
  balance goes negative; chat jobs may still work. So when *semantic recall* goes stale while
  chat feels fine, check the embedding provider's balance first.
- **Recovery is cheap — don't wait.** The whole backlog here was ~927K tokens ≈ **$0.12** at
  text-embedding-3-large rates. Backfilling is trivially inexpensive; the expensive mistake is
  leaving the gap open for a week.
- **A 402 is a *billing* signal, not a *transient* one.** Unlike a 429 (retry later), a 402
  will never clear on its own — escalating "it'll catch up next tick" is the wrong call. The
  indexer's own retry loop only handles 429; anything else raises straight through.

---

## 5. Daily Health Monitoring Cron

A daily (not every-5-minutes) cron that checks Qdrant health, point counts, search functionality, and embedding type. Delivers a brief summary to the user. Useful after migrations or when watching for regressions.

**Script pattern** (agent-run, not no_agent — needs reasoning to assess anomalies):

```
name: Qdrant & Memory Daily Tracker
schedule: every day at 9am
deliver: origin
prompt: |
  Run a daily health check on Qdrant and memory systems:
  1. Check Qdrant collections via HTTP API — report point counts, verify 384-dim.
  2. Check memory usage — char counts vs limits (6000 memory, 3500 user).
  3. Test Qdrant search — embed a test query via fastembed, verify Python float (not numpy.float32), search vesper_memory, report results and top score.
  4. Check plugin availability — fastembed importable in Hermes venv.
  5. Append results to state/qdrant-daily-log.md with today's date.
  6. Report brief summary. Note any anomalies.
```

**Key checks after fastembed migration:**
- Point counts stable (no unexpected drops)
- All collections 384-dim
- Search returns results (not empty)
- Embedding type is Python `float` (not `numpy.float32`)
- fastembed importable in Hermes venv
- Memory char usage vs limits

**Design principles:**
- Agent-run (not no_agent) — needs reasoning to assess anomalies
- Daily cadence — not every 5 minutes (that's the indexer's job)
- Delivers to user — this is a report, not a silent watchdog
- Logs to file — accumulates data for trend analysis over days

**When to use:** After any migration, embedding change, or plugin update. Run for a few days, then review the accumulated log with the user to decide if further tweaks are needed.

```
Health Watchdog (every 5h)           Memory Indexer (every 5m)
       │                                      │
       ▼                                      ▼
┌──────────────┐                     ┌──────────────────┐
│ Check Qdrant  │──── healthy ─────▶ │ (silent, no-op)   │
│ HTTP 200?     │                     └──────────────────┘
└──────┬───────┘
       │ unhealthy
       ▼
┌──────────────┐     success     ┌──────────────────┐
│ Auto-restart  │──────────────▶ │ Resume indexing   │
│ Qdrant        │                └──────────────────┘
└──────┬───────┘
       │ failure
       ▼
┌──────────────────────┐
│ Alert user via Discord │
└──────────────────────┘
```

The two cron jobs are independent but complementary:
- The **watchdog** (5h) keeps Qdrant running — if it crashes, it auto-restarts before the indexer's next tick.
- The **indexer** (5m) keeps memory fresh — if Qdrant was briefly down, the indexer will catch up next run.
- No single point of failure: if one cron job fails, the other still operates.

---

## 4. First-Run Catchup

After deploying a fresh indexer (or after recovering from a long Qdrant outage), run a one-time backfill to index all historical messages:

```bash
cd ~/.hermes/profiles/vesper
python3.12 scripts/vesper-memory-indexer.py --backfill
```

This loads sentence-transformers (takes ~30s first time), scans all messages, deduplicates against existing Qdrant points, and indexes everything new. After it finishes, the incremental cron takes over seamlessly.

> **⚠️ Cursor pitfall:** The `--backfill` flag skips cursor advancement (by design — it processes everything, not just new messages). After backfill completes, you MUST manually set the cursor to the latest message ID so the incremental cron doesn't try to re-index everything on its next tick:
>
> ```bash
> cd ~/.hermes/profiles/vesper
> python3.12 -c "import sqlite3; conn = sqlite3.connect('state.db'); print(conn.execute('SELECT MAX(id) FROM messages').fetchone()[0])"
> # Then write that number to .memory_cursor:
> echo '<max_id>' > .memory_cursor
> ```
>
> Without this step, the first incremental tick sees cursor=0 and tries to process all messages again — leading to a timeout (the script tries to index 1800+ chunks) and repeated cron failures. The backfill already indexed those chunks; the cursor must reflect that progress.
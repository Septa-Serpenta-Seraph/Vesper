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

A cursor-based script that indexes new conversation messages into Qdrant's `vesper_session_archive` collection without re-processing everything each run.

> **⚠️ CRITICAL PITFALL: `sentence-transformers` breaks in cron environments.** The `regex` dependency has a circular import bug (`ImportError: cannot import name '_regex' from partially initialized module 'regex'`) that only triggers when the script runs in cron's minimal environment — not in your interactive terminal. This happens even with the correct shebang and user site-packages in `sys.path`.
>
> **Fix:** Use the **OpenRouter embeddings API** (`text-embedding-3-large`, 3072-dim) instead of local `sentence-transformers` for cron scripts. The same OPENROUTER_API_KEY used for LLM calls works for embeddings. Example:
> ```python
> import urllib.request, json
> def get_embedding(text):
>     body = json.dumps({"model": "openai/text-embedding-3-large", "input": text[:8000], "dimensions": 3072}).encode()
>     req = urllib.request.Request("https://openrouter.ai/api/v1/embeddings", data=body,
>         headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, method="POST")
>     return json.loads(urllib.request.urlopen(req, timeout=30).read())["data"][0]["embedding"]
> ```
> The existing `backfill-vesper-memory.py` script already uses this pattern and works reliably in both interactive and cron environments.

A cursor-based script that indexes new conversation messages into Qdrant's `vesper_session_archive` (or any 384-dim collection) without re-processing everything each run.

**Script** (`~/.hermes/profiles/vesper/scripts/vesper-memory-indexer.py`):
```python
#!/usr/bin/python3.12
""""
Incremental indexer using OpenRouter embeddings via text-embedding-3-large.
API-based, NOT local sentence-transformers (which breaks in cron environments
due to a circular import in the `regex` dependency).
Tracks last-indexed message ID via .memory_cursor file.
"""
import hashlib, json, os, sqlite3, time, urllib.request
from pathlib import Path

PROFILE_DIR = Path.home() / ".hermes" / "profiles" / "vesper"
STATE_DB = PROFILE_DIR / "state.db"
CURSOR_FILE = PROFILE_DIR / ".memory_cursor"
ENV_PATH = Path.home() / ".hermes" / ".env"
QDRANT_URL = "http://localhost:6333"
COLLECTION = "vesper_session_archive"  # 384-dim
EMBED_MODEL = "openai/text-embedding-3-large"
EMBED_DIMS = 384  # MUST match collection dimension!

# For full implementation, see the actual file at
# ~/.hermes/profiles/vesper/scripts/vesper-memory-indexer.py
```

**Key design choices:**
- **Local embeddings** — sentence-transformers/all-MiniLM-L6-v2, 384-dim. No API key, no rate limits, works offline.
- **Cursor file** — stores last-indexed message ID. Each run only processes `WHERE id > cursor`. O(new), not O(all).
- **Silent when idle** — prints nothing when no new messages. Perfect for `no_agent` cron.
- **Batch to Qdrant** — chunks of 16 points with 0.1s delay between batches to avoid hammering.
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

> **Why 5 minutes instead of 2?** The 2-minute cron from Lumi used a full LLM agent (expensive tokens per tick). Our no_agent script runs a local embedding model — 5 minutes is plenty responsive, and avoids hammering Qdrant with tiny writes.

> **⚠️ VECTOR DIMENSION MUST MATCH COLLECTION.** This was the #1 source of silent failures in the initial deployment. The `vesper_session_archive` collection stores **384-dim** vectors (originally set up via sentence-transformers/all-MiniLM-L6-v2). The OpenRouter `text-embedding-3-large` model defaults to **3072-dim**. If you send a 3072-dim vector to a 384-dim collection, Qdrant returns `HTTP 400 Bad Request` — silently (no obvious error in cron output).
>
> The fix: pass `"dimensions": 384` in the OpenRouter embedding request body. `text-embedding-3-large` supports arbitrary dimensions from 256 to 3072 via this parameter.
>
> ```python
> body = json.dumps({
>     "model": "openai/text-embedding-3-large",
>     "input": text[:8000],
>     "dimensions": 384,  # critical — must match target collection
> }).encode()
> ```
>
> Collection dimension check: `curl -s http://localhost:6333/collections/<name>` and look for `config.params.vectors.size`.
>
> **Dimension reference:**
> | Collection | Dim | Notes |
> |---|---|---|
> | `<name>_session_archive` | 384 | original sentence-transformers setup |
> | `<name>_memory` | 3072 | OpenRouter default, plugin primary |
> | `<name>_lorebooks` | 3072 | lorebook auto-inject |

---

## 3. Combined Reliability Strategy

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
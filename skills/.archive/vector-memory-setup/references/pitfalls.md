# Qdrant Memory System — Pitfalls & Gotchas

## Critical Pitfalls

### 1. Qdrant Point IDs Must Be UUIDs or Unsigned Integers
Qdrant rejects arbitrary string IDs. Valid formats:
- UUID: `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`
- Unsigned integer: `12345`

Hex hashes (e.g., `"748fe6c84720fae3"`) are **NOT valid**. Convert them:

```python
import hashlib
def to_qdrant_uuid(text: str) -> str:
    h = hashlib.md5(text.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
```

Using `uuid.uuid4()` also works but is non-deterministic. For idempotent re-indexing, hash-based deterministic UUIDs are preferred.

### 2. execute_code Sandbox Has No System Packages
The `execute_code` tool runs in a sandboxed Python environment. System-installed packages (`sentence-transformers`, `qdrant-client`, `numpy`, `torch`, etc.) are **NOT available**. Any script that imports these MUST be run via `terminal()`.

```python
# FAILS: ModuleNotFoundError
execute_code(code="from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2')")

# WORKS: runs in real system Python
terminal(command="python3 ~/.hermes/qdrant/seed-memory.py")
```

This applies to ALL system packages, not just ML ones.

### 2b. Background Process Wrappers Cause Exit Code 127
Using `nohup`, `disown`, or trailing `&` inside a `terminal()` command string causes "command not found" (exit 127). Hermes rejects shell-level background wrappers in foreground mode.

```python
# EXIT 127: shell wrapper inside terminal string
terminal(command="nohup /path/qdrant --config /path/config.yaml > /path/log 2>&1 &")

# CORRECT: use background=true parameter
terminal(background=True, command="/path/qdrant --config-path /path/config.yaml > /path/log 2>&1")
```

### 3. Binary in /tmp Disappears on Reboot
`/tmp` is cleaned on VM reboot. Always store the Qdrant binary in a persistent location:
```bash
mkdir -p ~/.hermes/qdrant
cp /tmp/qdrant ~/.hermes/qdrant/qdrant
chmod +x ~/.hermes/qdrant/qdrant
```

### 4. Embedding Dimension Mismatch
A 384d model (MiniLM) cannot populate a 3072d collection (stella). Match model output dimension to collection config. If you need to switch dimensions, recreate the collection.

**Corollary — the agent's own recall tool hits this wall.** `qdrant_recall`
embeds its query at the *primary* memory dimension (3072) and therefore cannot
search a 384-dim `<name>_session_archive`. It does not error; it returns
`{"results": [], "count": 0}`. Data can be perfectly present and still be
invisible to that tool. Verify with a **direct 384-dim query vector** against
`POST /collections/<name>/points/search`, and treat `0.4–0.5` cosine as a normal
hit for the small model. See `embedding-provider-outage-recovery.md` §5.

### 5. Forgetting Payload Indexes
Without payload indexes, filtered searches are O(n). Always index fields you filter on:
```python
client.create_payload_index(collection_name="...", field_name="source", field_schema="keyword")
client.create_payload_index(collection_name="...", field_name="type", field_schema="keyword")
client.create_payload_index(collection_name="...", field_name="timestamp", field_schema="integer")
```

> **`order_by` on `points/scroll` needs an index.** Ordering a scroll by a payload
> field that has no range index returns `HTTP 400 Bad Request` with no helpful
> message. Either create a range payload index first, or skip `order_by` and
> sort client-side after fetching.

### 6. Disk Space During Installation
`sentence-transformers` needs ~2-4GB. If disk is tight, clean pip cache first (`rm -rf ~/.cache/pip`), install qdrant-client first (small), then sentence-transformers. If still failing, expand the VM disk.

### 7. No sudo Access
The agent may not have `sudo`. Don't assume `journalctl --vacuum-time=3d` or `apt-get clean` will work. Focus on user-space cleanup.

### 8. Session Indexing: Use `hermes sessions export` (Not Direct SQLite)

The `hermes sessions export --session-id <id> <file>` command is the cleanest way to extract session data — it handles the DB query and produces structured JSONL. Avoid reading `state.db` directly unless the CLI export is unavailable.

**To get ALL session IDs** (not just the default 20):
```bash
hermes sessions list --limit 200
```
The last column of each line is the session ID.

### 9. session_search vs Qdrant: Two Complementary Search Tools

| Tool | Type | Best For |
|---|---|---|
| `session_search` | FTS5 exact-text search | Finding specific quoted text, exact phrases |
| `Qdrant semantic search` | Vector similarity | Finding conversations by topic/theme even if wording differs |

Use `session_search` first for exact matches, then Qdrant for broader semantic recall. They index different data: `session_search` covers the SQLite FTS5 index (updated by Hermes), Qdrant covers what you've manually indexed + what the qdrant-memory plugin auto-stores.

### 10. VM Disk Expansion (Hyper-V)

When running out of disk space on a Hyper-V VM:

1. Shut down the VM fully (not save-state)
2. In Hyper-V Manager: Edit Disk → Expand → set new size (e.g., 600 GB)
3. Boot VM, then run:
```bash
sudo parted /dev/sda resizepart 3 100%
sudo pvresize /dev/sda3
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```
4. Verify: `df -h /`

**Always persist the Qdrant binary before reboot** — `/tmp` gets cleaned.

### 11. Search Endpoints: `/points/query` vs `/points/search`

Qdrant ≥1.10 exposes **both**:
- `POST /collections/{name}/points/query` — the newer idiom (named-vector aware,
  returns `{"result": {"points": [...]}}`).
- `POST /collections/{name}/points/search` — the older idiom, still served by
  **v1.18.2** (returns `{"result": [{...}, ...]}`). **Verified working
  2026-10-18** with `{"vector": [...], "limit": 4, "with_payload": true}`.

> **Correction to earlier guidance:** an older revision of this file claimed
> `/points/search` always returns HTTP 400 on v1.18.2. That is **wrong** — it was
> diagnosed from a malformed payload, not from the endpoint. Do not avoid a
> working endpoint on the strength of a bad error message.

If either endpoint returns **400**, the cause is almost always the **payload
shape**, not the route. Check in this order: (1) is the key `vector` (or
`query`) — not `embedding`? (2) does the vector length match the collection
dimension exactly? (3) any `order_by` without a range payload index?

The `qdrant-client` Python library uses `client.query_points()`.

### 12. `execute_code` Is Fully Blocked (Not Just System Packages)

The `execute_code` tool is completely blocked for arbitrary Python — not just system packages. The error is:
```
BLOCKED: execute_code runs arbitrary local Python
```
Any Python that imports `sentence-transformers`, `qdrant-client`, `urllib`, `json`, etc. must run via `terminal(command="python3 ...")`.

### 13. Short embedding probes lie when the account is depleted

**The highest-value pitfall in this file.** An out-of-credit embedding account
does not reject everything — it enforces a token ceiling (~17 tokens on a
depleted OpenRouter tier). So:

- one-line probe → **HTTP 200** ✅ (looks healthy)
- real 700-token chunk → **HTTP 402** `Prompt tokens limit exceeded` ❌

Every health check built on a short string will report a dead provider as alive.
**Probe with 600+ tokens**, and decide from `GET /api/v1/credits`
(`total_credits - total_usage`), *not* `/api/v1/auth/key` (per-key usage, not the
balance). Full detect → verify → drain → confirm playbook:
`embedding-provider-outage-recovery.md`.

### 15. fastembed Returns numpy.float32 — Silent JSON Serialization Failure

**The highest-value pitfall from the fastembed migration (2026-10-27).** fastembed's `TextEmbedding.embed()` returns vectors of `numpy.float32` values. Python's `json` module and `requests.post(json=payload)` **cannot serialize** `numpy.float32` — but the exception is caught by the plugin's `except` block, so the failure is **silent**: search returns `[]` with no error.

**Symptom:** `qdrant_recall` returns `{"results": [], "count": 0}` even though the collection has thousands of points with correct 384-dim vectors. Direct search with the stored vector works (score 1.0). The stored vectors and fresh embeddings are cosine-identical. The only difference is the serialization path.

**Root cause:** `_EmbeddingClient.embed()` returns `list(vecs[0])` — the elements are `numpy.float32`, not Python `float`. When the plugin builds the JSON payload for the Qdrant search API, `requests.post(json=payload)` raises `TypeError` (not JSON serializable), caught by the except block, returning empty results.

**Fix:** Always convert numpy floats to Python floats in the embed method:
```python
return [float(x) for x in vecs[0]]  # NOT list(vecs[0])
```

**Debugging methodology when search returns 0 results:**
1. Verify points exist: `POST /collections/<name>/points/scroll` with `with_vector: true`
2. Embed the exact same text from a stored point
3. Compare stored vector vs fresh embedding (cosine similarity)
4. If cosine = 1.0 but search returns 0 → check the embedding type (`type(vec[0])`)
5. If it's `numpy.float32` → that's the bug. Convert to `float()`.

**General rule:** Any time you use a numpy-based embedding library (fastembed, sentence-transformers, etc.) and send vectors via HTTP/JSON, convert to Python `float()` first. This applies to Qdrant, Pinecone, Weaviate, or any REST API.

The session indexer printed `[+] Cursor advanced to <n>` unconditionally while
the actual `write_cursor()` call was guarded on `indexed > 0`. Result: six days
of failed runs logged as success, invisible to the watchdog (which saw
`last_status: ok`).

**Pattern rule:** if a script prints a success claim, the print must be guarded
by the *same condition* as the mutation, and should print the failure branch
explicitly (`[!] Cursor NOT advanced — still at <n>`). Then verify the artifact
on disk — `cat .memory_cursor` vs `SELECT MAX(id) FROM messages` — never the log.

## Less Critical But Useful

- Seed immediately after creating collections — empty collections are useless
- Create a cron job for auto-restart — Qdrant won't survive reboots without it
- Test search after seeding — verify embeddings are actually retrievable
- Keep a README documenting your specific setup in `~/.hermes/qdrant/README.md`
- After indexing sessions, expect ~3-5x the original lorebook chunk count — plan disk accordingly
- A stalled indexer loses **nothing**: the cursor only advances on real progress,
  so a backfill from the frozen cursor recovers every message. Say this early —
  the instinct on finding a multi-day stall is to panic.
- When draining a parked-text queue (`state/pending-archives.md`), **skip entries
  marked `[superseded ...]`** — they are merged copies already in the batch, and
  archiving them duplicates recall results.

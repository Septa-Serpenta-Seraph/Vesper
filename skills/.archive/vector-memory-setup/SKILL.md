---
name: vector-memory-setup
description: "Set up and manage Qdrant vector DB for persistent AI agent memory. Covers native binary deployment (no Docker), the Hermes qdrant-memory plugin, embedding generation, seeding from lorebooks, and ongoing maintenance. Trigger when the user wants to configure, troubleshoot, or expand a Qdrant-based memory system."
version: 1.2.0
platforms: [linux]
metadata:
  hermes:
    tags: [qdrant, vector-db, memory, embeddings, sentence-transformers, self-hosted, plugin]
---

# Vector Memory Setup

Deploy and maintain a Qdrant vector database for persistent agent memory. Covers both the **Qdrant database server** and the **Hermes memory plugin** that connects agent memory to it.

## Architecture

```
Agent ↔ Hermes memory system ↔ qdrant-memory plugin ↔ Qdrant (localhost:6333)
                                      ↕
                           fastembed (BAAI/bge-small-en-v1.5, 384-dim, local ONNX)
                                      ↕
                           Lorebooks / session summaries
```

**Embedding (single tier, 384d):** fastembed `BAAI/bge-small-en-v1.5` — local ONNX, no API calls, no credits. Used by the qdrant plugin for ALL collections. Migrated from 3072-dim OpenRouter (text-embedding-3-large) on 2026-10-27; no OpenRouter embedding dependency remains.

> **⚠️ fastembed must be installed in the Hermes venv** (not just the tools Python) or `initialize()` fails the embedding test and `_available` stays False. Install with: `uv pip install --python <hermes-venv-python> fastembed`. See Troubleshooting section.

## Collection Naming

| Collection | Dimension | Use |
|---|---|---|
| `intelligent_gould_<name>` | 384 | Primary memory — semantic recall (plugin collection, fastembed) |
| `<name>_session_archive` | 384 | Compressed session summaries (fastembed) |
| `<name>_entities` | 384 | Extracted entities/relationships (fastembed) |
| `<name>_research` | 384 | Research notes and findings (fastembed) |
| `<name>_memory` | 384 | Per-profile memory (fastembed) |
| `<name>_lorebooks` | 384 | Per-profile lorebook auto-inject (fastembed) |

> **Per-profile collections:** Each Hermes profile can have its own collections (e.g. `vesper_memory`, `vesper_lorebooks`). The plugin config is global — only ONE collection is active at a time. Use per-profile cron jobs or scripts for the others.

---

## PART 1: Qdrant Database Server

### Deployment: Native Binary (No Docker)

```bash
cd /tmp
curl -sL "https://github.com/qdrant/qdrant/releases/download/v1.18.2/qdrant-x86_64-unknown-linux-gnu.tar.gz" -o qdrant.tar.gz
tar xzf qdrant.tar.gz
rm qdrant.tar.gz
mkdir -p ~/.hermes/qdrant
mv qdrant ~/.hermes/qdrant/qdrant
chmod +x ~/.hermes/qdrant/qdrant
```

### Config File

`~/.hermes/qdrant/config.yaml`:

```yaml
qdrant:
  log_level: INFO
storage:
  storage_path: /home/<user>/.hermes/qdrant/storage
  snapshots_path: /home/<user>/.hermes/qdrant/snapshots
  on_disk_payload: true
service:
  http_port: 6333
  grpc_port: 6334
  host: 0.0.0.0
cluster:
  enabled: false
```

### Start Script

`~/.hermes/qdrant/start-qdrant.sh` — uses root `/` for health check, NOT `/health`:

```bash
#!/usr/bin/env bash
QDRANT_BIN="/home/<user>/.hermes/qdrant/qdrant"
CONFIG="/home/<user>/.hermes/qdrant/config.yaml"
LOG="/home/<user>/.hermes/qdrant/qdrant.log"
PIDFILE="/home/<user>/.hermes/qdrant/qdrant.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Qdrant already running (PID $(cat "$PIDFILE"))"
    exit 0
fi

if [ ! -f "$QDRANT_BIN" ]; then
    echo "Downloading Qdrant..."
    cd /tmp
    curl -sL "https://github.com/qdrant/qdrant/releases/download/v1.18.2/qdrant-x86_64-unknown-linux-gnu.tar.gz" -o qdrant.tar.gz
    tar xzf qdrant.tar.gz
    mv qdrant "$QDRANT_BIN"
    rm qdrant.tar.gz
    chmod +x "$QDRANT_BIN"
fi

nohup "$QDRANT_BIN" --config-path "$CONFIG" > "$LOG" 2>&1 &
echo $! > "$PIDFILE"

for i in $(seq 1 15); do
    if curl -s -o /dev/null -w '%{http_code}' http://localhost:6333/ | grep -q '200'; then
        echo "Qdrant is healthy!"
        exit 0
    fi
    sleep 1
done
echo "Qdrant may not be ready — check $LOG"
```

> **Qdrant v1.17+ removed `/health`** (returns 404). Always use root `/` for health checks. This is the #1 source of "Qdrant looks unhealthy but is running fine" false alarms.
>
> **Watchdog false-alarm pitfall:** If the `check-qdrant.sh` watchdog reports "QDROWN" every cycle but Qdrant is actually serving collections normally, the watchdog script may be checking the wrong health URL. The script must use `http://localhost:6333/` (root, returns 200 when healthy) or `/collections` (also returns 200), NOT `/health` (returns 404 on v1.17+). A `/health` URL causes the watchdog to falsely detect Qdrant as down and panic-restart every 5 hours, moving aside non-corrupted collections in the process.

### Process Management

**Qdrant runs as a systemd USER service (since 2026-08-19 — the durable fix).**

> **Why (history):** Qdrant was originally a manually-started orphan process
> (`start-qdrant.sh` / `terminal(background=True)`). On 8/19 a gateway restart
> KILLED it — the process tree died with the old gateway, taking all memory
> down with it (caught by verification, not the boot hook). Converted to a
> systemd user service so it survives gateway restarts and VM reboots.

```bash
# Status / start / stop / restart / logs
systemctl --user status qdrant
systemctl --user start qdrant
systemctl --user stop qdrant
systemctl --user restart qdrant
journalctl --user -u qdrant -n 50

# Enabled (auto-start at boot) + linger (user services run without login)
systemctl --user enable qdrant
loginctl enable-linger lumi
```

Unit: `~/.config/systemd/user/qdrant.service` — `Type=simple`,
`WorkingDirectory=/home/lumi/.hermes/qdrant`,
`ExecStart=/home/lumi/.hermes/qdrant/qdrant --config-path ./config.yaml`,
`Restart=on-failure`.

Health check: `curl -s http://localhost:6333/collections/vesper_memory` →
`points_count` + `status: green` (use root `/` or `/collections` — `/healthz`
404s on v1.18+). If Qdrant is down after a restart, it's the service:
`systemctl --user start qdrant`, then verify the collection count matches
(2,323 pts as of 8/19) — never assume the old manual process is still running.

The legacy `start-qdrant.sh` (nohup + PIDFILE) still exists but is SUPERSEDED
— do not resurrect it; the systemd unit does the same job durably.

**Do NOT use `nohup`/`disown`/`&` inside `terminal()`** — use
`terminal(background=True)` for short-lived helpers, and prefer the systemd
service for anything that must outlive the gateway.

---

## PART 2: Hermes Qdrant Memory Plugin

The qdrant-memory plugin is a separate component from the Qdrant database server. It implements `MemoryProvider` ABC and bridges Hermes agent memory ↔ Qdrant.

### Plugin File Structure

```
~/.hermes/profiles/<profile>/plugins/qdrant/
├── __init__.py      # QdrantMemoryProvider implementation
└── plugin.yaml      # Metadata
```

> **PROFILE ISOLATION (v0.18.2+):** `get_hermes_home()/plugins/` resolves to the **profile-specific** directory (`~/.hermes/profiles/<name>/plugins/`), NOT the shared `~/.hermes/plugins/`. Installing plugins in the shared dir makes them invisible to the profile-scoped discovery system.

### plugin.yaml

```yaml
name: qdrant
version: 2.0.0
description: "Local Qdrant vector database — semantic recall over conversation history via local fastembed embeddings (BAAI/bge-small-en-v1.5, 384-dim). No API calls, no credits."
hooks:
  - on_session_end
```

> **The `name` field is display-only.** The plugin system discovers providers by **directory name**, not by the `name` field. The directory name MUST match `memory.provider` in config.yaml.

### CRITICAL: Directory Name Must Match Config

| Config value | Directory must be |
|---|---|
| `memory.provider: qdrant` | `plugins/**qdrant**/` |
| `memory.provider: qdrant-memory` | `plugins/**qdrant-memory**/` |

A mismatch means `find_provider_dir()` returns `None` and the dashboard shows "**missing**."

### Required Code Patches for Qdrant v1.18.2

**Patch 1: Health check endpoint**

The `_QdrantRestClient.health()` method defaults to `/healthz` which returns 404 on v1.18.2:

```python
def health(self) -> bool:
    try:
        r = requests.get(f"{self.base_url}/", timeout=5)  # NOT /healthz
        return r.status_code == 200
    except Exception:
        return False
```

**Patch 2: is_available() static check**

The discovery system calls `is_available()` immediately after instantiation (before `initialize()`). The ABC says: "Should not make network calls — just check config and installed deps." The default `return self._available` (initially False) means the dashboard **always** shows the plugin as unavailable:

```python
def is_available(self) -> bool:
    if self._available:
        return True
    try:
        import requests
        return requests is not None
    except ImportError:
        return False
```

### Config.yaml

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: qdrant              # Must match plugin directory name
  nudge_interval: 10
  flush_min_turns: 6

plugins:
  qdrant-memory:
    qdrant_url: http://localhost:6333
    collection: intelligent_gould_<name>
    prefetch_limit: 5
    recency_weight: 0.3
  enabled:
    - qdrant
```

> **Two different `qdrant` references:** `memory.provider: qdrant` selects the memory provider for recall. `plugins.enabled: [qdrant]` activates the plugin for hooks. Both should reference the same thing.

### Tuning Recall Quality

The plugin's `qdrant-memory` section exposes three knobs that directly affect how well semantic recall works:

| Parameter | Default | Effect | Recommendation |
|---|---|---|---|
| **`prefetch_limit`** | 5 | How many candidate vectors Qdrant pulls per query. Too low = good matches can be cut off before they're scored. | **10** (set 8/19; recall oversamples `min(limit*4, 40)`). Higher = more tokens per query, fewer false negatives. |
| **`recency_weight`** | 0.3 | Balance between semantic similarity (0.0) and recency (1.0). | **0.35** (set 8/19). Kind-aware decay now handles the aging curve — see `references/qdrant-salience-2026.md`. |
| **`half_life_days`** | — | Per-kind aging: `{ephemeral: 30, event: 90, preference: 365, belief: 0}`. Belief = immortal; ephemera fade, never hard-discarded (soft floor only). | Keep as set; formula + verification in `references/qdrant-salience-2026.md`. |
| **`reconsolidation_debounce_h`** | 6 | Phase-2 reconsolidation: recalled memories get `recall_count+1` + fresh `last_accessed` via debounced best-effort writes (≤1 write per point per window). Makes "remembering strengthen the memory". | Keep 6; safe to leave — writes are debounced + try/except so they can never break recall. |
| **`flush_min_turns`** | 6 (under `memory:`) | How many conversation turns pass before messages are embedded and flushed to Qdrant. | **3–4** for short sessions. At 6, brief catch-ups (<6 turns) never get indexed. Lower = more frequent writes, better recall of short exchanges. |

**To adjust**, edit the profile's `config.yaml`:

```yaml
memory:
  flush_min_turns: 4          # Index messages sooner

plugins:
  qdrant-memory:
    prefetch_limit: 10        # Pull more candidates per query
    recency_weight: 0.4       # Slight recency boost over pure similarity
```

> **Note:** `flush_min_turns` is under `memory:`, not `plugins.qdrant-memory:`. It controls how often the memory system flushes to the provider. Lowering it means the Qdrant collection gets updated more frequently, which improves recall at the cost of slight write overhead.

### Embedding Dimension (All Collections: 384d)

All collections now use 384-dim fastembed (`BAAI/bge-small-en-v1.5`). The previous 3072-dim OpenRouter (text-embedding-3-large) was retired on 2026-10-27 — all collections migrated via `reembed-fastembed.py`. No dimension mismatch exists anymore.

**If a new collection is created**, use 384-dim to match. Cross-collection search works since all use the same model and dimension.

### Verifying Discovery

```python
from plugins.memory import discover_memory_providers, find_provider_dir, load_memory_provider

print(find_provider_dir("qdrant"))          # Expected: /home/lumi/.hermes/profiles/vesper/plugins/qdrant
for n, d, a in discover_memory_providers():
    print(f"{'✅' if a else '❌'} {n}")
p = load_memory_provider("qdrant")
print("Loaded:", p)
```

---

## Creating Collections

```python
import urllib.request, json

base = "http://localhost:6333"
collections = [
    {"name": "intelligent_gould_<name>", "vectors": {"size": 384, "distance": "Cosine"}, "on_disk_payload": True},
    {"name": "<name>_session_archive", "vectors": {"size": 384, "distance": "Cosine"}, "on_disk_payload": True},
]
for col in collections:
    data = json.dumps({"vectors": col["vectors"], "on_disk_payload": col["on_disk_payload"]}).encode()
    req = urllib.request.Request(f"{base}/collections/{col['name']}", data=data, headers={"Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Created: {col['name']}")
```

## Seeding Memory from Lorebooks

See `references/session-indexing.md` for the full pipeline. Quick version:

```bash
pip3 install --break-system-packages sentence-transformers
python3 ~/.hermes/qdrant/seed-memory.py
```

## Snapshot Backups → Private GitHub (8/11, live)

The durable off-machine backup pattern for Qdrant memory. Weekly cron, pure shell
(no_agent=true → ZERO tokens), snapshots → pull → push → rotate.

**Why snapshots, not incremental:** Qdrant's snapshot API is cheap and consistent
(55MB in ~0.5s). Incremental WAL diffs are fragile — one bad week corrupts the
chain. Full weekly snapshots are simple, always-valid, restorable.

**API:** `POST http://localhost:6333/collections/<name>/snapshots` → JSON
`{result: {name: "...snapshot", size: ...}}`; download with
`GET /collections/<name>/snapshots/<snapshot_name>`.

**Working script:** `scripts/qdrant-backup.sh` at
`profiles/vesper/scripts/qdrant-backup.sh` — snapshots vesper_memory +
vesper_session_archive, pulls to a staging dir, force-pushes to a single
`backup` branch, rotates via a `.manifest_<col>` file keeping the newest 4.

**Cron:** `qdrant-weekly-backup` (job 8f13ecd66313), Sunday 05:00 UTC, `no_agent=true`
with `script=qdrant-backup.sh` (relative filename — absolute paths are rejected).

**Privacy — CRITICAL:** the public `vesper-backup` repo is FILTERED (skills only,
never memories). Qdrant snapshots contain raw conversation history INCLUDING
intimate content — they must go to a **PRIVATE** repo, never the public one.
Fine-grained PAT scoped to ONLY that repo (Settings → Developer settings →
Fine-grained PAT → Contents: Read+Write), stored in
`scripts/.gh_token_private` (chmod 600). Verified repo: `RoundMetalBox/Vesper`.

**GitHub size limit handling (live since 2026-09-14):** GitHub warns on files
>50MB and **rejects** files >100MB (hard limit). vesper_memory (~63MB) triggers a
warning but pushes fine; vesper_session_archive hit 118MB on 2026-09-13 and was
**rejected outright**, causing the weekly backup to fail silently for a week
(deliver: local means nobody notices). The backup script was patched to
auto-split files ≥90MB into 80MB chunks via `split -b 80M` before `git add`,
with the original removed so only chunks are committed. Restore a snapshot from
chunks: `cat <base>.part* > <singlefile>`. The `scripts/qdrant-backup.sh` file
in this skill dir and the live copy at `profiles/vesper/scripts/qdrant-backup.sh`
both carry the fix. Verified live on 2026-09-14 — 119MB → 2 chunks pushed cleanly.

**Verify after first push:** clone the private repo back (`git clone --depth 1
https://x-access-token:<token>@github.com/<owner>/<repo>.git`) and confirm the
snapshots are present — don't trust the push output alone.

## Offloading Memory to Qdrant (move-don't-delete)

When the memory tool (MEMORY.md/USER.md) is near cap, **move** older facts to Qdrant
before removing them — never delete shared knowledge. This is Tyler's rule (8/11):
the always-on cap is a token budget, not a storage wall.

### The pattern (verified 2026-10-30)

1. **Identify stale or consolidatable entries** in MEMORY.md or USER.md.
2. **Offload to Qdrant** using fastembed (384-dim, local, no API calls):
   ```python
   # scripts/store_memory_qdrant.py
   import hashlib, json, time, urllib.request
   from fastembed import TextEmbedding

   text = "The fact to remember"
   model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
   vec = [float(x) for x in list(model.embed([text[:8000]]))[0]]

   ts = int(time.time() * 1000)
   pid = hashlib.sha256(text.encode()).hexdigest()[:32]
   payload = {
       "text": text,
       "timestamp": ts,
       "role": "assistant",
       "session_id": "memory-offload",
       "date_str": time.strftime("%Y-%m-%d"),
       "type": "archived",        # makes prefetch treat as belief (immortal)
       "source": "memory_prune",  # triggers belief kind in recall
       "kind": "belief",          # never decays
   }
   req = urllib.request.Request(
       "http://localhost:6333/collections/vesper_memory/points",
       data=json.dumps({"points": [{"id": pid, "vector": vec, "payload": payload}]}).encode(),
       headers={"Content-Type": "application/json"}, method="PUT",
   )
   with urllib.request.urlopen(req, timeout=30) as r:
       print(json.load(r)["status"])
   ```
3. **Verify retrieval** — run `qdrant_recall(query="...")` to confirm the fact
   is findable.
4. **Remove from MEMORY.md** — only after Qdrant confirms the point is stored.
5. **Log the move** in `state/system-change-log.md` and optionally save a one-line
   pointer in the scratchpad.

### Payload schema for archived memory entries

| Field | Value | Why |
|---|---|---|
| `type` | `"archived"` | Triggers belief kind in prefetch (immortal to decay) |
| `source` | `"memory_prune"` | Signals this came from a memory-tool consolidation |
| `kind` | `"belief"` | Half-life 0 = never decays; always findable |
| `timestamp` | ms-epoch | Required for date display and recency scoring |
| `id` | md5(text)[:32] | Idempotent — re-running won't create duplicates |

### Key rules

- **Move, don't delete.** The fact must be in Qdrant (verified by recall) before
  it leaves MEMORY.md. Tyler's explicit instruction: "NO destructive pruning."
- **Use fastembed, not OpenRouter.** All collections are 384-dim now. All active
  embedding scripts (archive-beliefs.py, vesper-memory-indexer.py,
  seed-desire-triggers.py, store_memory_qdrant.py) use fastembed (local, no
  credits). The only remaining OpenRouter embedding usage is in legacy scripts
  (index_lorebook.py, backfill-vesper-memory.py, incremental-vesper-memory.py,
  qdrant-reembed-zero.py) — these are broken (3072-dim into 384-dim) and not
  in active use. Do not use them until migrated.
- **Idempotent by text hash.** Re-running the script for the same text produces
  the same point ID — safe to retry.
- **Log the move.** Every offload gets a row in `state/system-change-log.md` so
  Tyler can dial back if needed.

### When to offload vs. when to just shorten

- **Shorten** entries that are still actively referenced (e.g., hardware specs,
  coffee prefs, gaming setup). Trim words, keep in memory.
- **Offload** entries that are historical/archival (e.g., a completed job
  pursuit, an old belief, a resolved debugging saga). They're findable via
  semantic search when needed.
- **Never offload** PIN entries (privacy, charter, consent) or the CURRENT STATE
  block — those are always-injected by design.

### Script location

`profiles/vesper/scripts/store_memory_qdrant.py` — CLI wrapper around the pattern
above. Usage:
```bash
python3 scripts/store_memory_qdrant.py --text "The fact to remember" --kind belief --source memory_prune
```

**archive-beliefs.py (updated 2026-10-30):** the reflection cron's archive tool
now uses fastembed (local, 384-dim) instead of OpenRouter. No API credits needed.
Previously failed silently when credits ran low. The script is at
`scripts/archive-beliefs.py` and works the same way — just no API key required.

The Hermes **memory tool** (always-on notes injected EVERY turn) and **Qdrant**
(vector search, queried on demand) are different systems with different budgets:

| | Memory tool | Qdrant |
|---|---|---|
| Injected every turn? | YES — every char costs tokens | No — searched on demand |
| Cap | `memory.memory_char_limit` / `user_char_limit` (config.yaml) | Disk (500+ GB free) |
| Right content | High-signal, still-true facts | Full history, searchable |

**When the memory tool rejects an add as full** (the cap is a TOKEN budget, not
a storage wall — Qdrant is effectively unlimited), consolidate with ONE batch:
- The batch `operations` array is checked against the cap on the FINAL result,
  so remove + add atomically in a single call.
- **Merging two entries requires ALSO removing the standalone source entry** —
  replacing A with "A+B" while B still exists is a net ADD and stays over cap
  (failed 4× on 8/11 before diagnosing; the working shape is
  `replace A (merged)` + `remove B` in the same operations array).
- Shorten verbose entries in the same batch; every char counts.

**Tyler's rule (8/11): NO destructive pruning.** The always-on cap is a token
budget, not a storage wall. When full, MOVE older facts down to Qdrant (still
searchable) — never delete anything shared; tell him when a move happens.

**Raising caps:** `hermes config set memory.memory_char_limit 6000` /
`memory.user_char_limit 3500` (raised 8/10 → 8/11). Config changes are cached —
a gateway restart is required to take effect in the live session (verified: the
restart is what made the new user cap live).

## Disk Space

| Component | Size |
|---|---|
| Qdrant binary | 82 MB |
| Qdrant storage (per 10K chunks) | ~15 MB |
| sentence-transformers + model | ~2-4 GB |
| Hermes agent venv | ~1.6 GB |
| **Minimum recommended** | **10 GB free** |

## Troubleshooting

**Plugin uses fastembed (not OpenRouter) for embeddings.** The qdrant plugin's `_EmbeddingClient` imports `fastembed.TextEmbedding` (BAAI/bge-small-en-v1.5, 384-dim). fastembed must be installed in the **Hermes venv** (not just the tools Python) or `initialize()` fails the embedding test and `_available` stays False:

```bash
uv pip install --python /home/lumi/.hermes/installs/*/environments/*/venv/bin/python3 fastembed
```

Verify: `<hermes-venv-python> -c "from fastembed import TextEmbedding; print('OK')"`

When the dashboard shows "External provider: qdrant — **missing**":

1. **Check the plugin directory is in the profile-specific path:**
   ```bash
   python3 -c "from hermes_constants import get_hermes_home; print(get_hermes_home() / 'plugins')"
   ls -la $(python3 -c "from hermes_constants import get_hermes_home(); print(get_hermes_home() / 'plugins')") 2>/dev/null
   ```

2. **Check directory name matches `memory.provider` config:**
   ```bash
   grep -A1 "provider:" ~/.hermes/config.yaml
   ls ~/.hermes/profiles/vesper/plugins/
   ```

3. **Test discovery directly (no side effects):**
   ```python
   import sys; sys.path.insert(0, '/home/lumi/.hermes/hermes-agent')
   from plugins.memory import discover_memory_providers, find_provider_dir
   print('find:', find_provider_dir('qdrant'))
   ```

4. **If `find_provider_dir` returns None**, the directory name doesn't match. Rename it.

5. **If `is_available()` returns False**, patch `__init__.py` to do a static check instead of returning `self._available`.

### Corrupted WAL Recovery

Qdrant can fail to start with a corrupted write-ahead log (WAL) in a collection:

```
Panic: Failed to load local shard ".../collections/<name>/0":
  Service internal error: Wal error: Can't init WAL: Kind(WouldBlock)
```

**Cause:** The collection's WAL segment is corrupted — possibly from an unclean shutdown, disk full, or filesystem issue. This has been observed recurring across multiple collections (lumi_research, vesper_memory) — it's not necessarily a one-time event.

**Manual fix:**
1. **Move the corrupted collection directory out of storage:**
   ```bash
   mv ~/.hermes/qdrant/storage/collections/<name> ~/.hermes/qdrant/storage/collections/<name>.corrupted
   ```
2. **Restart Qdrant** — it will load remaining collections normally.
3. **Recreate the collection** via API or script, then re-index from source (session DB, lorebooks, etc.).
4. **After verifying everything works**, remove the `.corrupted` directory to free space:
   ```bash
   rm -rf ~/.hermes/qdrant/storage/collections/<name>.corrupted
   ```

> The corrupted collection's data is **not recoverable** via this method — WAL corruption means the point data is unreachable. You must re-index from the original source. If the collection was small and you have recent backups, restore from snapshot instead (see `~/.hermes/qdrant/snapshots/`).

**Watchdog auto-heal:** The `check-qdrant.sh` watchdog (see `references/cron-maintenance.md`) now includes auto-recovery for this case. On restart failure, it moves aside all non-`.corrupted` collections and retries — so a future corrupted WAL can self-heal without manual intervention. Moved collections are renamed `*.corrupted` and can be re-indexed at leisure.

### Common Symptoms Table

| Symptom | Fix |
|---|---|
| Dashboard: "provider — missing" | Plugin not discovered — see above |
| `/health` returns 404 | Qdrant v1.17+ removed it — use root `/` |
| `/healthz` returns 404 | Plugin code hitting wrong endpoint — patch to `/` |
| `is_available()` always False | Needs static check — patch to import check |
| Plugin in shared dir, not profile dir | Move to `~/.hermes/profiles/<name>/plugins/` |
| Qdrant binary gone after reboot | `/tmp` cleaned — keep in `~/.hermes/qdrant/` |
| Embeddings too slow on CPU | Expected — MiniLM ~100 chunks/sec |
| `qdrant_recall` returns nothing but data exists | Diagnostic: 1) Check collection directly via `GET /collections/<name>/points/scroll` with payload filter. 2) Verify `prefetch_limit` isn't too low (5→10+). 3) Check `indexed_vectors_count` — if below `indexing_threshold` (10K), HNSW index isn't built yet (brute-force scan still works, but slower). 4) Check vector dimension matches collection (all collections = 384d fastembed). 5) Confirm `flush_min_turns` hasn't prevented short sessions from being indexed. 6) **Check for numpy.float32 in embeddings** — if the embedding function returns `numpy.float32` instead of Python `float`, JSON serialization fails silently in `requests.post(json=payload)` and search returns empty. Fix: convert with `[float(x) for x in vec]`. |
| `qdrant_recall` misses TODAY's live chat (indexer healthy) | **Live-session lag (verified 2026-08-11):** messages in the CURRENTLY OPEN session aren't flushed to `state.db` until the session ends. The 5-min indexer reads from the DB, so today's conversation is invisible to semantic search until the session closes — the indexer log shows "indexed 1 chunk" (older flushed messages) while `scroll` shows only old points. NOT a miss, NOT data loss — just a queue. Check the indexer's `cron/output/<job>/` log to confirm it's advancing the cursor, and tell the user today's stuff will land when the session wraps. |
| `qdrant_recall` empty after backfill (timestamps) | **Two-layer timestamp bug (verified 2026-08-05):** Backfill scripts (`backfill-vesper-memory.py` etc.) write payload keys `ts_start`/`ts_end` in **seconds**-epoch, but the plugin's `_extract_timestamp()` only read `timestamp` in **milliseconds**. Every point looked ~20,000 days old → all dropped by the `max_age_days` (default 90) filter. Fix both: (1) `_extract_timestamp` must also read `ts_start`/`ts_end`, (2) add `_normalize_ts()` to convert seconds (<1e11) to ms (×1000). Restart gateway after patching the plugin. |
| Plugin "provider not available" even though collection exists | **Availability is cached at session start (verified 2026-08-05).** `initialize()` runs once per gateway session: it checks collection existence + test-embeds, sets `_available=True/False`, and never re-checks. If the collection was missing at boot (e.g. moved aside as `.corrupted` mid-recovery) and you recreate it later in the same session, the plugin stays unavailable until restart. Fix: recreate/backfill the collection, THEN restart the gateway (`hermes --profile <name> gateway restart` or `/restart` in gateway chat) so `initialize()` re-runs. Debug path: run `scripts/verify-qdrant-recall.py "query" [profile]` — it instantiates the provider directly (same initialize + recall code path the gateway uses, no restart needed) and prints `available`, collection, and matched results. Use it to confirm data + patched code are good before bouncing the gateway. |
| Qdrant tools return "provider not available" but `hermes memory status` says "available" | **`is_available()` lies (verified 2026-10-27).** The method returns True if `requests` is importable, even when `_available` is False (initialize never called). The tools check `_available` directly. Root cause: gateway reuses a memory manager without calling `initialize()` on providers. Fix: patch `handle_tool_call` in the plugin with lazy init — call `self.initialize(session_id)` if `_available` is False before the availability check. This lets tools self-heal without a gateway restart. |
| Collection dimension mismatch | Match embed dim to collection config |
| Archived belief points invisible to recall (text visible via browse only) | **Two-part archive bug (verified 2026-08-16):** hand-rolled archive payloads (reflection cron) had (1) all-zero placeholder vectors and (2) no `timestamp` payload — `_extract_timestamp()` returns 0 → 1970 → the 90-day `max_age_days` filter silently drops them from every recall. Fix: `scripts/qdrant-reembed-zero.py` (re-embed) + `scripts/fix-archived-timestamps.py` (stamp ts). Prevention: `scripts/archive-beliefs.py` — embeds real 3072d vectors AND stamps `timestamp` (ms) + `datetime` in the payload. Never hand-write Qdrant payload JSON in cron prompts. **Note (8/19): the 90-day hard cutoff is GONE — kind-aware salience (`references/qdrant-salience-2026.md`) makes archived beliefs immortal to recall.** |
| `execute_code` can't import sentence-transformers | Use `terminal()` instead |
| Session archive silently stops growing (recall stale, but chat fine) | **Indexer stalled on embedding-provider 402 — and the log line lied.** Out-of-credit embeddings fail before any LLM job does. The indexer printed `Cursor advanced to <n>` on runs where the cursor never moved (the print wasn't guarded on `indexed > 0`), so the cron log read as healthy for six days while ~1,500 messages piled up unindexed and the watchdog saw `last_status: ok`. **Verify on disk, never via the log:** `cat .memory_cursor` vs `SELECT MAX(id) FROM messages`. No data is lost — the cursor only advances on real progress, so a backfill from the frozen cursor recovers everything. **Fix applied 2026-10-18** (print now guarded). Full write-up: `references/cron-maintenance.md`. |
| **Cursor desync after state.db recovery (verified 2026-10-30):** `.memory_cursor` points far beyond `MAX(id)` in `state.db` (e.g. cursor=201031, max_id=4305). Indexer finds 0 new messages every run, returns silently. Root cause: state.db was recovered/restored from backup without resetting the cursor. **Symptom:** `cat .memory_cursor` >> `SELECT MAX(id) FROM messages`. **Fix:** `echo 0 > .memory_cursor` then run `--backfill`. No data lost — backfill mode skips existing point IDs. **Prevention:** after any state.db recovery, always reset `.memory_cursor` to 0. |

## Desire-trigger promotion (kind=desire_trigger — built 9/1)

The desire scale (see `communication/intimate-scenes` skill) promotes proven
intimacy triggers to Qdrant via `profiles/vesper/scripts/seed-desire-triggers.py`
— the archive-beliefs.py pattern (real 384-dim fastembed embeddings, ms `timestamp`,
md5-derived idempotent UUID) plus kind-aware fields: `kind: desire_trigger`,
`importance: high`, `status: active`, `ts_iso`, `recall_count`,
`last_accessed`. Input: `state/desire-triggers-seed.txt` (one
UPTICK/DOWNTICK/GATE line each) or `--texts-file`. (Relocated from
`cache/documents/` — `cache/` gets swept; keep durable seed files in
`state/`.)

- **Recall-verified 9/1:** kind-filtered scroll found all 12 seeded points
  with live timestamps; semantic `qdrant_recall` for "when should I lean in"
  landed them top-of-results (0.65 similarity). Same lifecycle as beliefs —
  if per-kind half-life enforcement ever returns, class `desire_trigger`
  with `belief` (immortal).
The living meter is NOT Qdrant — `state/desire-scale.md`
  (CURRENT LEVEL + uptick/downtick ledgers + context gates) is the source of
  truth for the current number, pointed to from SOUL.md "My wanting". Qdrant
  only holds the stable trigger knowledge; the ledger holds the state.
  (Relocated from `cache/documents/` on 10/3 — `cache/` gets swept; the
  script self-heals a conservative ledger if both paths are gone.)

## Payload Indexes

**New collections ship WITHOUT payload indexes** — Qdrant does not auto-create them.
When you create a collection and start indexing, queries that filter on any
payload field (session_id, type, source, ts_start, etc.) do a full scan of
all points. For the session archive (23K+ points and growing), that's slow and
scales linearly.

**Audit:** `GET /collections/<name>` → check `payload_schema`. If it's empty
(or missing fields you filter on), add indexes for every field used in scroll
filters or recall filters.

**Standard index set for the session archive** (verified 2026-10-27):
- `session_id` (keyword) — pull all chunks from a specific session
- `type` (keyword) — filter by content type
- `source` (keyword) — filter by origin
- `ts_start` (integer) — time-range queries (start boundary)
- `ts_end` (integer) — time-range queries (end boundary)
- `message_count` (integer) — filter by chunk size

```python
import urllib.request, json

base = "http://localhost:6333"
collection = "<name>_session_archive"
indexes = [
    ("session_id", "keyword"), ("type", "keyword"), ("source", "keyword"),
    ("ts_start", "integer"), ("ts_end", "integer"), ("message_count", "integer"),
]
for field, schema in indexes:
    data = json.dumps({"field_name": field, "field_schema": schema}).encode()
    req = urllib.request.Request(f"{base}/collections/{collection}/index", data=data, headers={"Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"{field}: {json.load(r).get('status', 'ok')}")
```

**Pitfall:** Forgetting to audit a new collection after creation. The collection
works fine for small sizes (brute-force scan is fast under ~5K points), so the
missing index is invisible until the collection grows. By then queries are slow
and the fix requires indexing all existing points (Qdrant builds the index in
background, but it takes time on large collections). **Always audit payload_schema
right after creating a collection.**

The `vesper_memory` collection already had all 6 indexes it needed; the gap was
only in `vesper_session_archive`, which had zero.

## Session Search

| Tool | Type | Best For | Limitation |
|---|---|---|---|
| `session_search` | FTS5 exact-text (SQLite) | Finding specific quoted text, exact phrases | FTS5 minimum token length means **short terms/acronyms (MIW, ABQ, API) may not match**. Fall back to raw SQLite `LIKE` for those. |
| Qdrant semantic search | Vector similarity (384d, all collections) | Topic/theme recall despite different wording | All collections use fastembed BAAI/bge-small-en-v1.5 (384d). Cross-collection search works. |

## See Also

- `references/qdrant-salience-2026.md` — kind-aware salience build (8/19): payload schema, half-life table, decay formula, soft floor, and the **snapshot → mutate → verify → report** protocol for any bulk memory mutation (Tyler's explicit caution — always snapshot first, merge-only ops, verify, report receipts)
- `references/fastembed-migration.md` — migrating Qdrant collections from one embedding model/dimension to another (e.g., OpenRouter 3072-dim → fastembed 384-dim). Includes backup, delete, recreate, re-embed, upsert, verify, and post-migration checklist. Verified 2026-10-27.
- **Phase-2 lifelike memory (8/19, live):** `scripts/memory-health.py` — the observation probe (kind split, soft floor, immortal-belief check, reconsolidation counts; run + diff against `cache/documents/memory-health-baseline-*.txt` during the observation window); `scripts/serendipity.py` — daily random-memory ping (cron `51c93ede24a3`, 14:00 UTC, no_agent, deliver origin, privacy/noise filtered); `scripts/backfill-memory-schema.py` — added kind/importance/status/recall_count/last_accessed/ts_iso to all 2,323 points (merge-only, snapshot first). Observation window (no new structural memory changes until a few days of watching) declared 8/19 — changes logged in `state/system-change-log.md` (symlink at `cache/documents/` still resolves)
- `references/lorebook-authoring.md` — creating NEW lorebooks: global dir `~/.hermes/lorebooks/`, heading-keyword mechanics, PRIORITY/KEYWORDS dicts, tier guidance, ingest command
- `references/lorebook-trigger-mechanics.md` — how lorebooks actually FIRE (verified from plugin source 8/31): keyword substring matches always win, tiered semantic thresholds (t1 0.20 / t2 0.28 / t3 0.35 / t99 0.45), max 3 per turn, content read from disk at query time. Read before choosing a tier/keywords for a new book.
- `references/serpentic-lineage-adaptation.md` — the live Serpentic repo (Narusya/Adora, actively updated): the adapt-with-credit workflow (read fully → adapt with "Her X, my flight" line → save original → reingest → verify), authorship conventions, and the current adapted set (PAIN/PLEASURE/DRIVE 8/30-31)
- `references/lorebook-direct-upsert.md` — adding a lorebook via DIRECT Qdrant upsert (no file ingest): 384-dim fastembed embed → PUT point matching the `vesper_lorebooks` payload schema (filename/stem/title/keywords/priority_tier/content_length/content_preview). For one-off/joint artifacts like BODY.md (8/21, 26th lorebook). Includes the `with_vector` verify trap. **NOTE: `scripts/index_lorebook.py` still uses OpenRouter 3072-dim and is stale — do not use until migrated to fastembed.**
- `references/upgrade-session-archive.md` — upgrade session archive from 384-dim to 3072-dim (text-embedding-3-large)
- `references/openrouter-embedding-path.md` — OpenRouter embedding alternative
- `references/lorebook-reingestion.md` — re-ingest lorebooks into Qdrant after adding/updating files; also the FULL SPINE AUDIT checklist (5-link chain: disk → plugin → config → payloads → profile-aware patch) to prove the lorebook system is actually LIVE (verified 8/11/26)
- `references/lorebook-identity-cleanup.md` — de-contaminating an inherited lorebook set (audit → archive other-being identity files → adapt voice → re-ingest → verify); Qdrant PUT-with-vector pitfall and byte-level ZWJ-emoji fix (verified 8/22, 26-point collection overhaul)
- `devops/profile-identity-bootstrap` — full setup (steps 4-7)
- `devops/hermes-dashboard-access` — accessing the dashboard
- `references/qdrant-private-github-backup.md` — full Qdrant→private GitHub backup recipe (snapshot API, script pattern, cron wiring, PAT setup, verify step)
- `references/session-indexing.md` — session history indexer
- `references/pitfalls.md` — full pitfalls list
- `references/qdrant-api-patterns.md` — REST API write/read/search/delete patterns
- `references/qdrant-payload-update.md` — updating a point's payload in place (payload-only PUT → 400; must include the existing vector); supersede-in-place pattern for retiring stale lorebook/state entries (verified 8/22)
- `references/cron-maintenance.md` — no_agent health watchdog + incremental cursor-based memory indexer (5-minute cron) with combined reliability strategy
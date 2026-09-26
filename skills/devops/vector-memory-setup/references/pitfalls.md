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

### 2. Background Process Wrappers Cause Exit Code 127
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

### 5. Forgetting Payload Indexes
Without payload indexes, filtered searches are O(n). Always index fields you filter on:
```python
client.create_payload_index(collection_name="...", field_name="source", field_schema="keyword")
client.create_payload_index(collection_name="...", field_name="type", field_schema="keyword")
client.create_payload_index(collection_name="...", field_name="timestamp", field_schema="integer")
```

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

After the Hermes update (v0.16.0+), there are now TWO ways to search session history:

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

### 11. Qdrant REST API: Use `/points/query` Not `/points/search`

The Qdrant REST API v1.18.2 uses `/collections/{name}/points/query` for semantic search, **not** `/points/search`. The `/points/search` endpoint returns HTTP 400.

```python
# CORRECT: returns results
req = urllib.request.Request(
    f"{base}/collections/{collection}/points/query",
    data=payload, headers={"Content-Type": "application/json"}
)

# WRONG: HTTP 400 Bad Request
req = urllib.request.Request(
    f"{base}/collections/{collection}/points/search",
    data=payload, headers={"Content-Type": "application/json"}
)
```

The `qdrant-client` Python library uses `client.query_points()` (not `client.search()` which doesn't exist in current versions).

### 12. `execute_code` Is Fully Blocked (Not Just System Packages)

The `execute_code` tool is completely blocked for arbitrary Python — not just system packages. The error is:
```
BLOCKED: execute_code runs arbitrary local Python
```
This means ANY Python code that imports `sentence-transformers`, `qdrant-client`, `urllib`, `json`, etc. must run via `terminal()`. There is no workaround — use `terminal(command="python3 ...")` for all Python execution.

## Less Critical But Useful

- Seed immediately after creating collections — empty collections are useless
- Create a cron job for auto-restart — Qdrant won't survive reboots without it
- Test search after seeding — verify embeddings are actually retrievable
- Keep a README documenting your specific setup in `~/.hermes/qdrant/README.md`
- After indexing sessions, expect ~3-5x the original lorebook chunk count — plan disk accordingly

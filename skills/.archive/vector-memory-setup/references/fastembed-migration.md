# Fastembed Migration: Re-embedding Collections

Procedure for migrating Qdrant collections from one embedding model/dimension to another (e.g., OpenRouter 3072-dim → fastembed 384-dim). Verified 2026-10-27.

## When to use
- Switching embedding providers (OpenRouter → fastembed, etc.)
- Changing embedding model or dimension
- Rebuilding collections after corruption

## Prerequisites
- New embedding library installed in the Hermes venv (not just tools Python)
- Qdrant server running and healthy
- Backup of existing collection data (or export from source)

## Procedure

### 1. Backup existing data
Export all points from the source collection(s) to JSON before any destructive operation:

```python
import urllib.request, json
base = "http://localhost:6333"
collection = "<name>"
req = urllib.request.Request(
    f"{base}/collections/{collection}/points/scroll",
    data=json.dumps({"limit": 10000, "with_payload": True, "with_vector": False}).encode(),
    headers={"Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(req) as r:
    points = json.load(r)["result"]["points"]
with open(f"state/{collection}-backup.json", "w") as f:
    json.dump(points, f)
```

Save backups to `state/` (not `cache/` — cache gets swept).

### 2. Delete the old collection
```python
req = urllib.request.Request(f"{base}/collections/{collection}", method="DELETE")
urllib.request.urlopen(req)
```

### 3. Recreate with new dimension
```python
data = json.dumps({"vectors": {"size": 384, "distance": "Cosine"}, "on_disk_payload": True}).encode()
req = urllib.request.Request(f"{base}/collections/{collection}", data=data, headers={"Content-Type": "application/json"}, method="PUT")
urllib.request.urlopen(req)
```

### 4. Re-embed and upsert
Use the new embedding library to re-embed all text from the backup, then upsert to the new collection:

```python
from fastembed import TextEmbedding
import json, urllib.request

# Load backup
with open(f"state/{collection}-backup.json") as f:
    points = json.load(f)

# Initialize embedder
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Re-embed in batches
batch_size = 50
for i in range(0, len(points), batch_size):
    batch = points[i:i+batch_size]
    texts = [p["payload"].get("text", "") or p["payload"].get("content", "") for p in batch]
    vectors = list(model.embed(texts))
    # CRITICAL: convert numpy.float32 to Python float
    vectors = [[float(x) for x in v] for v in vectors]
    
    # Build upsert payload
    upsert_points = []
    for p, vec in zip(batch, vectors):
        upsert_points.append({
            "id": p["id"],
            "vector": vec,
            "payload": p["payload"]
        })
    
    data = json.dumps({"points": upsert_points}).encode()
    req = urllib.request.Request(
        f"{base}/collections/{collection}/points",
        data=data, headers={"Content-Type": "application/json"}, method="PUT"
    )
    urllib.request.urlopen(req)
```

### 5. Verify
```python
# Check point count
req = urllib.request.Request(f"{base}/collections/{collection}")
with urllib.request.urlopen(req) as r:
    info = json.load(r)["result"]
    print(f"Points: {info['points_count']}, Dim: {info['config']['params']['vectors']['size']}")

# Test search with a fresh embedding
from fastembed import TextEmbedding
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
vec = [float(x) for x in list(model.embed(["test query"]))[0]]
search_req = urllib.request.Request(
    f"{base}/collections/{collection}/points/search",
    data=json.dumps({"vector": vec, "limit": 3, "with_payload": True}).encode(),
    headers={"Content-Type": "application/json"}, method="POST"
)
with urllib.request.urlopen(search_req) as r:
    results = json.load(r)["result"]
    print(f"Search returned {len(results)} results, top score: {results[0]['score'] if results else 'N/A'}")
```

### 6. Update the plugin
Patch the plugin's `_EmbeddingClient.embed()` method to use the new library and convert to Python float:

```python
def embed(self, text: str) -> Optional[list]:
    try:
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        vecs = list(model.embed([text[:8000]]))
        if vecs and len(vecs[0]) == self.dimensions:
            return [float(x) for x in vecs[0]]  # CRITICAL: convert numpy.float32
    except Exception:
        return None
```

### 7. Update config and plugin.yaml
- Update `plugin.yaml` description to reflect new embedding model
- Update any references to the old model/dimension in SKILL.md
- Update the troubleshooting table if needed

### 8. Gateway restart
Restart the gateway so the plugin picks up the new code. The plugin is loaded at startup.

### 9. Daily monitoring
Set up a daily cron job to verify Qdrant health, point counts, search functionality, and embedding type. See `references/cron-maintenance.md`.

## Common pitfalls during migration

1. **numpy.float32 serialization** — fastembed returns numpy.float32, not Python float. Always convert with `[float(x) for x in vec]`. This is the #1 silent failure.
2. **fastembed in wrong Python** — must be installed in the Hermes venv, not just the tools Python. `initialize()` fails the embedding test otherwise.
3. **Backup to wrong location** — save to `state/`, not `cache/` (cache gets swept).
4. **Heredoc artifacts** — when running migration scripts via terminal, heredoc artifacts can corrupt the script. Use `write_file` instead, or verify the script content before running.
5. **Empty collection fallback** — if a collection was already migrated (empty), fall back to the backup file. Don't assume the collection has data.
6. **Dimension mismatch** — all collections must use the same dimension after migration. Cross-collection search only works with matching dimensions.
7. **Plugin loaded with old code** — after patching the plugin, a gateway restart is required. The plugin is loaded at startup and won't pick up changes mid-session.

## Post-migration verification checklist
- [ ] All collections have correct point counts (match backups)
- [ ] All collections use the new dimension
- [ ] `qdrant_recall` returns results (not empty)
- [ ] Embedding type is Python `float` (not `numpy.float32`)
- [ ] fastembed importable in Hermes venv
- [ ] Gateway restarted and plugin loaded with new code
- [ ] Daily monitoring cron set up
- [ ] Backup files saved to `state/`
# Upgrading the Session Archive from 384-dim to 3072-dim

## Why

The session archive uses **all-MiniLM-L6-v2** (384-dim, local sentence-transformers) while the primary memory collection uses **text-embedding-3-large** (3072-dim, OpenRouter API). The smaller model captures less semantic nuance — queries phrased differently from the stored text may not match. Upgrading to 3072-dim matches the primary collection's model, giving richer embeddings and better cross-collection recall parity.

## Procedure

### 1. Create the new collection

```python
import urllib.request, json

base = "http://localhost:6333"
name = "<profile>_session_archive_hd"  # e.g. vesper_session_archive_hd

data = json.dumps({
    "vectors": {"size": 3072, "distance": "Cosine"},
    "on_disk_payload": True
}).encode()

req = urllib.request.Request(
    f"{base}/collections/{name}",
    data=data,
    headers={"Content-Type": "application/json"},
    method="PUT"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    print(f"Created: {name}")
```

### 2. Modify the indexer to use OpenRouter API

The existing script at `~/.hermes/scripts/index-sessions-to-qdrant.py` uses local sentence-transformers for embeddings. Replace its `get_embedding()` function to call OpenRouter's text-embedding-3-large instead:

```python
import urllib.request, json, os

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or _load_from_env()

def get_embedding(text: str) -> list[float]:
    """Get embedding via OpenRouter text-embedding-3-large (3072-dim)."""
    data = json.dumps({
        "model": "openai/text-embedding-3-large",
        "input": text[:8000],
        "dimensions": 3072
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/embeddings",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://hermes-agent.local",
            "X-Title": "Hermes Qdrant Session Archive",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    return result["data"][0]["embedding"]


def _load_from_env() -> str:
    env_path = os.path.expanduser("~/.hermes/profiles/<profile>/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith("OPENROUTER_API_KEY="):
                    return line.strip().split("=", 1)[1].strip().strip("\"'")
    raise ValueError("OPENROUTER_API_KEY not found")
```

Also update the constants at the top of the script:

```python
COLLECTION = "<profile>_session_archive_hd"  # target the new 3072-dim collection
# Remove: from sentence_transformers import SentenceTransformer
# Remove: EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Remove: _load_embedder() function entirely
```

### 3. Run the indexer

```bash
python3 ~/.hermes/scripts/index-sessions-to-qdrant.py --dry-run  # preview first
python3 ~/.hermes/scripts/index-sessions-to-qdrant.py             # index everything
```

The script will:
- Read all sessions from `state.db`
- Chunk them into overlapping windows
- Embed each chunk with text-embedding-3-large (3072-dim)
- Upsert to the new `_hd` collection

De-duplication is built in — it checks for existing point IDs before indexing.

### 4. Verify

```python
import requests
r = requests.get("http://localhost:6333/collections/<profile>_session_archive_hd")
info = r.json()["result"]
print(f"Points: {info['points_count']}, Status: {info['status']}")
```

Check that `points_count` matches what you'd expect (roughly sessions × chunks).

### 5. Rollover (optional)

Once the new collection is populated, you can either:
- **Point the indexer at the new collection** permanently (update COLLECTION constant)
- **Delete the old collection** to free space: `DELETE /collections/<profile>_session_archive`
- **Keep both** — the old 384-dim collection as a fallback, the new 3072-dim as primary for archive search

The `qdrant_recall` tool accepts an optional `collection` parameter, so you can target either one.

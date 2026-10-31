# Qdrant REST API Patterns (v1.18.2)

Quick-reference for direct Qdrant API interactions. All examples use
`urllib` (stdlib, no extra deps).

## Health Check

**Qdrant v1.17+ removed `/health` and `/healthz`.** Always use root `/`:

```python
import urllib.request, json
with urllib.request.urlopen("http://localhost:6333/", timeout=5) as r:
    assert r.status == 200  # {"title":"qdrant - ...","version":"1.18.2",...}
```

## Point IDs

**Must be UUIDs or unsigned integers.** Arbitrary strings ("test-001") are
rejected with HTTP 400. Use `uuid.uuid4()`:

```python
import uuid
point_id = str(uuid.uuid4())
```

## Write

```python
url = "http://localhost:6333/collections/<name>/points?wait=true"
data = json.dumps({
    "points": [{
        "id": str(uuid.uuid4()),
        "vector": [0.1] * 3072,
        "payload": {"text": "...", "timestamp": int(time.time() * 1000), "role": "user"}
    }]
})
req = urllib.request.Request(url, data=data.encode(),
    headers={"Content-Type": "application/json"}, method="PUT")
with urllib.request.urlopen(req, timeout=10) as r:
    result = json.loads(r.read())
    assert result["status"] == "ok"
```

## Scroll (Read Points)

```python
data = json.dumps({"limit": 10, "with_payload": True})
req = urllib.request.Request(
    f"http://localhost:6333/collections/<name>/points/scroll",
    data=data.encode(), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as r:
    data = json.loads(r.read())
    for pt in data["result"]["points"]:
        print(pt["payload"]["text"])
```

## Search (Semantic)

```python
data = json.dumps({
    "vector": query_vector, "limit": 5, "with_payload": True
})
req = urllib.request.Request(
    f"http://localhost:6333/collections/<name>/points/search",
    data=data.encode(), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as r:
    for hit in json.loads(r.read())["result"]:
        print(f"Score {hit['score']:.4f}: {hit['payload']['text'][:100]}")
```

> **Deprecation note:** Older docs reference `/collections/<name>/points/search`
> which works in v1.18.2. The newer path is `/collections/<name>/points/query`
> (POST) — use search for now unless you know the target version uses query.

## Delete by Filter

```python
data = json.dumps({
    "filter": {"must": [{"key": "session_id", "match": {"value": "test-verification"}}]}
})
req = urllib.request.Request(
    f"http://localhost:6333/collections/<name>/points/delete",
    data=data.encode(), headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=10) as r:
    result = json.loads(r.read())
    # status may be "acknowledged" (async) — add ?wait=true for sync
```

Delete without `?wait=true` is async. Add `?wait=true` to the URL to block
until completion.

## Collection Info

```python
with urllib.request.urlopen(f"http://localhost:6333/collections/<name>", timeout=10) as r:
    info = json.loads(r.read())["result"]
    print(f"Points: {info['points_count']}, Dim: {info['config']['params']['vectors']['size']}")
```

## Verify Discovery (Hermes Plugin)

```python
import sys
sys.path.insert(0, "/home/lumi/.hermes/hermes-agent")
from plugins.memory import discover_memory_providers, find_provider_dir, load_memory_provider

print("find:", find_provider_dir("qdrant"))
for n, d, a in discover_memory_providers():
    print(f"{'✅' if a else '❌'} {n}")
```
# Updating a Point's Payload (verified 2026-08-22)

**Pitfall: a payload-only update returns HTTP 400.** `PUT /points` with
`{"points": [{"id": ..., "payload": {...}}]}` (no vector) → **400 Bad Request**.
Qdrant requires the FULL point for an upsert-by-id: `id` + `vector` + `payload`.

The working shape — read the existing vector first, then PUT the full point:

```python
import json, urllib.request

# 1. Scroll WITH vector to capture the existing vector for the point
req = urllib.request.Request(
    "http://localhost:6333/collections/<name>/points/scroll",
    data=json.dumps({"limit": 100, "with_payload": True, "with_vector": True}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
pts = json.load(urllib.request.urlopen(req, timeout=15))["result"]["points"]

target = None; vec = None
for p in pts:
    if p["payload"].get("filename") == "X.md":   # identify your point
        target = p["id"]; vec = p.get("vector"); break

# 2. Mutate payload, keep vector
payload = {**p["payload"], "status": "superseded", "superseded_by": "..."}

# 3. PUT full point (id + vector + payload) — NOT payload-only, NOT POST
req2 = urllib.request.Request(
    "http://localhost:6333/collections/<name>/points",
    data=json.dumps({"points": [{"id": target, "vector": vec, "payload": payload}]}).encode(),
    headers={"Content-Type": "application/json"}, method="PUT")
print(json.load(urllib.request.urlopen(req2, timeout=15))["status"])  # "ok"
```

- Use **PUT** (upsert), not POST, for modifying existing points.
- **Always include the vector** — payload-only edits 400.
- Batch point updates use the same rule: PUT with `points: [{id, vector, payload}, ...]`.

## Supersede-in-place pattern (instead of delete)

For lorebooks/entries that are stale but should be KEPT for history (move-don't-delete),
mark them rather than removing:

```python
payload["status"] = "superseded"
payload["superseded_by"] = "<replacement or note>"
payload["superseded_date"] = "2026-08-22"
```

Kept points with `status: superseded` stay in the collection (history preserved)
but can be excluded from recall via a payload filter. Used 8/22 to retire a stale
Lu-era STATUS lorebook fragment that was surfacing as Vesper's own state.

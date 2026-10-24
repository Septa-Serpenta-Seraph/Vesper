# Session History Indexing — Reference

## Source Data

Hermes stores all conversation sessions in SQLite at `~/.hermes/state.db`. Use the `hermes sessions` CLI to export — don't query SQLite directly unless the CLI is unavailable.

## Indexing via `hermes sessions export` (Recommended)

The cleanest approach uses the Hermes CLI to export sessions:
```bash
# List all sessions (not just default 20)
hermes sessions list --limit 200
```
**Important:** `hermes sessions list` defaults to showing only 20 recent sessions. Always use `--limit 200` (or higher) to get the full list. The last column of each line is the session ID.

```bash
# Export a specific session
hermes sessions export --session-id <session_id> /tmp/session_<id>.jsonl
```

Each exported JSONL file contains one JSON object with session metadata and a `messages` array. Each message has: `role`, `content`, `timestamp`, plus tool call info.

### Full Indexing Script

`~/.hermes/qdrant/index-all-sessions.py`:

```python
import json, uuid, subprocess, urllib.request, sys, os, time
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Get all session IDs
result = subprocess.run(['hermes', 'sessions', 'list', '--limit', '200'],
                       capture_output=True, text=True, timeout=30)
lines = result.stdout.strip().split('\n')[1:]  # skip header
session_ids = [line.split()[-1] for line in lines if line.strip()]

base = "http://localhost:6333"
collection = "lumi_session_archive"
total_indexed = 0

for sid in session_ids:
    export_file = f'/tmp/sess_{sid[:20]}.jsonl'
    try:
        subprocess.run(['hermes', 'sessions', 'export', '--session-id', sid, export_file],
                      capture_output=True, text=True, timeout=30)
        
        with open(export_file) as f:
            for line in f:
                entry = json.loads(line.strip())
                messages = entry.get('messages', [])
                if messages:
                    break
        
        # Chunk messages (~400 chars each)
        chunks = []
        current = ""
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if not content or len(content.strip()) < 5 or role in ('tool', 'system'):
                continue
            text = f"[{role}]: {content}"
            if len(current) + len(text) > 400:
                if current.strip():
                    chunks.append(current.strip())
                current = text
            else:
                current += "\n" + text if current else text
        if current.strip():
            chunks.append(current.strip())
        
        if not chunks:
            continue
        
        embeddings = model.encode(chunks).tolist()
        points = [{
            "id": str(uuid.uuid4()),
            "vector": emb,
            "payload": {
                "text": chunk[:2000],
                "session_id": sid,
                "session_title": entry.get('title', 'Untitled'),
                "source": f"session:{entry.get('source', 'unknown')}",
                "type": "session",
                "timestamp": time.time()
            }
        } for chunk, emb in zip(chunks, embeddings)]
        
        for i in range(0, len(points), 50):
            batch = points[i:i+50]
            data = json.dumps({"points": batch}).encode()
            req = urllib.request.Request(f"{base}/collections/{collection}/points",
                                        data=data, headers={"Content-Type": "application/json"},
                                        method="PUT")
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_indexed += len(batch)
    finally:
        if os.path.exists(export_file):
            os.remove(export_file)

print(f"Indexed {total_indexed} chunks")
```

## Actual Indexing Results (June 2026)

- **90 sessions** listed via `hermes sessions list --limit 200`
- **86 sessions** successfully indexed (4 errors from weird session IDs)
- **1,998 chunks** indexed from sessions
- **2,860 total points** in `lumi_session_archive` (including 862 pre-existing lorebook chunks)
- **1 error** (session with unusual ID format)
- Indexing time: ~5-10 minutes for all 90 sessions
- Model: `all-MiniLM-L6-v2` (384d), loaded once at script start

## Alternative: Direct SQLite Reading

If `hermes sessions export` is unavailable, query `~/.hermes/state.db`:

```python
import sqlite3, json

conn = sqlite3.connect('/home/lumi/.hermes/state.db')
c = conn.cursor()
c.execute("SELECT id, title, source, message_count FROM sessions ORDER BY started_at DESC")
sessions = c.fetchall()
```

# Qdrant Configuration Reference

## Qdrant config.yaml

```yaml
qdrant:
  log_level: INFO
storage:
  storage_path: /home/lumi/.hermes/qdrant/storage
  snapshots_path: /home/lumi/.hermes/qdrant/snapshots
  on_disk_payload: true
service:
  http_port: 6333
  grpc_port: 6334
  host: 0.0.0.0
cluster:
  enabled: false
```

## Collection Schemas

| Collection | Dimensions | Distance | Purpose |
|---|---|---|---|
| intelligent_gould_lumi | 3072 | Cosine | Primary semantic memory |
| lumi_session_archive | 384 | Cosine | Session summaries |
| lumi_entities | 3072 | Cosine | Extracted entities |
| lumi_research | 3072 | Cosine | Research notes |

## Hermes config.yaml Snippet

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 4400
  user_char_limit: 2750
  provider: qdrant
  nudge_interval: 10
  flush_min_turns: 6

plugins:
  qdrant-memory:
    qdrant_url: http://localhost:6333
    collection: intelligent_gould_lumi
    prefetch_limit: 5
    recency_weight: 0.3
  enabled:
    - qdrant
```

## Disk Expansion (Hyper-V LVM)

When the host VHD is expanded, run inside the VM:

```bash
sudo parted /dev/sda resizepart 3 100%
sudo pvresize /dev/sda3
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```

## Verification

```bash
curl -s http://localhost:6333/health
curl -s http://localhost:6333/collections
```

## Common Pitfalls (June 2026 Session)

### execute_code Sandbox Limitation
The `execute_code` tool runs sandboxed Python without system packages. `sentence-transformers`, `qdrant-client`, `numpy`, `torch` etc. are NOT available inside `execute_code`. Always run embedding/seeding scripts via `terminal()`:
```python
# ❌ Fails: ModuleNotFoundError inside execute_code
execute_code(code="from sentence_transformers import SentenceTransformer; ...")
# ✅ Works: runs in real system Python
terminal(command="python3 ~/.hermes/qdrant/seed-memory.py")
```

### Background Process Exit Code 127
Using shell-level background wrappers (`nohup`, `disown`, `&` inside a string) inside `terminal()` causes exit code 127 ("command not found"). Hermes rejects these wrappers in foreground mode. Instead:
```python
# ❌ Causes exit 127
terminal(command="nohup /path/to/qdrant ... &")
# ✅ Correct
terminal(background=True, command="/path/to/qdrant --config-path /path/to/config.yaml > /path/to/log 2>&1")
```

### Installation Order Matters
When disk space is tight, install in this order and verify space after each:
1. Qdrant binary (82MB)
2. qdrant-client (~10MB) via pip
3. sentence-transformers (~2-4GB) via pip — this is the big one
4. If pip fails with "No space left", clean cache: `rm -rf ~/.cache/pip` and retry

### rolling_context (Narusya's Cross-Session Skill)
Located at `~/.hermes/narusya-backup/skills/rolling_context/`. Stores compression summaries in Qdrant and injects them on session start. Complementary to this setup — consider adopting for long-running projects.

## See Also

- `references/pitfalls.md` — detailed pitfalls and gotchas from live deployment (June 2026)
- `references/search-patterns.md` — search query patterns and filtering examples

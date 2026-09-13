# Windows SSH Reverse Tunnel: Full Diagnostic Session

Recorded 2026-07-25. Desktop (LM Studio) → SSH tunnel → VM (Hermes).

## Initial Setup

```
VM IP (Tailscale): <VM_TAILSCALE_IP>
Desktop IP (Tailscale): <DESKTOP_TAILSCALE_IP>
Desktop (LAN): <DESKTOP_LAN_IP>:1234
LM Studio port: 1234
Tunnel port on VM: 1235
```

## Symptom Progression

### Step 1: Curl exits 52 (empty reply) on direct Tailscale connection

```bash
curl -s http://<DESKTOP_TAILSCALE_IP>:1234/v1/models
# → empty, exit 52
```

**Root cause:** Windows Tailscale "Allow incoming connections" not enabled (firewall/faulty client settings).

### Step 2: SSH tunnel establishes but curl exits 52

```powershell
# Tunnel command
ssh -N -R 1235:localhost:1234 lumi@<VM_TAILSCALE_IP>

# Test
curl -s http://127.0.0.1:1235/v1/models
# → empty, exit 52
```

Tunnel is alive (`ss -tlnp | grep 1235` shows LISTEN). But empty response.

### Step 3: Verbose SSH reveals the problem

```powershell
ssh -v -N -R 1235:localhost:1234 lumi@<VM_TAILSCALE_IP>
```

Key diagnostic lines:
```
debug1: remote forward success for: listen 1235, connect localhost:1234
debug1: client_request_forwarded_tcpip: listen localhost port 1235, originator 127.0.0.1 port 35494
debug1: connect_next: start for host localhost ([::1]:1234)        ← IPv6!
debug1: channel 0: connected to localhost port 1234
```

**Root cause:** Windows SSH resolves `localhost` to `::1` (IPv6). LM Studio binds only `127.0.0.1` (IPv4). Tunnel connects but gets empty socket.

### Step 4: Fix with explicit IPv4

```powershell
ssh -N -R 1235:127.0.0.1:1234 lumi@<VM_TAILSCALE_IP>
```

Result: `curl http://127.0.0.1:1235/v1/models` returns model list successfully.

## Verified Working Models

```json
{
  "data": [
    {"id": "hermes-3-llama-3.1-8b"},
    {"id": "gguf-gpt-oss-20b-derestricted"},
    {"id": "qwen/qwen3.5-9b"},
    {"id": "text-embedding-nomic-embed-text-v1.5"}
  ]
}
```

## Summary of Diagnostics

1. **curl exit 28 (timeout):** Network unreachable, machine off, firewall block
2. **curl exit 52 (empty reply) with TCP connect success:** Connected but wrong protocol/address — check IPv4 vs IPv6, check LM Studio bind to `0.0.0.0`
3. **curl exit 52 with verbose SSH showing `[::1]`:** Windows SSH using IPv6 for `localhost` — use `127.0.0.1` explicitly
4. **Desktop browser succeeds but VM fails:** Windows firewall, Tailscale settings, or SSH tunnel issue

## Key Lesson

**Never use `localhost` in Windows SSH forward targets.** Always use `127.0.0.1` to force IPv4.
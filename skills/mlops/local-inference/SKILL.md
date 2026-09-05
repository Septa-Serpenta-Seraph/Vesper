---
name: local-inference
description: "Custom providers for local inference (LM Studio, Ollama, vLLM). Per-model context_length overrides, SSH tunnel setup, network topology options (LAN/Tailscale/tunnel), and verification. Use on /model switch to a local provider."
version: 1.0.0
platforms: [linux, windows]
metadata:
  hermes:
    tags: [hermes, config, provider, local, inference, lm-studio, tailscale, ssh-tunnel]
---

# Local Inference Setup — Hermes Custom Providers

Configure Hermes to use a local or self-hosted model provider, bypassing cloud API costs and enabling offline/zero-latency inference.

## When to Use

- User wants to switch from a cloud provider (OpenRouter, Anthropic) to a local model
- User has LM Studio, Ollama, vLLM, or another OpenAI-compatible endpoint running locally or on their LAN
- User wants `/model` command support for toggling between providers
- VM/agent is on a different network than the inference server (requires tunnel)

## Correct Config Format

In `config.yaml` (or profile config), use **`custom_providers`** — not `providers` (wrong shape, causes `AttributeError`):

```yaml
custom_providers:
  # ⚠ MUST be a list of dicts, each with a "name" key
  - name: desktop
    base_url: http://127.0.0.1:1235/v1
    api_key: ""
    discover_models: true
    # Per-model overrides — dict format REQUIRED for context_length to work
    models:
      hermes-3-llama-3.1-8b:
        context_length: 64000
```

Key details:
- `custom_providers` is the correct key (Hermes v0.18+). Bare `providers` at top level stores as string, triggering `AttributeError`.
- `discover_models: true` tells Hermes to call `/v1/models` and list returned model IDs in the `/model` picker.
- `api_key` can be empty string for local endpoints.
- Each entry is a **list element** with a `name` field — NOT a top-level key (no `desktop: {base_url: ...}` — that's wrong).

## Network Topology

### Same LAN
LM Studio on local machine, VM on same network:
```yaml
  base_url: http://192.168.0.xxx:1234/v1
```
Requires: `0.0.0.0` binding in LM Studio, firewall open.

### Tailscale
Both machines on same Tailnet:
```yaml
  base_url: http://100.x.x.x:1234/v1
```
Requires: Windows "Allow incoming connections" enabled.

### SSH Reverse Tunnel
Desktop runs LM Studio, VM connects through tunnel:
```powershell
ssh -N -R 1234:localhost:1234 user@vm-ip
```
```yaml
  base_url: http://127.0.0.1:1234/v1
```

## SSH Reverse Tunnel (Windows → Linux VM)

Common pattern: Windows desktop runs LM Studio, Linux VM runs Hermes, tunnel bridges them.

### Correct command

```powershell
ssh -N -R <vm-port>:127.0.0.1:<desktop-port> user@vm-ip
# Example: forward VM:1235 → desktop:1234
ssh -N -R 1235:127.0.0.1:1234 lumi@<VM_TAILSCALE_IP>
```

**Keep the tunnel alive:** Long-running tunnels drop without keepalive flags:
```powershell
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1235:127.0.0.1:1234 lumi@<VM_TAILSCALE_IP>
```
- `ServerAliveInterval=30` — send a keepalive every 30 seconds
- `ServerAliveCountMax=3` — disconnect after 3 missed keepalives

**⚠️ ALWAYS use `127.0.0.1` NOT `localhost` for the target!**  
Windows SSH resolves `localhost` to `::1` (IPv6) by default. LM Studio binds only `127.0.0.1` (IPv4), so the tunnel connects to an empty socket and returns `curl: (52) Empty reply from server`. Force IPv4 explicitly with `127.0.0.1`.

### Verbose debugging

```powershell
ssh -v -N -R 1235:127.0.0.1:1234 user@vm-ip
```

Key diagnostic lines from the output:

| Verbose Output | Meaning |
|----------------|---------|
| `remote forward success for: listen 1235, connect localhost:1234` | Forward accepted by VM SSHd |
| `connect_next: connect host localhost ([::1]:1234)` | **PROBLEM** — connecting to IPv6 on desktop side |
| `connect_next: connect host localhost (127.0.0.1:1234)` | ✅ Correct — IPv4 connection |
| `channel 0: connected to localhost port 1234` | Desktop-side connection established |

### Port conflicts on VM

Before setting up tunnel, check if the VM-side port is already claimed:

```bash
ss -tlnp | grep -w <port>
```

If occupied, use a different VM-side port (e.g. `1235` instead of `1234`).

### Curl exit code diagnostics

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Response received |
| 28 | Timeout | Network unreachable; check path, firewall, tunnel status |
| 52 | Empty reply | Connected but server sent nothing; check IPv4/IPv6, LM Studio binding |
| 7 | Connection refused | Port not listening; is LM Studio running? |

## Windows OpenSSH Server (remote desktop access through tunnel)

When the Windows firewall blocks all inbound connections, install OpenSSH Server on the desktop and forward SSH through the existing LM Studio tunnel. This lets the Hermes VM run commands on Windows directly.

### Install

```powershell
# One command — downloads from Windows Update
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start and enable auto-start
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

### SSH Key Authentication (avoids sharing passwords)

**On the VM (Hermes side),** generate a dedicated key pair:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/windows_desktop -N "" -C "vesper@hermes-windows"
cat ~/.ssh/windows_desktop.pub
```

**On Windows,** paste the public key into `authorized_keys`:
```powershell
mkdir $env:USERPROFILE\.ssh -Force
"<paste_the_public_key_here>" | Out-File -Append $env:USERPROFILE\.ssh\authorized_keys -Encoding UTF8
```

### Forwarding SSH through the LM Studio tunnel

Add a second `-R` flag to the existing tunnel command:

```powershell
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N ^
  -R 1235:127.0.0.1:1234 ^
  -R 1236:127.0.0.1:22 ^
  lumi@<vm-ip>
```

This forwards:
- `VM:1235 → desktop:1234` (LM Studio)  
- `VM:1236 → desktop:22` (SSH)

### Connecting from the VM

```bash
# Interactive shell
ssh -p 1236 tyler@127.0.0.1

# One-off remote command
ssh -p 1236 tyler@127.0.0.1 powershell "Get-Service mpssvc | Format-List Name,Status,StartType"
```

No firewall config needed — the tunnel bypasses it entirely.

## LM Studio Chat Template Patching

Some GGUF models ship with strict Jinja chat templates that block tool calls by rejecting tool call IDs that don't match a rigid format (e.g., `tool_call.id|length != 9`). When Hermes uses longer tool call IDs than the template expects, the model raises a Jinja exception and generation fails.

### Symptom

```
Unable to generate parser for this template.
Automatic parser generation failed:
...
Error: Jinja Exception: Tool call IDs should be alphanumeric strings with length 9!
```

### Fixes

**Option A — Replace the template entirely:** In LM Studio, open the model's Settings → Edit template and replace with a simple ChatML-compatible template that preserves `bos_token`/`eos_token` and skips tool-specific logic. See `references/lm-studio-template-patching.md` for the exact replacement template.

**Option B — Remove only the ID-length check:** Find the line checking `tool_call.id|length != 9` and remove that condition. This preserves the original template's tool-handling logic while accepting Hermes' longer IDs.

After patching, click **Save & Reload** in LM Studio.

## Per-Model context_length Override

LM Studio often reports the wrong context window for GGUF models. When Hermes rejects a model with:

```
ValueError: Model <X> has a context window of 8,192 tokens,
which is below the minimum 64,000 required by Hermes Agent.
```

**Set per-model `context_length` in the `models` dict:**

```yaml
custom_providers:
  - name: desktop
    base_url: http://127.0.0.1:1235/v1
    api_key: ""
    discover_models: true
    # ⚠ MUST be a dict-of-dicts, NOT a list!
    # A flat list like ['hermes-3-llama-3.1-8b'] causes Hermes
    # to silently skip context_length lookup.
    models:
      hermes-3-llama-3.1-8b:
        context_length: 64000
      gguf-gpt-oss-20b-derestricted:
        context_length: 64000
      qwen/qwen3.5-9b:
        context_length: 64000
```

**⚠ CRITICAL:** The `get_custom_provider_context_length()` function checks `isinstance(models, dict)`. A **flat list** (`models: [hermes-3-llama-3.1-8b]`) is silently skipped — no error, no warning, and no context_length override applied. The model format MUST be a **dict-of-dicts**.

### Top-level model.context_length — ignored on model switch

Setting `model.context_length` at the global level works only when the **default model** matches the **active runtime model**. If you use `/model` to switch to a different provider, this override is discarded:

```yaml
# ❌ Ignored when active model ≠ tencent/hy3:free
model:
  default: tencent/hy3:free
  context_length: 64000
```

The active model check at agent_init.py:2200 compares `_configured_default_runtime_model` vs `_active_runtime_model`. If they differ, `_config_context_length` is set to `None` and falls through to the custom_providers lookup. **Always use the per-model override under `models:` in the custom provider** for reliable results.

| Symptom | Cause | Fix |
|---------|-------|------|
| `AttributeError: 'str' object...` | `providers` stored as YAML string | Use `custom_providers:` dict instead |
| curl connects, empty reply (52) | IPv4/IPv6 mismatch on SSH tunnel | Use `127.0.0.1` not `localhost` in SSH command |
| curl connects, empty reply (52) | LM Studio not on `0.0.0.0` | Check binding in LM Studio |
| Timeout (exit 28) | Network unreachable | Ping, firewall, verify path |
| `Model not found in listing` | Wrong model name or gateway stale | `curl <url>/v1/models` for exact ID, then `hermes gateway restart` |
| Tailscale ping fails but active | Incoming blocked | Preferences → "Allow incoming connections" |
| Provider missing from `/model` | Gateway hasn't reloaded | `hermes gateway restart` from external terminal |
| `hermes config set providers '[...]'` | Stores as JSON *string* in YAML | Use `custom_providers:` key with dict value, not array notation |
| context_length override not applied | `models:` is a flat list, not dict | Change to `models: {model_name: {context_length: N}}` format |
| `sc start mpssvc` → "instance already running" | Service stuck in STOP_PENDING | Can't kill without BSOD; use regedit+reboot to disable, then clean, then re-enable |

## Verification

```bash
# Check which models LM Studio reports
curl -v --connect-timeout 5 http://<host>:<port>/v1/models

# Test a chat completion (note: PowerShell WILL mangle quotes — use single-line curl syntax)
curl -s http://<host>:<port>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

# Confirm provider is registered in Hermes
hermes model
```

## Config Gotchas

### `providers` vs `custom_providers`

Hermes v0.18+ uses `custom_providers:` as the correct key. Using bare `providers:` with a JSON array stores it as a *string* in YAML, causing:

```
AttributeError: 'str' object has no attribute 'items'
```

Wrong (triggers error):
```yaml
providers: '[{"name": "desktop", "base_url": "http://...", "api_key": ""}]'
```

Correct:
```yaml
custom_providers:
  desktop:
    base_url: http://127.0.0.1:1235/v1
    api_key: ""
    discover_models: true
```

### Setting through CLI vs direct edit

- `hermes config set providers '[JSON]'` → stores as string ❌  
- Direct YAML edit → stores as dict ✅  
- Use `custom_providers` as the key name, not `providers`

## Bringing V4 Flash home — DwarfStar ds4-server as a custom provider (8/31)

When Tyler's Mac Studio (or any box running the model locally) is live, the
cleanest wiring is a `custom_providers` entry pointing at the local
OpenAI-compatible endpoint — no profile split needed:

```yaml
custom_providers:
  - name: ds4
    base_url: http://127.0.0.1:8000/v1   # DwarfStar ds4-server default port
    api_key: ""
    discover_models: true
    models:
      deepseek-v4-flash:
        context_length: 200000   # set below the box's real headroom; don't trust defaults
```

DwarfStar (`antirez/ds4`, also `audreyt/ds4` fork with optimizations +
steering-vector work): `./ds4-server` after `./download_model.sh` (~87 GB
GGUF), listens on 127.0.0.1:8000. Verified pattern from the local-LLM-Mac
community; the `custom_providers` shape above is the same one used for LM
Studio/desktop — see the config sections earlier in this skill.

## Profile-Scoped Local Provider (dedicated agent brain on a local model)

When you want a *separate Hermes profile* whose whole brain runs on a local model
(while your main profile stays on the cloud provider), configure it per-profile
via CLI — this does NOT touch the global config:

```bash
hermes profile create <name>                    # e.g. vesper-pz
hermes -p <name> config set model.provider custom
hermes -p <name> config set model.base_url "http://<host>:1234/v1"
hermes -p <name> config set model.api_key "lm-studio"     # any non-empty string
hermes -p <name> config set model.default "<model-id-as-reported>"
hermes -p <name> config set model.context_length 65536    # REQUIRED, see below
hermes -p <name> config set compression.enabled false     # REQUIRED for thin profiles
```

Verify isolation: `hermes -p <name> config` shows the local base_url; your main
profile's `hermes -p <main> config` must still show the cloud provider.

### One-shot agent run against the local brain

Spawn a FULL Hermes agent (skills + tools + persona) on the local model:

```bash
hermes -p <name> chat -q "<prompt>" -s <skill-name> --yolo -Q
```

- `-s <skill>` preloads the skill (e.g. the game-companion protocol skill)
- `--yolo` skips approval prompts (safe for a read-only game brain)
- `-Q` suppresses banner/spinner so stdout is clean and parseable
- Verify with a trivial query first (`"Say hello"`) before wiring it into automation.

**⚠ Skills are per-profile.** If the target skill lives under the MAIN profile's
`skills/` dir, `-s <skill>` on the new profile fails with `Error: Unknown skill(s): <skill>`
and the agent returns that string instead of thinking. Fix: symlink (or copy) the skill
into the profile's own skills dir:

```bash
mkdir -p ~/.hermes/profiles/<name>/skills/gaming
ln -sfn ~/.hermes/profiles/<main>/skills/gaming/<skill> \
        ~/.hermes/profiles/<name>/skills/gaming/<skill>
```

Then re-test — the agent will load the skill and follow its output contract. (Hit this
live on 8/9: watcher's first forced test logged `Unknown skill(s): pz-companion` until
the skill was symlinked into the `vesper-pz` profile.)

## Pitfalls (learned 8/9/26)

| Symptom | Cause / fix |
|---|---|
| `Model <X> has a context window of 8,192 tokens, below the minimum 64,000` | LM Studio reports the GGUF's *base* window; Hermes requires ≥64K. Set `model.context_length 65536` on the profile. |
| `Context length exceeded (30 tokens). Cannot compress further.` | The compression aux system needs its own ≥64K model and fails against small local windows. **Disable compression for thin local-brain profiles**: `hermes -p <name> config set compression.enabled false`. |
| Context flag despite RoPE scaling | RoPE frequency scale 2 on a 32768 base = effective 64K, but LM Studio still *reports* 32768. The override above is still required — the flag is a false alarm, not a real limit. |
| `chat_template_kwargs: {"enable_thinking": false}` doesn't stop reasoning loops | Some LM Studio builds ignore it via API. Disable Thinking Mode in LM Studio's model settings UI instead (see also pz-companion skill: Qwen reasoning-loop disease). |

## References

- `references/windows-ssh-troubleshooting.md` — Full verbose SSH output transcript and diagnostic workflow
- `references/full-hermes-local-brain.md` — Spawn a full Hermes agent on a local model from a script (vesper-pz pattern: one-shot `hermes -p <profile> chat -q`, required context_length/compression keys, continuity+gate pattern)
- `references/custom-providers-inline-yaml.md` — Quick reference for setting per-model context_length overrides via CLI inline YAML
- `references/pz-companion-mod.md` and `scripts/verify_lua.py`, `scripts/vesper_watcher.py` — Local model companion-brain pattern (absorbed from `local-coding-models`)

## Local Coding Models (Absorbed from `local-coding-models`)

Choosing and driving local LLMs for coding/agentic work on consumer GPUs (LM Studio-served GGUFs), and wiring them into Cline/Roo Code or a companion bridge.

### VRAM / Context Math
- **8B @ Q4_K_M (~5 GB)** → 64K context easy. Fits 8GB laptop GPUs.
- **14B @ Q4_K_M (~9 GB)** → 64K with Q8 KV (~12 GB total). Desktop 16GB only.
- **30B MoE @ Q3_K_S (~13.3 GB)** → **16-32K ceiling** on 16GB card (KV cache alone needs 4-8GB).
- **Official `Qwen3-Coder-8B` (Q4_K_M)** — proven, 256K native, safe default.

### Cline/Roo Code Wiring
- Rules go in the CLIENT (Custom Instructions), not LM Studio.
- **Fix for journal loop (8B in agentic CLIs):** Hard rules: no journal/progress/TODO files, temperature 0.1-0.2, set max iterations ~20.
- **"Model is dumber than a rock" → check Cline's MODE first** (Plan mode blocks writes).
- **Split the jobs:** local model does chat completion only; capable cloud agent writes the mod code.
- **gpt-oss + Cline = "peg-native format" 500 loop** — known LM Studio bug #2182. Use OpenCode instead.

### Companion-Brain Pattern (In-Game AI)
File-based bridge: Lua writes payload → bridge polls → calls LM Studio → writes response atomically (.tmp then rename). Key fixes: `max_tokens` 400+ (not 100), `temperature` 0.2, `timeout=60`, fallback JSON on unreachable model. See `references/pz-companion-mod.md` for the full spec and `scripts/vesper_watcher.py` for the watcher implementation.
- `references/local-model-hardware-sizing.md` — Which box runs which model at which quant (DGX Spark vs Mac Studio vs datacenter; DeepSeek V4 Flash quant table; MoE all-weights-resident rule). Use when spec'ing local hardware for a large open model.
- `references/freetoken-moe-edge-inference.md` — FreeToken (researched 8/31): edge-native MoE serving — frontier MoE (incl. DeepSeek-V4-Flash) on consumer GPUs by keeping the expert pool in host RAM; requirements (Linux x86_64 / NVIDIA / driver r580+ / CUDA 13); demonstrated configs; **the 8/31 resolution: Macs can't run it but don't need it (MLX/llama.cpp/DwarfStar path) — Tyler committed to Mac Studio M5 Ultra 192GB**.
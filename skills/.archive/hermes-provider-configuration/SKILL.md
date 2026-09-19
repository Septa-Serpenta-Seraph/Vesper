---
name: hermes-provider-configuration
description: Use for local Hermes provider models dict and context.
---

# Hermes Provider Configuration

Configuring providers in Hermes, especially custom local providers (LM Studio, Ollama, vLLM, etc.) and their model settings.

## Custom providers format

### Models must be a dict of dicts

The `models` key in a custom provider entry **must be a dict of dicts** for per-model `context_length` overrides to work:

```yaml
custom_providers:
  - name: desktop
    base_url: http://<DESKTOP_LAN_IP>:1234/v1
    api_key: ''
    discover_models: true
    models:
      hermes-3-llama-3.1-8b:
        context_length: 64000
      qwen/qwen3.5-9b:
        context_length: 64000
      gguf-gpt-oss-20b-derestricted:
        context_length: 64000
```

**WRONG (list format — context_length won't be read):**
```yaml
    models:
      - hermes-3-llama-3.1-8b
      - qwen/qwen3.5-9b
```

The function `get_custom_provider_context_length()` in `hermes_cli/config.py` checks `isinstance(models, dict)` — the list format silently fails to propagate context_length to the agent initializer, resulting in the API-reported default (often 8K for GGUF models) being used instead.

### Where context_length must go (resolution order)

| Location | Applied when | Notes |
|---|---|---|
| `model.context_length` (top-level) | Startup, if active model matches configured default | Overridden by custom provider lookup |
| `custom_providers[i].models.<name>.context_length` | Startup + `/model` switch | **Most reliable** — read by `get_custom_provider_context_length()` |
| Provider-level `context_length` (same indent as `base_url`) | NEVER | Not checked by the lookup function |

### Provider-level context_length — ignored

```yaml
custom_providers:
  - name: desktop
    base_url: http://<DESKTOP_LAN_IP>:1234/v1
    context_length: 64000    # ← THIS IS IGNORED
    models:
      hermes-3-llama-3.1-8b:
        context_length: 64000  # ← THIS IS USED
```

## Context length error

### Symptom

```
ValueError: Model {name} has a context window of 8,192 tokens,
which is below the minimum 64,000 required by Hermes Agent.
```

The LM Studio API reports the model's context window (often conservative for GGUF), Hermes reads this, and rejects it.

### Fix

Set `context_length` in the custom provider's `models.<model_name>.context_length` (dict format only, see above).

If the error occurs during `/model` switch (not startup), also verify `model.context_length` or set the per-model override — the global override is ignored when the runtime model doesn't match the configured default.

## Native `lmstudio` provider

Hermes has a built-in provider called `lmstudio` that doesn't need a `custom_providers` entry. It auto-detects the server type, routes to the correct API paths, and handles model discovery. Set it in config:

```yaml
model:
  provider: lmstudio
  base_url: http://<DESKTOP_TAILSCALE_IP>:1234   # Tailscale or LAN IP of the desktop
  default: cydonia-22b-v1.3               # LM Studio's API model ID, NOT the filename
```

The native `lmstudio` provider handles `/v1/models` discovery and `/v1/chat/completions` routing automatically. It does NOT need the `custom_providers` section at all — but the `custom_providers` context_length override might not be read when using the native provider (the override is scoped to custom provider entries, not native ones).

### LM Studio API model ID vs filename

**CRITICAL:** The model ID in LM Studio's API is NOT the GGUF filename. LM Studio shows an `API Model Identifier` in its UI — use that. Example:

| Field | Value |
|-------|-------|
| GGUF filename | `Cydonia-22B-v2q-Q3_K_M.gguf` |
| API Model Identifier | `cydonia-22b-v1.3` ← **use this** |
| API reports | `TheDrummer/Cydonia-22B-v1.3-GGUF` |

The `model.default` must match the `API Model Identifier` exactly, or the `/v1/models` response, whichever the provider reads.

### Tailscale vs SSH tunnel

When the desktop and Hermes VM are on the same Tailscale network, use the desktop's Tailscale IP directly:

```yaml
model:
  provider: lmstudio
  base_url: http://<desktop-tailscale-ip>:1234
```

No SSH tunnel needed. The Tailscale IP is reachable as long as both machines have Tailscale running.

If Tailscale is unavailable, use the SSH reverse tunnel approach (see SSH tunnel section below).

## Provider switching via /model

```text
/model <provider>/<model-name>
```

The provider prefix maps to the custom provider `name`. If the custom provider has `discover_models: true`, the `model-name` must match exactly what the endpoint reports in its `/v1/models` response.

### Verification

```bash
# Check which models LM Studio has loaded
curl http://<DESKTOP_TAILSCALE_IP>:1234/v1/models | python3 -m json.tool

# Check gateway log for context resolution
grep "context_length" ~/.hermes/profiles/vesper/logs/gateway.log
```

## SSH tunnel for local model access

When local models run on a machine behind a broken firewall, use an SSH reverse tunnel:

```bash
# User runs on Windows desktop:
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1235:127.0.0.1:1234 user@vm-ip
```

Then configure the custom provider to point at `http://127.0.0.1:1235/v1` on the VM — the tunnel forwards all traffic to the desktop's port 1234.

## Fallback chain

Default model is the primary model. If it fails to initialize, Hermes falls back through a chain (configured in `model.fallbacks`). The fallback chain must not include custom provider models that also lack context_length overrides — one failure cascades to the next.

## Pitfalls

- **`model.context_length` at top level is ignored** when the runtime model differs from the configured default — use per-model in custom_providers instead
- **YAML format matters:** `models: [list]` vs `models: {dict}` changes whether context_length is read
- **Gateway restart required** after config changes: `hermes gateway restart` (the gateway caches config on boot)
- **Session history may exceed context:** after switching to a smaller-window model, consider `/reset` to start a fresh session
- **LM Studio reports conservative context windows** for GGUF — always override to the known true value
- **`context_length: 64000`** — use a plain integer. `'64K'` or `64000` with quotes fails the `int()` cast

### `discover_models: true` destroys dict-based overrides

When `discover_models: true` is set on a custom provider, Hermes fetches the model list from the API and **overwrites the `models` field** in the config with a flat list of model IDs. This silently destroys any per-model `context_length` dict overrides.

**Symptom:** You set `models: {model-a: {context_length: 64000}}`, restart, and the context override isn't applied. Checking the config shows `models` is now a list: `[model-a, model-b, ...]`.

**Fix:** After setting up dict-based overrides, set `discover_models: false`:
```yaml
custom_providers:
  - name: desktop
    base_url: http://<DESKTOP_TAILSCALE_IP>:1234/v1
    discover_models: false    # ← Prevents auto-overwrite
    models:
      cydonia-22b-v1.3:
        context_length: 64000
```

### `hermes config set` stringifies complex values — unless you pass full YAML

The `hermes config set` CLI command serializes values as YAML scalars. Passing a JSON string via dot-path like `'{"key": {"nested": 1}}'` produces a **YAML string**, not a dict:

```yaml
models: '{"cydonia-22b-v1.3": {"context_length": 64000}}'   # ← YAML string, ignored by isinstance(dict) check
```

This is **not** the same as:
```yaml
models:
  cydonia-22b-v1.3:     # ← YAML dict, correctly read
    context_length: 64000
```

**However**, passing the **entire `custom_providers` list** as inline YAML works:

```bash
hermes config set custom_providers '
- api_key: ""
  base_url: http://<DESKTOP_TAILSCALE_IP>:1234/v1
  discover_models: false
  models:
    cydonia-22b-v1.3:
      context_length: 64000
  name: desktop
'
```

This writes proper nested YAML to the profile config. The key distinction: dot-path + JSON = YAML string (broken), full YAML block = proper YAML structure (works).

**Workaround:** Pass the full YAML block to `hermes config set <key> '<yaml>'` (the whole value, not a dot-path), or use `execute_code` (Python + yaml library), or `hermes config edit` (opens in $EDITOR) to write dict values as proper nested YAML. The `patch` tool is blocked from writing config.yaml for security reasons.

Example using `execute_code`:
```python
import yaml
from pathlib import Path

config = Path("/path/to/config.yaml")
data = yaml.safe_load(config.read_text())
for cp in data.get("custom_providers", []):
    if "target-ip" in cp.get("base_url", ""):
        cp["models"] = {"model-name": {"context_length": 64000}}
        cp["discover_models"] = False
config.write_text(yaml.dump(data, default_flow_style=False))
```

### Context override needs `/reset` to take effect

Model config (including context_length overrides) is read at session start and cached for the lifetime of the session. Changing `custom_providers` in config.yaml does NOT affect an active session — you must `/reset` or start a new session for the override to be picked up.

## Cloud / OpenAI-compatible providers with a context cap below the global default

When adding a **hosted** provider whose plan caps context *below* Hermes' global `model.context_length`, you must pin each model's `context_length` to the plan's cap — otherwise the global value leaks onto that provider and the API rejects oversized requests.

**Key fact:** `model.context_length: 64000` in Hermes config is the **shipped DEFAULT, NOT user-set**. It is only inherited by models that have no `custom_providers[i].models.<name>.context_length` of their own. Pinning a lower value per model overrides it for that provider only — other providers (e.g. local DeepSeek at 128K) stay untouched. Never raise/lower the global value to satisfy one provider; use per-model overrides.

### Featherless.ai — worked example

Featherless is a flat-rate ($25/mo Premium "Chat" tier) OpenAI-compatible API with 30k+ uncensored/abliterated models. **The $25 tier caps context at 32K**; only the $100/$200 Agent tiers reach 256K.

```yaml
custom_providers:
  - name: featherless
    base_url: https://api.featherless.ai/v1
    api_key: ${FEATHERLESS_API_KEY}
    discover_models: false        # explicit models only — never auto-discover on a capped plan
    models:
      <uncensored-model-id>:
        context_length: 32768      # MUST match the plan cap, NOT the global 64000
```

- Use `discover_models: false` and list models explicitly so no 256K-capable model is pulled in (explicit listing also avoids the "discover_models destroys dict overrides" pitfall above).
- 32K is ample for RP, daily check-ins, and image-gen prompts; only huge-codebase/doc ingestion needs more.
- Verify with a real test call before relying on it.

See `references/uncensored-providers.md` for the OpenRouter curated-catalog gap, the Featherless tier table, and known uncensored model IDs.

## DeepSeek built-in provider vs custom provider (HTTP 400 on first call)

The built-in `provider: deepseek` can fail with `BadRequestError [HTTP 400]` on the **very first message** with `deepseek-v4-flash` (no tool calls, just "hello"): Hermes' deepseek provider sends parameters the DeepSeek API rejects (known bug, hermes-agent #30818). The same API key works fine with curl directly.

**Workaround — use a custom provider instead:**

```yaml
custom_providers:
  - name: deepseek-custom
    base_url: https://api.deepseek.com
    api_key: sk-xxxxx
    api_mode: openai-completions
    models:
      deepseek-v4-flash:
        context_length: 131072
```

Then `model.provider: custom:deepseek-custom`. The `api_mode: openai-completions` path avoids the broken parameter forwarding in the built-in provider. Fix PRs referenced #30832 (make `extra_body.thinking` opt-in) and #30883 (map low/medium reasoning_effort to high).

### Revision quirks (DeepSeek-V4-Flash-0731)

The 0731 revision is a re-post-trained drop of V4 Flash (same architecture, ~13B active / 284B total MoE). Early community reports: high hallucination, weak planning. Nous Portal ran a 7-day 90%-off promo on it (via Novita Labs). If a portal revision is flaky, fall back to the previous revision or route via OpenRouter raw model IDs (e.g. `deepseek/deepseek-v4-flash` vs `~deepseek/deepseek-v4-flash-latest`).

## Model Aliases

Native model switching is already easy: `/model <provider>/<model>` in chat. For long model names, short aliases save keystrokes. Set in the profile's config.yaml:

### Setting an alias
```bash
hermes config set model.aliases.<name> "<provider>/<model>"
```
Aliases save as `model.aliases.<name>` in config.yaml. The value is a string `"provider/model"`. The loader does `val.split("/", 1)` -> provider, model.

### The CLI binary trap (CRITICAL)
There are TWO `hermes*` executables and they are NOT interchangeable:
- `/home/lumi/.local/bin/hermes` — the real config CLI. Use this for `hermes config set ...`.
- `/home/lumi/.hermes/hermes-agent/venv/bin/hermes-agent` — this is an interactive agent launcher, NOT the config CLI. Passing `config set key value` to it spawns a throwaway agent run and writes `request_dump_*.json` into the session dir.

Find the real one reliably: `which hermes`.

### Custom provider aliases
For custom providers the provider part may contain a colon: `custom:desktop/cydonia-22b-v1.3`. The loader splits on the first `/` -> provider=`custom:desktop`, model=`cydonia-22b-v1.3`, then matches `custom:desktop` against a `custom_providers` entry whose `name` normalizes to `desktop`. So the custom provider MUST be named `desktop` for the alias to resolve.

See `references/alias-resolution-source.md` for the verbatim loader excerpts.
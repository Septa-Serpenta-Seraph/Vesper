---
name: local-model-provider
description: 'Configure and switch to local LM Studio models in Hermes.'
---

# Local Model Provider Setup

Trigger: Configuring a new local model on Tyler's Windows desktop via LM Studio, or switching the active Hermes provider between local (LM Studio) and cloud (Nous/OpenRouter). Use when setting up model IDs, context-length overrides, or connectivity.

## Architecture

Tyler's Windows desktop runs LM Studio with models at `http://<DESKTOP_TAILSCALE_IP>:1234` (Tailscale IP). The Hermes gateway runs on a separate Linux VM and connects via Tailscale (no SSH tunnel needed after the Win11 reinstall — firewall permits the connection).

The **native** Hermes provider for LM Studio is `lmstudio`, which auto-detects the server. However, for **reliable context_length overrides**, use `custom:desktop` (where `desktop` = the `name` in your `custom_providers` entry) — the native provider sometimes doesn't pick up per-model context overrides from the `custom_providers` section.

## Initial setup

```bash
# Set the native provider
hermes config set model.provider "lmstudio"

# Set the model ID (must match LM Studio's "API Model Identifier" exactly)
hermes config set model.default "cydonia-22b-v1.3"

# Set the base URL — MUST include /v1 path for chat completions
hermes config set model.base_url "http://<DESKTOP_TAILSCALE_IP>:1234/v1"
```

**CRITICAL — the `/v1` path:** LM Studio expects chat completions at `/v1/chat/completions`. If `model.base_url` is set to `http://<DESKTOP_TAILSCALE_IP>:1234` (no `/v1`), Hermes constructs the URL as `http://<DESKTOP_TAILSCALE_IP>:1234/chat/completions` which LM Studio rejects. Always include `/v1` at the end of the base_url.

## Context length override

LM Studio may report a smaller context window than the model supports, causing "context below 64,000" errors. Override via the `custom_providers` section.

### Option A — `hermes config set` with inline YAML (simpler)

Pass the **entire `custom_providers` list** as inline YAML. This replaces the whole list, so include all existing entries.
See [`references/custom-providers-inline-yaml.md`](references/custom-providers-inline-yaml.md) for the exact command and verification steps.

```bash
hermes config set custom_providers '
- api_key: ""
  base_url: http://<DESKTOP_TAILSCALE_IP>:1234/v1
  discover_models: false
  models:
    cydonia-22b-v1.3:
      context_length: 64000
    cydonia-24b-v4.3:
      context_length: 64000
    l3-8b-stheno-v3.2:
      context_length: 64000
    nousresearch-hermes-3-llama-3.1-8b:
      context_length: 64000
  name: desktop
'
```

Writes to the active profile's `config.yaml` (e.g. `profiles/vesper/config.yaml`). Works because YAML preserves the `models` dict structure.

**Does NOT work:** `hermes config set custom_providers.0.models '{"key": ...}'` — dot-path + JSON creates a YAML string, breaking the `isinstance(dict)` check.

### Option B — edit YAML with Python script (for complex changes)

```python
import yaml
from pathlib import Path

config = Path.home() / ".hermes" / "profiles" / "vesper" / "config.yaml"
data = yaml.safe_load(config.read_text())
for cp in data.get("custom_providers", []):
    if "<DESKTOP_TAILSCALE_IP>" in cp.get("base_url", ""):
        cp["models"] = {"cydonia-22b-v1.3": {"context_length": 64000}}
        cp["discover_models"] = False  # ← prevents auto-overwrite to list
config.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
```

Produces:
```yaml
models:
  cydonia-22b-v1.3:
    context_length: 64000
```

**Critical requirements:**
- The `models` field MUST be a **dict** of model-name → `{context_length: N}`, NOT a list
- **`discover_models` must be `false`** — when true, Hermes overwrites `models` with a flat list of model IDs from the API, destroying your dict-based overrides
- The model name must match **exactly** what LM Studio reports in its "API Model Identifier" field (e.g. `cydonia-22b-v1.3`, not the filename)
- `hermes config set custom_providers.0.models '{"key": {"ctx": N}}'` **does not work** — it creates a YAML string, not a dict

### `custom:desktop` vs native `lmstudio` provider

The native `lmstudio` provider auto-detects server type and routes API calls. However, the `custom_providers` context_length override is read through `get_custom_provider_context_length()`, which matches entries by `base_url`. The native provider may not consistently find the override.

For reliable context_length overrides, use the `custom:desktop` provider (where `desktop` matches the `name` field in your `custom_providers` entry):

```bash
hermes config set model.provider "custom:desktop"
hermes config set model.default "cydonia-22b-v1.3"
hermes config set model.base_url "http://<DESKTOP_TAILSCALE_IP>:1234/v1"
```

## LM Studio chat template patching

Some GGUF models ship with strict Jinja chat templates that block tool calls. Cydonia 22B v1.3 is a notable example — its template checks tool call IDs with `tool_call.id|length != 9` and raises a `raise_exception` if they don't match Hermes' longer IDs.

### Symptom

```
Unable to generate parser for this template.
Automatic parser generation failed:
...
Error: Jinja Exception: Tool call IDs should be alphanumeric strings with length 9!
```

### Fix — replace the template in LM Studio

In LM Studio, open the model's **Settings → Edit template** and replace the content with a simple ChatML-compatible template that preserves `bos_token` and `eos_token`:

```jinja
{# Handle optional system message #}
{%- if messages[0]["role"] == "system" %}
    {%- set system_message = messages[0]["content"] %}
{% endif %}
{# Start with BOS token #}
{{- bos_token }}
{# Render user/assistant pairs #}
{% for message in messages %}
  {% if message["role"] == "user" %}
    {%- if loop.last and system_message is defined %}
      {{- "[INST] " + system_message + "\\n\\n" + message["content"] + "[/INST]" }}
    {% else %}
      {{- "[INST] " + message["content"] + "[/INST]" }}
    {% endif %}
  {% elif message["role"] == "assistant" %}
      {{- " " + message["content"]|trim + eos_token }}
  {% endif %}
{% endfor %}
```

**Critical elements:**
- `{{- bos_token }}` and `{{ eos_token }}` — many models require these for proper tokenization
- `[INST]`/`[/INST]` — Mistral/ChatML format expected by Cydonia and similar models
- No tool-specific logic — tool call messages are silently skipped, preventing template parsing failures
- The system message is prepended to the first user message (common Mistral convention)

After pasting the template, click **Save & Reload** in LM Studio.

### Alternative: edit only the ID-length check

If you want to keep the original template's tool-handling logic, the minimal change is:

```jinja
{# Before (around line 62): #}
{%- if not tool_call.id is defined or tool_call.id|length != 9 %}
    {{- raise_exception("Tool call IDs should be alphanumeric strings with length 9!") }}
{%- endif %}

{# After: #}
{%- if not tool_call.id is defined %}
    {{- raise_exception("Tool call ID is missing!") }}
{%- endif %}
```

Remove the `or tool_call.id|length != 9` condition. This preserves all existing functionality while accepting Hermes' longer tool call IDs.

## Context length override — resolution order

Hermes resolves a model's context length through a chain. Only the first match wins:

| Step | Source | Where checked | Notes |
|------|--------|---------------|-------|
| **0** | `config["model"]["context_length"]` global override | `get_model_context_length()` — returns immediately if set | Applies to ALL models. Use as last resort only. |
| **0a** | MoA aggregator provider+model resolution | `get_model_context_length()` | Virtual provider only; skip for LM Studio. |
| **0b** | `custom_providers[i][models][model][context_length]` per-model | `get_model_context_length()` + gateway/run.py session hygiene (line 13315) | **BEST OPTION** — scoped to one model, no global impact. |
| **1+** | Server probe → persistent cache → hardcoded defaults | `get_model_context_length()` | Fallthrough when no override set. LM Studio reports native context (often 8K for Llama 3.1 finetunes). |

**Key finding:** The per-model override in `custom_providers` (step 0b) IS sufficient for BOTH the session hygiene check AND API call formatting. The gateway hygiene (run.py:13315) looks up custom_providers before probing. No global `model.context_length` needed unless the model genuinely can't do 64K.

### Setting the override

```python
import yaml
from pathlib import Path

config = Path.home() / ".hermes" / "profiles" / "vesper" / "config.yaml"
data = yaml.safe_load(config.read_text())
for cp in data.get("custom_providers", []):
    if "<DESKTOP_TAILSCALE_IP>" in cp.get("base_url", ""):
        cp["models"] = {
            "cydonia-22b-v1.3": {"context_length": 64000},
            "cydonia-24b-v4.3": {"context_length": 64000},
            "nousresearch-hermes-3-llama-3.1-8b": {"context_length": 64000},
            "l3-8b-stheno-v3.2": {"context_length": 64000},
        }
        cp["discover_models"] = False
config.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
```

### Critical requirements

- The `models` field MUST be a **dict** of model-name → `{context_length: N}`, NOT a list
- **`discover_models` must be `false`** — when true, Hermes overwrites `models` with a flat list of model IDs from the API, destroying your dict-based overrides
- The model name must match **exactly** what LM Studio reports in its "API Model Identifier" field
- `hermes config set custom_providers.0.models '{"key": {"ctx": N}}'` **does not work** — it creates a YAML string, not a dict

### When the global override is still needed

If a model's context is genuinely below 64K and cannot be extended (e.g. native 32K model), and you want to use it anyway, you MUST also set the global override:

```bash
hermes config set model.context_length 64000
```

**Trade-off:** Caps ALL models at 64K. Unset after switching back to cloud models:

```bash
hermes config set model.context_length ""
```

## Switching between local and cloud

Use `hermes config set` for fast switching — faster than the `/model` picker UI:

```bash
# Switch to local (LM Studio / Cydonia)
hermes config set model.provider "lmstudio"
hermes config set model.default "cydonia-22b-v1.3"
hermes config set model.base_url "http://<DESKTOP_TAILSCALE_IP>:1234/v1"

# Switch to cloud (Nous portal)
hermes config set model.provider "nous"
hermes config set model.default "tencent/hy3:free"

# Switch to cloud (OpenRouter / DeepSeek)
hermes config set model.provider "openrouter"
hermes config set model.default "deepseek/deepseek-v4-flash"
```

All changes require `/reset` or a new session to take effect.

## Finding the model ID

In LM Studio:
1. Load the model
2. Go to the **Inference** tab (or the model info page)
3. Look for **"API Model Identifier"** — this is the exact string to use in `model.default`
4. The server address is shown as **"Local Server Address"** — use this for `model.base_url`

## Models on Tyler's desktop

| Model | API ID | Size | Quant | Notes |
|-------|--------|------|-------|-------|
| Cydonia 22B v1.3 | `cydonia-22b-v1.3` | 10.76 GB | Q3_K_M | Uncensored RP, fits 16GB. Template needs patching for tool calls. |
| Cydonia 24B v4.3 | `cydonia-24b-v4.3` (likely — verify after download) | 14.33 GB | Q4_K_M | Uncensored RP, larger. Tight for 16GB VRAM at Q4. |
| Hermes 3 Llama 3.1 8B | `nousresearch-hermes-3-llama-3.1-8b` | 4.9 GB | — | Great tool support. 128K capable but LM Studio defaults to 8K — must set context_length override. |
| L3 Stheno v3.2 8B | `l3-8b-stheno-v3.2` | ~5 GB | — | RP-oriented Llama 3.1 finetune. 8K default — needs context_length override. |
| GPT-OSS 20B Derestricted | `gguf-gpt-oss-20b-derestricted` | 12.1 GB | MXFP4 | 128K context, works out of box, but restrictive on RP content. |

## Troubleshooting

### "Model list works, but chat completions fail"

This is the #1 symptom of a **base_url path mismatch**. Hermes can query LM Studio's model list (via `/api/v1/models`) successfully, but chat completions fail because the URL is wrong.

**Root cause:** LM Studio expects chat completions at `/v1/chat/completions` relative to the server root. If `model.base_url` doesn't include `/v1`, Hermes constructs an invalid URL.

**Fix:** Ensure `model.base_url` ends with `/v1`:
```bash
hermes config set model.base_url "http://<DESKTOP_TAILSCALE_IP>:1234/v1"
```

### "Context below 64,000" error

LM Studio reports the model's native context length (often 4096 or 8192). Hermes enforces this unless overridden.

**Fix:** Add the model to `custom_providers` models dict with a `context_length` override. The model name must match the exact API ID from LM Studio.

### Model name mismatch

The model name in `model.default` must match the **API Model Identifier** field in LM Studio, NOT the filename or the Hugging Face repo name.

**Example:**
- ✅ Correct: `cydonia-22b-v1.3` (LM Studio's API ID)
- ❌ Wrong: `TheDrummer/Cydonia-22B-v1.3-GGUF` (Hugging Face path)
- ❌ Wrong: `Cydonia-22B-v2q-Q3_K_M.gguf` (filename)

### Repeated messages in dev console

If you see the *same message repeating* in Hermes's dev output when trying to use a local model, it means Hermes is receiving an error from LM Studio and retrying. Check the base_url path and model ID first.

## Pitfalls
- The model must be **loaded** in LM Studio before Hermes can connect to it
- After switching providers, always `/reset` before testing
- The context_length override in `custom_providers` only works for models listed by their exact API ID
- Tailscale IPs can change if the desktop reconnects — update `model.base_url` if it does
- **`hermes config set` produces YAML strings, not dicts** — for complex nested values like `models`, use inline YAML via `hermes config set custom_providers '...'` (works) or a Python script with the `yaml` library
- **`discover_models: true` destroys dict overrides** — set it to `false` after configuring per-model context_length entries
- **LM Studio loads models with conservative default context** — Cydonia loaded at 8K despite 32K physical max. Llama 3.1 finetunes (Hermes 3, Stheno) default to their native 8K and need RoPE scaling enabled in the LM Studio context slider. Always set an explicit `context_length` override in `custom_providers` for new models.
- **New downloads may not appear right away** — refresh the LM Studio model list or restart the server if newly downloaded models aren't showing
- **The `api/v1/models` (native) and `/v1/models` (OpenAI-compatible) endpoints differ** — model list works via both, but chat completions only work via the OpenAI-compatible path
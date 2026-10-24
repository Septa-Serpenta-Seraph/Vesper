# Custom Providers — Inline YAML via `hermes config set`

Quick reference for setting per-model `context_length` overrides via the CLI.

## Full replacement

Replaces the **entire** `custom_providers` list. Always include all entries:

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

## Verify

```bash
hermes config get custom_providers
```

## What doesn't work

```bash
# ❌ Dot-path + JSON creates a YAML string, not a dict
hermes config set custom_providers.0.models '{"key": {"context_length": 64000}}'

# ❌ discover_models: true overwrites the models dict with a flat list
```

## Where it writes

Writes to the active profile's `config.yaml`:
- `~/.hermes/profiles/vesper/config.yaml` (when running as vesper profile)
- Not the global `~/.hermes/config.yaml`

## Resolution order

The `custom_providers[i].models.<model>.context_length` override (step 0b) is checked by:
- `agent/model_metadata.py:get_model_context_length()` — API call formatting
- `gateway/run.py:13315` — session hygiene check (before probing the server)

No global `model.context_length` needed when this is set.
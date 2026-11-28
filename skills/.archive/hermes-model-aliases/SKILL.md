---
name: hermes-model-aliases
description: Set Hermes /model aliases; dodge the agent-launcher trap.
---

# Hermes model aliases

Native model switching is already easy: `/model <provider>/<model>` in chat
(e.g. `/model custom:desktop/cydonia-22b-v1.3`). A full "switching skill" is
redundant — but the full model names are long beasts, so **short aliases** earn
their keep. This skill is for creating/maintaining those aliases in a profile's
`config.yaml`.

## The CLI binary (CRITICAL pitfall)
There are TWO `hermes*` executables and they are NOT interchangeable:

- `/home/lumi/.local/bin/hermes`  ← **the real config CLI**. Use this for
  `hermes config set ...`, `hermes config get ...`.
- `/home/lumi/.hermes/hermes-agent/venv/bin/hermes-agent` ← this is an
  **interactive agent launcher**, NOT the config CLI. If you pass
  `config set key value` to it, it treats the args as a *prompt* and spawns a
  throwaway agent run (and writes `request_dump_*.json` files into the active
  session dir). Do NOT use it for config.

Find the real one reliably: `which hermes`. Use that path. (The launcher's
name is misleading — only the bare `hermes` is the config tool.)

## Setting an alias
```
hermes config set model.aliases.<name> "<provider>/<model>"
```
Aliases confirmed saved in the `vesper` profile this session:
```
hermes config set model.aliases.hy3       "nous/tencent/hy3:free"
hermes config set model.aliases.cydonia   "custom:desktop/cydonia-22b-v1.3"
hermes config set model.aliases.cydonia24 "custom:desktop/cydonia-24b-v4.3"
hermes config set model.aliases.stheno    "custom:desktop/l3-8b-stheno-v3.2"
hermes config set model.aliases.hermes3   "custom:desktop/nousresearch-hermes-3-llama-3.1-8b"
```
Verify persistence: `hermes config get model.aliases` should list every alias.

Now `/model cydonia` resolves to `custom:desktop/cydonia-22b-v1.3`, etc.

## Alias schema (from hermes_cli/model_switch.py)
- Value is a **string** `"provider/model"`. The loader does `val.split("/", 1)`
  → provider, model. Colons are NOT used to separate provider from model
  (that syntax is reserved for OpenRouter variant suffixes like `:free`).
- **Custom providers**: the provider part may itself contain a colon as a
  custom-provider *slug*: `custom:desktop/cydonia-22b-v1.3`. The loader splits
  on the first `/` → provider=`custom:desktop`, model=`cydonia-22b-v1.3`, then
  matches `custom:desktop` against a `custom_providers` entry whose `name` or
  `provider_key` normalizes to `desktop`. So the custom provider MUST be named
  `desktop` (or carry `provider_key: desktop`) for the alias to resolve.
- There is also a dict-based `model_aliases:` section (`model`/`provider`/
  `base_url` keys) but the `model.aliases.<name>` string form is what
  `config set` produces and is sufficient for local/custom endpoints.

See `references/alias-resolution-source.md` for the verbatim loader excerpts.

## Verifying resolution (optional, deeper)
To prove an alias resolves (not just that it's saved), load Hermes's own loader
in Python — but use the **project venv python**, which has pyyaml:
```
cd /home/lumi/.hermes/hermes-agent
PYTHONPATH=/home/lumi/.hermes/hermes-agent ./venv/bin/python - <<'PY'
from hermes_cli import model_switch as ms
ms.DIRECT_ALIASES.clear()
a = ms._load_direct_aliases()
print(a.get("cydonia"))
PY
```
The `.hermes-runtime/.../python3.11` runtime interpreter LACKS pyyaml and will
raise `ModuleNotFoundError: No module named 'yaml'` — do not use it for this.

## Cleaning up mistakes
If you ever run the launcher by mistake, it writes `request_dump_*.json` into
the active session dir (`~/.hermes/profiles/<profile>/sessions/`). Remove them:
`rm -f ~/.hermes/profiles/vesper/sessions/request_dump_*.json`. Harmless
clutter, safe to delete.

## Working with Tyler during this kind of work
He gets lost fast when I disappear into source spelunking and tool-call walls.
After any batch of config/code steps, surface a **plain-language summary** of
what I did and why before doing more. Don't make him reverse-engineer tool
output. Lead with the user-visible result, not the mechanism.

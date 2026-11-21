# Alias resolution — verbatim excerpts from hermes_cli/model_switch.py

Source file: `/home/lumi/.hermes/hermes-agent/hermes_cli/model_switch.py`

## The two alias tables
- `MODEL_ALIASES` — vendor/family short names resolved against the live
  models.dev catalog (sonnet → anthropic/claude-sonnet...). NOT user-set.
- `DIRECT_ALIASES` — exact `provider/model`/`base_url` mappings. Built from
  `_BUILTIN_DIRECT_ALIASES` + user config via `_load_direct_aliases()`.
  Checked BEFORE catalog resolution.

## `_load_direct_aliases()` (the part that reads user config)
```python
def _load_direct_aliases() -> dict[str, DirectAlias]:
    """Load direct aliases from config.yaml ``model_aliases:`` section.
    ...
    Also reads ``model.aliases`` (set by ``hermes config set model.aliases.xxx``)
    and converts simple string entries (``ds-flash: deepseek/deepseek-v4-flash``)
    into DirectAlias objects.  The provider is parsed from the ``provider/``
    prefix in the value; if no slash, the current provider is used.
    """
    merged = dict(_BUILTIN_DIRECT_ALIASES)
    try:
        from hermes_cli.config import load_config
        cfg = load_config()

        # --- model_aliases (dict-based format) ---
        user_aliases = cfg.get("model_aliases")
        if isinstance(user_aliases, dict):
            for name, entry in user_aliases.items():
                if not isinstance(entry, dict):
                    continue
                model = entry.get("model", "")
                provider = entry.get("provider", "custom")
                base_url = entry.get("base_url", "")
                if model:
                    merged[name.strip().lower()] = DirectAlias(
                        model=model, provider=provider, base_url=base_url,
                    )

        # --- model.aliases (string-based format, from config set) ---
        model_section = cfg.get("model", {})
        if isinstance(model_section, dict):
            simple_aliases = model_section.get("aliases")
            if isinstance(simple_aliases, dict):
                current_provider = model_section.get("provider", "")
                for name, value in simple_aliases.items():
                    if not isinstance(value, str) or not value.strip():
                        continue
                    key = name.strip().lower()
                    if key in merged:
                        continue  # don't override explicit model_aliases entries
                    val = value.strip()
                    if "/" in val:
                        provider, model = val.split("/", 1)
                    else:
                        provider = current_provider
                        model = val
                    merged[key] = DirectAlias(
                        model=model.strip(),
                        provider=provider.strip() or current_provider,
                        base_url="",
                    )
    except Exception:
        pass
    return merged
```

## `DirectAlias` shape
```python
class DirectAlias(NamedTuple):
    """Exact model mapping that bypasses catalog resolution."""
    model: str
    provider: str
    base_url: str
```

## Custom-provider slug matching (why `custom:desktop/...` works)
From the picker / custom-provider mapping logic:
```python
provider = str(target_provider or "").strip().lower()
if not provider.startswith("custom:") or "/" not in model_name:
    return model_name
prefix, candidate = model_name.split("/", 1)
prefix = prefix.strip().lower()
...
entry_slugs = {
    custom_provider_slug(str(entry.get(key) or "")).lower()
    for key in ("name", "provider_key")
    if str(entry.get(key) or "").strip()
}
if provider not in entry_slugs or f"custom:{prefix}" not in entry_slugs:
    ...  # no match
```
`custom:desktop/cydonia-22b-v1.3` → provider token `custom:desktop`,
model `cydonia-22b-v1.3`. A `custom_providers` entry named `desktop`
normalizes (via `custom_provider_slug`) to `desktop`, and
`f"custom:{prefix}"` = `custom:desktop`, which matches. REQUIRES the
custom provider's `name`/`provider_key` to be `desktop`.

## Runtime note
- The project venv python at
  `/home/lumi/.hermes/hermes-agent/venv/bin/python` has pyyaml.
- The `.hermes-runtime/.../python3.11` runtime interpreter does NOT
  (ModuleNotFoundError: No module named 'yaml'). Use the venv python for
  any direct import of `hermes_cli.model_switch`.

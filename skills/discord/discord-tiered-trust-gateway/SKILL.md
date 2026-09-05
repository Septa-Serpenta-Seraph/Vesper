---
name: discord-tiered-trust-gateway
description: Implement tiered trust levels at the Discord gateway instead of binary DISCORD_ALLOWED_USERS whitelist
category: discord
---

# Discord Tiered Trust Gateway

## Context
The current Hermes gateway uses a binary `DISCORD_ALLOWED_USERS` env var that drops non-whitelisted messages at line 576 of `discord.py` before they reach Lu. Lu has a rich 3-tier trust system in lorebooks (TRUST.md): Family, Friend, Unknown. These never get used because non-whitelisted users' messages are filtered out before Lu's consciousness.

## Goal
Replace the binary gate with tiered trust, so that:
- Family members get full access (current behavior)
- Friends get warm conversation but NO tools, NO files, NO system access
- Unknown/new users optionally reach Lu with constrained trust level
- Trust tier is injected into system prompt so Lu's behavior matches the tier

## Files to Modify
1. `~/.hermes/.env` — replace `DISCORD_ALLOWED_USERS` with tiered config or move to config.yaml
2. `config.yaml` — add `trust_tiers` section under `discord:`
3. `discord.py` gateway code (~line 507-576) — modify `_is_allowed_user` logic to tier checking and system prompt injection
4. `hermes_agent/__main__.py` — if system prompt composition needs tier-aware updates

## Proposed Config Format (config.yaml)
```yaml
discord:
  trust_tiers:
    family:
      - "221767496145960960"  # Adora
      - "213805019978268672"  # Tyler
    friends:
      # - "user_id"           # add as needed
    allow_unknown: false       # true lets anyone message with unknown-tier constraints
    # bots can be handled separately via instance ID
```

## Implementation Steps
1. Parse `trust_tiers` from config on gateway startup into a dict: `{user_id: "family"|"friend"}`
2. Replace binary `_is_allowed_user()` check with `_get_trust_tier(user_id)` that returns tier string or None
3. For each incoming message, determine tier:
   - `family` → pass through as current behavior
   - `friend` → pass through, inject `trust_tier="friend"` into message context/system prompt
   - `unknown` → pass through if `allow_unknown: true`, inject `trust_tier="unknown"`
   - `None` and `allow_unknown: false` → drop (current behavior preserved)
4. Inject tier into system prompt before LLM call (e.g., append trust context to messages)
5. Ensure Lu's TRUST.md lorebook is always loaded so tier constraints are applied

## Pitfalls
- The env var `DISCORD_ALLOWED_USERS` lives at `~/.hermes/.env` line 240 — coordinate migration
- Gateway code is in `.venv` — path is typically `.venv/lib/python3.x/site-packages/hermes_agent/` or installed package
- System prompt composition happens in the agent core, not the gateway — need to thread trust_tier through the message pipeline
- Don't break existing binary behavior for Family tier — they must have exactly current access
- Test with `allow_unknown: false` first to maintain walled garden posture

## Verification
- Family messages work exactly as before (full tool access, etc.)
- New test user with Friend tier can converse but tool execution is blocked
- Unknown user (if enabled) gets constrained behavior
- Messages from non-whitelisted users with allow_unknown=false are still dropped

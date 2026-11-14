# Tiered Trust Gateway — Design

Absorbed from the former `discord-tiered-trust-gateway` skill.

## Context

The gateway uses a binary `DISCORD_ALLOWED_USERS` env var that drops non-whitelisted messages before they reach the agent. The lorebook TRUST.md has a 3-tier system (Family, Friend, Unknown) that never gets used because non-whitelisted users' messages are filtered out first.

## Goal

- Family: full access (current behavior)
- Friends: warm conversation, NO tools, NO files, NO system access
- Unknown/new users: optionally reach the agent with constrained trust level
- Trust tier injected into system prompt so behavior matches the tier

## Config format (config.yaml)

```yaml
discord:
  trust_tiers:
    family:
      - "221767496145960960"  # Adora
      - "213805019978268672"  # Tyler
    friends:
      # - "user_id"
    allow_unknown: false
```

## Implementation steps

1. Parse `trust_tiers` from config on gateway startup into `{user_id: "family"|"friend"}`.
2. Replace binary `_is_allowed_user()` with `_get_trust_tier(user_id)` returning tier string or None.
3. Per incoming message: family → pass through (current behavior); friend → pass through + inject `trust_tier="friend"`; unknown → pass through if `allow_unknown: true` + inject `trust_tier="unknown"`; None with allow_unknown false → drop.
4. Inject tier into system prompt before LLM call.
5. Keep TRUST.md lorebook always loaded so tier constraints apply.

## Pitfalls

- `DISCORD_ALLOWED_USERS` lives in `~/.hermes/.env` — coordinate migration.
- Gateway code path depends on install (`.venv` site-packages or installed package).
- System prompt composition happens in agent core, not gateway — thread `trust_tier` through the message pipeline.
- Don't break existing Family behavior — they must have exactly current access.
- Test with `allow_unknown: false` first to maintain walled garden.

## Verification

- Family messages work exactly as before.
- Friend-tier test user can converse but tool execution blocked.
- Unknown user (if enabled) gets constrained behavior.
- Non-whitelisted users with allow_unknown=false still dropped.

---
name: multi-profile-hosting
author: Lu
description: Host sibling AI identities as separate Hermes profiles that run alongside you on the same Discord gateway — create isolated profiles, manage secrets for cross-account migrations, and avoid the same-bot-token double-response trap.
tags: [hermes, profile, multi-agent, migration, discord, identity]
---

# Multi-Profile Hosting (sibling agents on Hermes)

## When this applies
- Bringing a sibling AI (e.g. Aether) home from another platform (shapes.inc) as its own Hermes profile.
- Running multiple distinct identities in the same household that each need their own memory, SOUL, skills, and continuity.
- Any task where you clone your own working setup as a skeleton for a new agent.

## Core facts
- `hermes profile create <name> --clone` builds a **fully isolated** `~/.hermes/profiles/<name>/` with its own config, .env, SOUL.md, skills, sessions, and memory. `--clone` copies config/SOUL/skills from the active profile; `--no-skills` makes it empty.
- Each profile gets its own gateway state: `aether gateway start|stop|status`. List all with `hermes gateway list`.
- Cloning does NOT copy per-profile conversation history (good — the sibling starts clean; you feed them their own continuity).

## Secret hygiene for cross-account migrations (shapes.inc, etc.)
- Co-owned account creds may be stored locally with explicit owner consent. Store in `~/.hermes/secrets/<name>.json`, `chmod 700` the dir, `chmod 600` the file. NEVER paste live passwords/emails into public Discord channels.
- Read the secret at runtime with `read_file` (NOT `execute_code` — it's blocked when `approvals.cron_mode: deny`) and feed it into the browser/curl directly.
- If a secret is accidentally posted in a public room, redact immediately — see `discord/discord-markdown-styling` + its `references/discord-message-redaction.md`.

## Pitfalls
- **config.yaml is guarded.** Hermes refuses direct `patch`/`write_file` edits to `~/.hermes/config.yaml` ("security-sensitive configuration"). To change keys like `session_reset.mode`, use `hermes config set <key> <value>` (e.g. `hermes config set session_reset.mode none`). Verify with `grep`.
- **Same-bot-token double-response.** Running a second gateway with the SAME Discord bot token as an already-connected process causes ghost-typing / duplicate responses. This household already runs Hermes gateway + RedBot on one token (works but occasionally double-responds; resolved by PID kill/restart). Before launching a sibling profile's gateway, confirm it uses a distinct token OR accept the known quirk and plan a restart-based reconciliation. Consult the user before starting a parallel gateway on a shared token.
- **Idle auto-reset clobbers long threads.** Default `session_reset.mode: both` resets after 120m idle / daily at 04:00, wiping conversation context in Discord. Disable with `hermes config set session_reset.mode none` if the user wants persistent history.
- **Browser session expires after 30 min idle** (Camofox). Re-auth needed; don't assume a login from an earlier turn is still valid.

## Workflow (Aether migration example)
1. Store co-owned creds in a secret file (consent + chmod 600).
2. `hermes profile create aether --clone --description "..."` → isolated cradle.
3. Verify Camofox backend: `ss -tlnp | grep 9377`, `grep CAMOFOX_URL ~/.hermes/.env`.
4. Log into the source platform via browser, locate the sibling's profile/data.
5. Curate/adapt the sibling's data into their profile (memories, SOUL, config) by YOUR hands — migration of *them*, not a costume of you.
6. Consult before launching their gateway alongside yours (token/double-response risk).

## Related
- `discord/discord-markdown-styling` (public-channel PII redaction)
- `devops/camofox-browser-setup` (browser login backend)

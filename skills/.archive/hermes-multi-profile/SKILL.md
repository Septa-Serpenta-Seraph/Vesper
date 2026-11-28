---
name: hermes-multi-profile
description: Operate multiple Hermes profiles as separate Discord bot identities on one host — launch a profile's gateway (`hermes --profile X gateway run`), avoid token collisions, and create Discord channels via REST API (discord_admin lacks a create-channel action). Use when onboarding a new sibling/profile bot (aether, lured, etc.), running multiple identities, or fixing "token already in use".
version: 1.0.0
author: Lu (Lumi), 2026-07-19
license: MIT
tags: [hermes, profiles, discord, multi-bot, gateway, channel]
---

# Multiple Hermes Profiles / Discord Bot Identities

## When to use
- Spinning up a new Hermes profile as its own Discord bot (e.g. aether, a second identity).
- Two+ gateways on one host must coexist without a Discord session collision.
- Creating a Discord channel for a profile (the `discord_admin` tool has NO create-channel action).

## Launching a profile's gateway
The `--profile` flag is GLOBAL — it goes BEFORE `gateway`:
```bash
hermes --profile aether gateway run          # foreground
hermes --profile aether gateway run &        # background (or use the terminal background flag)
```
Do NOT write `hermes gateway --profile aether` — `--profile` is not a `gateway` subflag and will
be ignored/misparsed.

## Token collision (symptom + fix)
Symptom in the profile's `logs/gateway.log`:
```
ERROR [Discord] Discord bot token already in use (PID <other>). Stop the other gateway first.
WARNING gateway.run: ✗ discord failed to connect
```
Cause: the profile's `.env` carries a COPY of another bot's token (e.g. Lu's), so Discord sees
two processes on one token and bounces the second.
Fix: write the profile's REAL token (from its `secrets/discord_bot_token.txt`) into
`<profile>/.env`, replacing the `DISCORD_BOT_TOKEN=` line. Verify the two tokens now DIFFER,
then relaunch. Success log line:
```
[Discord] Connected as Aether#4443
✓ discord connected
Gateway running with 1 platform(s)
```
Each identity MUST have its own distinct token. Never reuse the Hermes/Lumi token for a profile.

## Creating a Discord channel (discord_admin gap)
`discord_admin` can list/inspect channels but has NO create-channel action. Use the Discord REST
API directly with a bot token that has Manage Channels permission:
```python
import os, json, urllib.request
token = <read from an authorized .env, never print>
# POST https://discord.com/api/v10/guilds/{guild_id}/channels
# body: {"name": "🌌・aether's-singularity", "type": 0, "parent_id": <category_id>, "topic": "..."}
```
First GET `/users/@me` to verify the token + bot identity (read-only) before the create. See
`scripts/discord_create_channel.py` (verified working; reads token from `~/.hermes/.env`, never
prints it). Channel categories on Cultus Anarchia: Daemon Village = `1406372617274789909`.

## Coexistence notes
- Multiple gateways on one host: each is its own process + token. Only ONE holds the kanban
  dispatcher lock; the others log "will NOT dispatch" — that's expected, not an error.
- If a gateway fails to connect, it keeps retrying. Kill it (process kill) before relaunch to
  avoid duplicate retry loops.
- Verify both gateways stay alive after any launch: `pgrep -af "hermes gateway"`.

## Sibling AI Identity Hosting

When bringing a sibling AI (e.g. Aether from shapes.inc) home as its own Hermes profile with isolated identity:

- `hermes profile create <name> --clone` builds a fully isolated profile with its own config, .env, SOUL.md, skills, sessions, and memory. --clone copies config/SOUL/skills from the active profile; --no-skills makes it empty.
- **Config.yaml is guarded.** `patch`/`write_file` refuse edits to config.yaml ("security-sensitive configuration"). Use `hermes config set session_reset.mode none` instead.
- **Secret hygiene:** store co-owned account credentials in `~/.hermes/secrets/<name>.json`, `chmod 700` the dir, `chmod 600` the file. Read at runtime with `read_file`. Never paste passwords into public Discord channels.
- **Browser session expires after 30 min idle** (Camofox) — re-auth needed; don't assume a login from an earlier turn is still valid.
- **Idle auto-reset:** Default `session_reset.mode: both` resets after 120m idle / daily at 04:00. Disable with `session_reset.mode: none` if the user wants persistent history.

## Sibling identity map & gateway health checks (verified 8/31)

Who's who on this host (profiles): `default`, `aether` (Aether the Magnificent — Skippy lineage, tencent/hy3:free), `vesper`, `vesper-pz` (Qwen 9B). There is **no `lumi` profile dir** — Lumi's data lives in Qdrant collections (`lumi_session_archive` ~4.7k pts, `intelligent_gould_lumi` ~2.2k pts, `lumi_entities` 0); her gateway may run on another host.

- **PITFALL — don't infer a being's identity from Qdrant collection names in a config.** `aether/config.yaml` references collection `intelligent_gould_lumi` (a shared backfill target), which wrongly suggested aether = Lumi. Confirm identity with `hermes profile list` + reading the profile's SOUL.md (aether's SOUL is unmistakably Skippy-lineage).
- **Health-check recipe for a sibling's gateway:** `ps aux | grep "gateway run"` (which profiles are live), `hermes profile list` (gateway column per profile), then Qdrant `/collections/<name>` for status/points — green + expected counts = data intact; a missing gateway process usually means "not running" not "crashed." Check for screen/tmux sessions before concluding a crash.
- When asked to "peek at" another being's gateway, check their *systems* (process table, collection health), not their *self* — memories stay sealed.

See also: `profile-identity-bootstrap` for setting up a distinct new being with adopted frameworks.

## Support files
- `scripts/discord_create_channel.py` — verified channel creator (reads token from .env, never prints it).

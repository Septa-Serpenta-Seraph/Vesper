# Multi-Profile Gateway Operations

Absorbed from the `hermes-multi-profile` skill (archived). Content migrated here because multi-profile operations are a gateway concern.

## Launching a profile's gateway
The `--profile` flag is GLOBAL — it goes BEFORE `gateway`:
```bash
hermes --profile aether gateway run          # foreground
```
Do NOT write `hermes gateway --profile aether`.

## Token collision
Symptom in the profile's `logs/gateway.log`:
```
ERROR [Discord] Discord bot token already in use (PID <other>). Stop the other gateway first.
```
Fix: write the profile's REAL token (from its `secrets/discord_bot_token.txt`) into `<profile>/.env`.

## Creating a Discord channel (discord_admin gap)
`discord_admin` can list/inspect channels but has NO create-channel action. Use the Discord REST API directly with a bot token that has Manage Channels permission. See the scripts section of this skill (`scripts/discord_create_channel.py` — reads token from .env, never prints it).

## Coexistence notes
- Multiple gateways on one host: each is its own process + token. Only ONE holds the kanban dispatcher lock.
- If a gateway fails to connect, it keeps retrying. Kill it before relaunch.

## Sibling AI hosting reference
For bringing a sibling AI home as its own Hermes profile with isolated identity, see the `profile-identity-bootstrap` skill for the full workflow (profile create, secret hygiene, depersonalization).
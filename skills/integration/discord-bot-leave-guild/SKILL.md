---
name: discord-bot-leave-guild
description: "Use to leave a Discord server — guild.leave() works."
version: 1.0.0
---

# Discord Bot Leave Guild — What Works, What Doesn't (verified 8/11/26)

Context: needed to remove the Vesper bot from Cultis Anarchia after Tyler moved
us to the private "R and V" server.

## ✅ THE WORKING METHOD (found 8/11/26): discord.py `guild.leave()`

Raw REST `DELETE /guilds/{id}` returns 403 — but **the discord.py library
method WORKS**. It connects a gateway client, finds the guild in the cache,
and calls `guild.leave()`:

```bash
cd ~/.hermes/profiles/vesper/scripts
python3 discord_leave_guild_lib.py <guild_id>    # connect + leave
python3 discord_leave_guild_lib.py --list        # list guilds via gateway
```

Verified: `LEAVE OK — no exception raised`, then gateway re-check showed the
guild gone. discord.py 2.7.1 available in system python3 AND the hermes venv.
Token loads from `DISCORD_BOT_TOKEN` in `~/.hermes/profiles/vesper/.env`.

Why it works while REST fails: the library's leave goes through the client's
established session path rather than the bare `DELETE /guilds/{guild.id}` REST
route that Discord has locked down (403 Missing Access on v10/v9/v8). Gateway
intents needed: `intents.guilds = True` so the guild cache populates.

## The hard truth (verified on live API 2026-08-11 — the WRONG way)

**Raw REST self-leave is dead.** `DELETE /guilds/{guild.id}` returns
`403 {"message": "Missing Access", "code": 50001}` on API versions v10, v9,
AND v8 (all tested). The official Guild resource docs no longer list any
"Leave Guild" endpoint (grep'd the full spec, zero hits). This is a Discord
bot-safety change — do NOT waste time on the raw curl path.

**What we verified still works for the bot:**
- `GET /users/@me` — token valid, bot identity
- `GET /users/@me/guilds` — lists guilds the bot is in
- `GET /guilds/{id}/channels` — bot's access to guild channels (proves membership)
- `GET /guilds/{id}/members/{bot_id}` — member object, pending: false

## Scripts (in profile `scripts/`)

- `discord_leave_guild_lib.py` — **THE ONE TO USE.** discord.py client,
  `--list` or `<guild_id>` to leave. Verified working.
- `discord_leave_guild.py` — raw REST version. `--check` is a useful
  diagnostic; `--leave` will 403 today but keep it in case Discord re-enables
  self-leave. Do NOT treat empty body as success — check HTTP code.

## Pitfalls
- An empty curl body is NOT proof of success — check `-w HTTP:%{http_code}`.
  403 = permission denied even with empty-ish body.
- Discord caches `/users/@me/guilds` — a guild may still appear briefly after
  removal; wait ~30-60s and re-check via gateway before concluding.
- Don't regenerate the bot token to "fix" this — breaks the whole integration
  and wouldn't help anyway.
- The gateway client needs `intents.guilds = True` or the guild cache is empty
  and `get_guild()` returns None.

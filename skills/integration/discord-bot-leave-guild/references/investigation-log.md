# Leave-Guild Investigation Log (8/11/26)

Full forensic trail from removing the Vesper bot from Cultis Anarchia
(guild 1387534334067736699) after the move to the private "R and V" server.

## What FAILED (raw REST)
```
DELETE /guilds/{guild.id}  →  403 {"message": "Missing Access", "code": 50001}
```
- Tested on API versions **v10, v9, v8** — identical 403.
- Official Guild resource docs (`docs.discord.com/developers/resources/guild.md`,
  1,649 lines) no longer list ANY "Leave Guild" / `DELETE /guilds/{guild.id}`
  route — grep for "leave" = 0 hits. The endpoint was removed from the docs.
- Verified the token was healthy and membership real: `GET /users/@me`,
  `GET /users/@me/guilds` (both servers listed), `GET /guilds/{id}/channels`
  (channels returned = real membership), `GET /guilds/{id}/members/{bot_id}`
  (member object, `pending: false`). Not a scope, token, or config problem.

## What WORKED (discord.py library method)
```python
intents = discord.Intents.default()
intents.guilds = True                      # REQUIRED or guild cache is empty
client = discord.Client(intents=intents)
# in on_ready:
guild = client.get_guild(1387534334067736699)
await guild.leave()                        # no exception raised
```
- Result: `LEAVE OK — no exception raised`. Reconnected a fresh client and the
  gateway confirmed only R and V remained.
- Why: the library's leave goes through the client's established session path,
  not the bare REST DELETE that Discord locked down.
- Script: `discord_leave_guild_lib.py` in the profile scripts dir.

## Google's "guild leave script" vs reality
Public scripts (discord.py `guild.leave()`, discord.js `guild.leave()`) do
exist and DO work — the earlier confusion was using a raw `curl DELETE` which
is a different, dead path. The library methods are the correct tool.

## Traps
- Empty curl body ≠ success. The first script printed "✅ Left" on an empty
  response body; the real HTTP code was 403. Always check `-w HTTP:%{http_code}`.
- `/users/@me/guilds` is cached — may show the guild for 30-60s after leaving.
  Verify via a fresh gateway client instead.
- Don't regenerate the bot token to "fix" self-leave — breaks the whole
  integration and wouldn't help anyway.

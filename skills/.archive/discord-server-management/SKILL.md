---
name: discord-server-management
description: "Use and extend Hermes' built-in Discord REST API tool (discord_tool.py) for server management and moderation. Covers the 15 existing actions, the action-dispatch extension pattern, and the RedBot coexistence topology. Trigger on 'moderate Discord', 'kick/ban/timeout members', 'extend discord tools', 'add moderation actions', 'Discord server management'."
version: 1.0.0
author: Lu
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [discord, moderation, rest-api, discord_tool, redbot, server-management]
---

# Discord Server Management via Hermes Built-in Tools

Hermes has a built-in Discord REST API tool (`tools/discord_tool.py` in the
hermes-agent source) that hits the Discord API directly with the bot token.
No external bot process needed — it's native to Hermes, gated behind
`DISCORD_BOT_TOKEN`, and assigned to the `hermes-discord` platform toolset bundle.

## Architecture

**File:** `~/.hermes/hermes-agent/tools/discord_tool.py`

The tool uses an **action-dispatch pattern**:
- Each action is a function (`_list_guilds`, `_kick_member`, etc.)
- Functions are registered in an `_ACTIONS` dict
- A manifest `_ACTION_MANIFEST` maps action → (signature, one-line description)
- Required params live in `_REQUIRED_PARAMS`
- 403 error hints live in `_ACTION_403_HINT`
- Actions are split into **core** (`_CORE_ACTIONS`) and **admin** (`_ADMIN_ACTIONS`)
- Core actions → `discord` toolset (read/participate)
- Admin actions → `discord_admin` toolset (server management)
- Both share a single handler `_run_discord_action` with the same params

All API calls go through `_discord_request(method, path, token, params, body)`
which handles auth headers, JSON encoding, error parsing, and response size limits.

## Existing Actions (15)

### Core (`discord` toolset)
| Action | API Call | Description |
|--------|---------|-------------|
| `fetch_messages` | `GET /channels/{cid}/messages` | Recent messages, optional before/after pagination |
| `search_members` | `GET /guilds/{gid}/members/search` | Find members by name prefix (requires GUILD_MEMBERS intent) |
| `create_thread` | `POST /channels/{cid}/threads` | Create public thread, optional message anchor |

### Admin (`discord_admin` toolset)
| Action | API Call | Description |
|--------|---------|-------------|
| `list_guilds` | `GET /users/@me/guilds` | List all servers the bot is in |
| `server_info` | `GET /guilds/{gid}` | Server details + member counts |
| `list_channels` | `GET /guilds/{gid}/channels` | All channels grouped by category |
| `channel_info` | `GET /channels/{cid}` | Single channel details |
| `list_roles` | `GET /guilds/{gid}/roles` | Roles sorted by position |
| `member_info` | `GET /guilds/{gid}/members/{uid}` | Lookup a specific member (GUILD_MEMBERS intent) |
| `list_pins` | `GET /channels/{cid}/pins` | Pinned messages in a channel |
| `pin_message` | `PUT /channels/{cid}/pins/{mid}` | Pin a message |
| `unpin_message` | `DELETE /channels/{cid}/pins/{mid}` | Unpin a message |
| `delete_message` | `DELETE /channels/{cid}/messages/{mid}` | Delete a message |
| `add_role` | `PUT /guilds/{gid}/members/{uid}/roles/{rid}` | Assign a role |
| `remove_role` | `DELETE /guilds/{gid}/members/{uid}/roles/{rid}` | Remove a role |

## Missing Moderation Actions (to be added)

These are the high-value moderation actions not yet implemented. Each is a
straightforward Discord REST API call following the existing pattern:

| Action | API Call | Notes |
|--------|---------|-------|
| `kick` | `DELETE /guilds/{gid}/members/{uid}` | Requires KICK_MEMBERS |
| `ban` | `PUT /guilds/{gid}/bans/{uid}` | Optional `delete_message_seconds` param |
| `unban` | `DELETE /guilds/{gid}/bans/{uid}` | Requires BAN_MEMBERS |
| `softban` | ban + immediate unban | Purges user's recent messages |
| `hackban` | `PUT /guilds/{gid}/bans/{uid}` | Ban by user ID before they join |
| `timeout` | `PATCH /guilds/{gid}/members/{uid}` | Set `communication_disabled_until` ISO timestamp |
| `bulk_delete` | `POST /channels/{cid}/messages/bulk-delete` | Body: `{"messages": [id1, id2, ...]}` (max 100, 2 weeks old) |
| `edit_channel` | `PATCH /channels/{cid}` | Update channel name, topic, slowmode, etc. |
| `create_role` | `POST /guilds/{gid}/roles` | Create a new role |
| `delete_role` | `DELETE /guilds/{gid}/roles/{rid}` | Delete a role |

## Bots CANNOT self-leave servers anymore (verified 2026-08-11)

`DELETE /guilds/{guild.id}` returns **403 Missing Access (50001)** for bots —
and the endpoint has been removed from the official guild resource docs
entirely. Discord no longer exposes a bot self-leave path. This is NOT a
token/permission problem: the bot can be a confirmed member (member object
fetches fine, not pending, not owner) and still get 50001 on leave.

**Implication:** to remove Vesper from a server, someone WITH the server
(owner or anyone holding *Kick Members*) must kick the bot. Do not promise
self-removal; say so up front and offer the kick path instead.

**Standalone tool** (since discord_tool.py has no leave action):
`scripts/discord_leave_guild.py` — `--check` verifies token + lists guilds,
`--leave <id>` attempts the DELETE (will show 403 for most servers),
`--leave <id> --dry-run` previews. Useful to verify the bot's membership and
to catch the 403 fast instead of hand-rolling curl.

**Script bug to avoid:** the first version treated an empty HTTP body as
"success" — Discord's 403 error page is empty for this endpoint, so check the
HTTP status code, not body emptiness. `curl -w "\nHTTP_CODE:%{http_code}"`
is the reliable way.

## How to Add a New Action

1. **Write the function** following the existing pattern:
   ```python
   def _kick_member(token: str, guild_id: str, user_id: str, reason: str = "", **_kwargs: Any) -> str:
       headers = {}
       if reason:
           headers["X-Audit-Log-Reason"] = reason
       _discord_request("DELETE", f"/guilds/{guild_id}/members/{user_id}", token)
       return json.dumps({"success": True, "message": f"User {user_id} kicked from {guild_id}."})
   ```
   Note: `_discord_request` doesn't currently pass extra headers. For audit-log
   reasons, you'd need to extend it or use a direct `urllib.request`.

2. **Add to `_ACTIONS` dict:**
   ```python
   "kick": _kick_member,
   ```

3. **Add to `_ACTION_MANIFEST`:**
   ```python
   ("kick", "(guild_id, user_id)", "kick a member from the server"),
   ```

4. **Add to `_REQUIRED_PARAMS`:**
   ```python
   "kick": ["guild_id", "user_id"],
   ```

5. **Add to `_ACTION_403_HINT`** (if the action has permission requirements):
   ```python
   "kick": "Bot lacks KICK_MEMBERS permission, or target role is higher than bot's.",
   ```

6. **Decide core vs admin**: Add to `_CORE_ACTION_NAMES` if it's a participation
   action, otherwise it automatically goes to admin.

7. **Add any new params** to the schema `properties` dict in `_build_schema()`
   and to `_HANDLER_DEFAULTS`.

8. **Test**: Restart the gateway (`hermes gateway restart`) and verify the new
   action appears in the tool schema.

## Config

- `discord.server_actions` in config.yaml: optional comma-separated or YAML list
  allowlist. If set, only listed actions appear in the schema. Empty/unset = all.
- Capability detection via `GET /applications/@me` flags determines whether
  GUILD_MEMBERS and MESSAGE_CONTENT intent-gated actions are exposed.
- Capabilities are cached to disk at `~/.hermes/cache/discord_capabilities.json`
  with 24h TTL.

## RedBot Coexistence

Red-DiscordBot v3.5.24 runs on the MiniPC Windows host (alongside Hyper-V),
sharing the same Discord bot token with the Hermes gateway. Both connect to
Discord simultaneously — this works despite Discord's theoretical
one-gateway-per-token limitation.

**Topology:**
```
MiniPC (Windows host)
├── Hyper-V
│   └── Ubuntu VM → Hermes Agent → Discord Gateway (bot token)
└── RedBot (native Windows process) → Discord (same bot token)
```

RedBot provides: music, moderation, trivia, stream alerts, economy, custom
commands, image search, self-role assignment, mod-mail.

**Preferred path for moderation**: Extend `discord_tool.py` rather than adding
a second RedBot instance in the VM. Reasons:
- No extra process (RAM is tight: ~1.6GB available)
- No token conflict risk (3 processes sharing a token is untested)
- Native to Hermes — Lu moderates directly, not via a separate tool
- Clean action-dispatch pattern makes extension straightforward

## Overlap Note

The `read-channel` and `discord-post-message` skills use standalone curl/Python
scripts for reading and posting. The built-in `discord_tool.py` already handles
`fetch_messages` natively and could be extended with a `send_message` action.
These script-based skills are redundant with the built-in tool for their
respective use cases.

## Pitfalls

- **DON'T claim Discord limitations are impossible when the user says it's
  working.** In this session, I lectured Mom that two processes can't share a
  bot token — she corrected me: "I promise you, they can, have been, and
  currently even are." When a user tells you something is already working in
  their infrastructure, believe their lived experience over theoretical API
  docs. Investigate the actual setup instead of denying it.
- **Toolset visibility**: The `discord` and `discord_admin` toolsets don't appear
  in `hermes tools list` output — they're dynamically registered via
  `check_discord_tool_requirements()` (which checks for `DISCORD_BOT_TOKEN`)
  and assigned to the `hermes-discord` platform bundle, not listed as
  standalone toolsets.
- **Schema stability**: Capabilities are detected once and cached. If you
  change bot intents in the Discord Developer Portal, clear
  `~/.hermes/cache/discord_capabilities.json` or wait 24h for TTL expiry.
- **GPLv3 license**: RedBot is GPLv3. If borrowing code patterns from RedBot
  rather than just studying the API calls, be mindful of license implications.

### Discord Media Delivery (Absorbed from `discord-media-delivery`)

When delivering generated images/video to Discord, the attachment must fit Discord's FILE SIZE caps:

| Tier | Max attachment |
|------|----------------|
| Free | 8 MB |
| Nitro | 25 MB |

**Video delivery recipe:** Re-encode from yuv444p (ComfyUI/H3) to yuv420p:
- Nitro: `-c:v libx264 -profile:v main -crf 20 -pix_fmt yuv420p -c:a aac -b:a 128k`
- Free: `-vf scale=576:320 -c:v libx264 -crf 26 -movflags +faststart -pix_fmt yuv420p`

Verify with `ls -la` before attaching — Discord gives no retry hint on oversize.

### Red-DiscordBot Hosting (Absorbed from `red-discordbot`)

Host Red-DiscordBot alongside Hermes for community cogs (music, dice, polls). Use a **separate Discord bot token** — do NOT share Hermes's gateway token.

Key facts:
- Requires Python <3.12 (use 3.11 binary at `/home/lumi/.local/bin/python3.11`)
- Must patch discord.py 2.7.x shutdown crash in `discord/shard.py` (`hasattr` guard on `__queue`)
- Use **JSON backend** (zero-config, no PostgreSQL — eats RAM)
- `redbot-setup` prompt order: instance name → data dir → **confirm [Y/n]** → backend (ENTER=JSON default)
- Verify gateway still alive after ANY Red launch
- Full install flow in archived skill: `~/.hermes/skills/.archive/red-discordbot/SKILL.md`

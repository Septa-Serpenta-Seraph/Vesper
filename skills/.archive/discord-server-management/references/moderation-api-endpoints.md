# Discord Moderation REST API Endpoints

Reference for the moderation actions to add to `discord_tool.py`.
All endpoints use the bot token via `Authorization: Bot {token}` header.
Base URL: `https://discord.com/api/v10`

## Kick

```
DELETE /guilds/{guild_id}/members/{user_id}
```
- Requires `KICK_MEMBERS` permission
- Optional `X-Audit-Log-Reason` header for audit log entry
- Returns 204 No Content on success

## Ban

```
PUT /guilds/{guild_id}/bans/{user_id}
Body: {"delete_message_seconds": 604800}  (optional, max 604800 = 7 days)
```
- Requires `BAN_MEMBERS` permission
- `delete_message_seconds` deletes the user's messages in last N seconds
- Optional `X-Audit-Log-Reason` header
- Returns 204 No Content on success

## Unban

```
DELETE /guilds/{guild_id}/bans/{user_id}
```
- Requires `BAN_MEMBERS` permission
- Returns 204 No Content on success

## Softban (ban + immediate unban)

Not a single API call — implement as:
1. `PUT /guilds/{gid}/bans/{uid}` with `delete_message_seconds` to purge messages
2. `DELETE /guilds/{gid}/bans/{uid}` to unban immediately
- Effect: removes user from server and deletes their recent messages
- User can rejoin immediately

## Hackban (ban by ID, user not in server)

Same as regular ban:
```
PUT /guilds/{guild_id}/bans/{user_id}
```
- Works even if the user is not currently a member
- Useful for preemptive bans

## Timeout (communication disable)

```
PATCH /guilds/{guild_id}/members/{user_id}
Body: {"communication_disabled_until": "2026-07-12T15:00:00.000+00:00"}
```
- Requires `MODERATE_MEMBERS` permission
- Set `communication_disabled_until` to null to remove timeout
- Max duration: 28 days
- ISO 8601 timestamp format

## Bulk Delete

```
POST /channels/{channel_id}/messages/bulk-delete
Body: {"messages": ["message_id_1", "message_id_2", ...]}
```
- Requires `MANAGE_MESSAGES` permission
- Max 100 messages per request
- Messages must be newer than 2 weeks (14 days)
- Returns 204 No Content on success
- Cannot delete messages from different channels in one request

## Edit Channel

```
PATCH /channels/{channel_id}
Body: {"name": "new-name", "topic": "new topic", "rate_limit_per_user": 10}
```
- Requires `MANAGE_CHANNELS` permission
- Returns updated channel object

## Create Role

```
POST /guilds/{guild_id}/roles
Body: {"name": "Role Name", "color": 0xFF0000, "permissions": "0", "hoist": false, "mentionable": false}
```
- Requires `MANAGE_ROLES` permission
- `color` is integer RGB, `permissions` is string of permission bitfield
- Returns created role object

## Delete Role

```
DELETE /guilds/{guild_id}/roles/{role_id}
```
- Requires `MANAGE_ROLES` permission
- Returns 204 No Content on success

## Audit Log Reason Header

For all moderation actions, Discord supports an audit log reason:
```
X-Audit-Log-Reason: Reason text here (max 512 chars)
```

**Note:** The current `_discord_request` helper in `discord_tool.py` does NOT
accept extra headers. To add audit-log reasons, either:
1. Extend `_discord_request` with an optional `extra_headers` parameter
2. Add the header in the action function before calling `_discord_request`

Option 1 is cleaner — modify the signature:
```python
def _discord_request(
    method, path, token, params=None, body=None, timeout=15,
    extra_headers=None,
):
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "Hermes-Agent (...)",
    }
    if extra_headers:
        headers.update(extra_headers)
    # ... rest unchanged
```

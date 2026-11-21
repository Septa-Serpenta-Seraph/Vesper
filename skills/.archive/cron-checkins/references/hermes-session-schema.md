# Hermes Session Store Schema (for context readers)

The conversation history lives in a SQLite database, NOT a JSON memory file.

## Path
`~/.hermes/profiles/<profile>/state.db`
(this profile: `/home/lumi/.hermes/profiles/vesper/state.db`)

## Key tables
- `messages`: `id INTEGER, session_id TEXT, role TEXT, content TEXT, timestamp REAL, ...`
  - `timestamp` is **epoch seconds, UTC**.
  - `role` ∈ `user` | `assistant` | `tool` | `system`.
- `sessions`: `id TEXT, source TEXT, user_id TEXT, chat_id TEXT, chat_type TEXT,
  display_name TEXT, message_count INTEGER, started_at REAL, ended_at REAL, ...`
  - `source` = `discord` | `tui` | `cli` | `subagent`.
  - `chat_id` = Discord channel id (for DMs it's the DM channel id).
  - `chat_type` = `dm` | `group`.

## Finding the live DM session
```sql
SELECT id FROM sessions
WHERE chat_id = '<DISCORD_DM_CHAT_ID>'
ORDER BY (SELECT MAX(timestamp) FROM messages m WHERE m.session_id = sessions.id) DESC
LIMIT 1;
```

## Gaps
```sql
SELECT MAX(timestamp) FROM messages WHERE session_id=? AND role='assistant';  -- my last msg
SELECT MAX(timestamp) FROM messages WHERE session_id=? AND role='user';       -- their last msg
```
Convert `now_utc.timestamp() - max_ts` to minutes.

## Timezone
The host is `Etc/UTC`. To show the user's local time:
```python
from zoneinfo import ZoneInfo
now_mt = datetime.now(ZoneInfo("America/Denver"))   # MT, DST-aware
```
Fallback if `zoneinfo` missing:
`datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-6)))`.

## CLI gotcha
No `sqlite3` binary is guaranteed; use `python3` with the `sqlite3` stdlib module
(heredoc in terminal). The `execute_code` tool may be blocked by `cron_mode`
approval in some profiles — prefer terminal heredocs for inspection.

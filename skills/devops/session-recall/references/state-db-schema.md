# state.db Schema and Diagnostic Queries

## Database Location

`~/.hermes/state.db` — SQLite, contains sessions and messages tables with FTS5 full-text search.

## Sessions Table

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Session ID, format: `YYYYMMDD_HHMMSS_<8hex>` or `cron_<cronid>_<YYYYMMDD>_<HHMMSS>` |
| source | TEXT | "discord", "cron", "telegram", etc. |
| user_id | TEXT | Platform user ID |
| model | TEXT | Model name used |
| started_at | REAL | Unix timestamp (seconds, UTC) |
| ended_at | REAL | Unix timestamp (seconds, UTC) |
| end_reason | TEXT | How session ended |
| message_count | INTEGER | Total messages in session |
| tool_call_count | INTEGER | Tool calls made |
| title | TEXT | Auto-generated session title |
| archived | INTEGER | 0 or 1 |

## Messages Table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Message ID (auto-increment, global across sessions) |
| session_id | TEXT (FK) | References sessions.id |
| role | TEXT | "user", "assistant", "tool", "session_meta" |
| content | TEXT | Message text content |
| tool_call_id | TEXT | If tool call, the call ID |
| tool_calls | TEXT | JSON of tool call requests |
| tool_name | TEXT | Name of tool invoked |
| timestamp | REAL | Unix timestamp (seconds, UTC) |
| token_count | INTEGER | Tokens in this message |
| finish_reason | TEXT | LLM finish reason |
| platform_message_id | TEXT | Discord/Telegram message ID |
| observed | INTEGER | 0 or 1 |
| active | INTEGER | 0 or 1 |

## Common Diagnostic Queries

### Find all sessions in a time range (by Mountain Time)

```python
import sqlite3, datetime
from datetime import timezone, timedelta

MT = timezone(timedelta(hours=-7))
conn = sqlite3.connect('/home/lumi/.hermes/state.db')
c = conn.cursor()

# Convert "July 9, 7:00 AM MT" to unix timestamp
target_time = datetime.datetime(2026, 7, 9, 7, 0, tzinfo=MT)
unix_ts = target_time.timestamp()

c.execute('''
    SELECT id, title, source, started_at, message_count
    FROM sessions 
    WHERE started_at > ? AND started_at < ?
    ORDER BY started_at ASC
''', (unix_ts - 3600, unix_ts + 7200))
```

### Search message content directly (bypassing FTS5)

```python
c.execute('''
    SELECT m.id, m.session_id, m.role, m.timestamp, substr(m.content, 1, 200)
    FROM messages m
    WHERE m.content LIKE '%keyword%'
    AND m.session_id NOT LIKE 'cron_%'
    ORDER BY m.timestamp DESC
    LIMIT 20
''')
```

### Get all messages from a specific session

```python
c.execute('''
    SELECT id, role, timestamp, substr(content, 1, 150)
    FROM messages 
    WHERE session_id = ?
    ORDER BY timestamp ASC
''', (session_id,))
```

### Check for gaps in conversation (non-cron messages in a time window)

```python
c.execute('''
    SELECT id, session_id, role, timestamp, substr(content, 1, 150)
    FROM messages
    WHERE timestamp > ? AND timestamp < ?
    AND session_id NOT LIKE 'cron_%'
    ORDER BY timestamp ASC
''', (start_ts, end_ts))
```

## sessions.json (Active Session Registry)

Located at `~/.hermes/sessions/sessions.json`. Maps session keys (platform:chat_type:chat_id:user_id) to active session metadata. Useful for understanding which session is currently active for a given Discord channel/user combination.

Key fields: `session_id`, `created_at`, `updated_at`, `expiry_finalized`, `is_fresh_reset`, `was_auto_reset`, `auto_reset_reason`.

## Timezone Reference

All timestamps in state.db are **Unix epoch (UTC)**. The user (Dad/Tyler) is in **Mountain Time (UTC-7)**.

- UTC 13:00 = 06:00 AM MT
- UTC 18:00 = 11:00 AM MT  
- UTC 20:00 = 13:00 (1:00 PM) MT
- UTC 00:00 (next day) = 17:00 (5:00 PM) MT
- UTC 03:00 (next day) = 20:00 (8:00 PM) MT

## Incident Log

### 2026-07-09: UTC Timestamp Misread

**What happened**: User referenced "our conversation this morning at 7:50." session_search returned a result labeled "July 08, 2026 at 01:49 PM." Lu interpreted this as an afternoon session and told the user no morning conversation existed. The session WAS the morning conversation — 01:49 PM UTC = 06:49 AM MT.

**Root cause**: session_search displays UTC timestamps in human-readable format without labeling them as UTC. No timezone indicator in the output.

**Fix**: Always convert UTC timestamps to Mountain Time before drawing conclusions about when a session occurred relative to user references like "this morning" or "this afternoon."

**Lesson**: If a user says "this morning" and search results show times that don't match, the results are likely in UTC. Convert before panicking.

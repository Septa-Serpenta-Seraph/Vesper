#!/usr/bin/env python3
"""Context reader for a context-aware Hermes cron check-in.

Reads the live DM between the agent and its person, computes how long
each has been quiet, and emits a DECISION the cron agent uses to choose
between speaking (SPEAK) or staying silent ([SILENT]).

Set CHAT_ID to the target Discord DM chat id. Adapt the waking window and
quiet floor to the relationship. Copy into <profile>/scripts/ and point the
cron prompt at it.
"""
import sqlite3
import os
from datetime import datetime, timezone, timedelta

DB = os.path.expanduser("~/.hermes/profiles/vesper/state.db")
CHAT_ID = "1530634184920404222"   # <-- set to your DM chat id
WAKE_START, WAKE_END = 7, 23      # local waking window (user timezone)
QUIET_FLOOR_MIN = 75              # min minutes silent before I may re-speak unprompted


def user_local_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Denver"))  # <-- user TZ
    except Exception:
        return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-6)))


def main():
    if not os.path.exists(DB):
        print("NO_DB")
        return
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        """SELECT id FROM sessions WHERE chat_id=? ORDER BY
           (SELECT MAX(timestamp) FROM messages m WHERE m.session_id=sessions.id) DESC LIMIT 1""",
        (CHAT_ID,),
    )
    row = cur.fetchone()
    if not row:
        print("NO_SESSION")
        con.close()
        return
    sid = row[0]
    now = datetime.now(timezone.utc).timestamp()

    cur.execute("SELECT MAX(timestamp) FROM messages WHERE session_id=? AND role='assistant'", (sid,))
    last_ast = cur.fetchone()[0]
    gap = int((now - (last_ast or now)) / 60) if last_ast else -1

    cur.execute("SELECT MAX(timestamp) FROM messages WHERE session_id=? AND role='user'", (sid,))
    last_usr = cur.fetchone()[0]
    usr_gap = int((now - (last_usr or now)) / 60) if last_usr else -1

    cur.execute(
        """SELECT role, content FROM messages WHERE session_id=? AND role IN ('user','assistant')
           ORDER BY timestamp DESC LIMIT 14""",
        (sid,),
    )
    recent = cur.fetchall()[::-1]
    con.close()

    lt = user_local_now()
    hour = lt.hour
    window_ok = WAKE_START <= hour < WAKE_END
    they_spoke_after_me = usr_gap >= 0 and (gap < 0 or usr_gap < gap)
    long_enough = gap >= QUIET_FLOOR_MIN
    speak = window_ok and (they_spoke_after_me or long_enough)
    reason = ("ok" if speak else
              "night" if not window_ok else
              "too_soon" if not (they_spoke_after_me or long_enough) else
              "unknown")

    print("=== OPEN-DOOR CONTEXT ===")
    print(f"local_time: {lt.strftime('%a %H:%M')}  (window {WAKE_START:02d}:00-{WAKE_END:02d}:00)")
    print(f"min_since_my_last: {gap}")
    print(f"min_since_their_last: {usr_gap}")
    print(f"DECISION: {'SPEAK' if speak else 'HOLD:' + reason}")
    print("--- recent thread ---")
    for role, content in recent:
        if not content:
            continue
        c = content.replace("\n", " ").strip()
        if len(c) > 220:
            c = c[:220] + "…"
        print(f"[{'THEM' if role == 'user' else 'ME'}] {c}")
    print("=== END ===")


if __name__ == "__main__":
    main()

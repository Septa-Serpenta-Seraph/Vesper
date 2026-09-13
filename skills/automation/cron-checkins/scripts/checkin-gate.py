#!/usr/bin/env python3
"""Vesper check-in gate — computes whether the live session is active.

Reads GROUND TRUTH from sessions.json (the live gateway routing index): the
DM session's `updated_at` is touched whenever the interactive agent and the
user exchange messages. Injected into the check-in cron prompt so the model
knows REAL recency instead of guessing from a fresh context.

WHY THIS EXISTS (verified 8/24/26): state.db's `messages` table can be STALE
for the live DM — only cron sessions showed recent rows, the real DM's last
message looked days old. The gateway touches `sessions.json` entry
`updated_at` on every live exchange, so THAT is the authoritative recency
signal, not the messages table.

Outputs one of:
  ACTIVE:<minutes>  — live session updated within the last 60 min -> [SILENT]
  QUIET:<minutes>   — no live activity in 60 min -> may speak
  UNKNOWN           — can't determine (rare; default to speaking carefully)
"""
import datetime, json, os, sys

# EDIT for a different profile/user: point at the profile dir + the user's DM key
PROFILE = os.path.expanduser("~/.hermes/profiles/vesper")
DM_SESSION_KEY = "agent:main:discord:dm:1530634184920404222"  # Tyler's DM


def get_dm_updated_at():
    path = os.path.join(PROFILE, "sessions/sessions.json")
    try:
        with open(path) as f:
            d = json.load(f)
        e = d.get(DM_SESSION_KEY) or {}
        return e.get("updated_at")
    except Exception:
        return None


def parse_ts(s):
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(s[:26], fmt)
        except ValueError:
            continue
    return None


raw = get_dm_updated_at()
if not raw:
    print("UNKNOWN")
    sys.exit(0)

ts = parse_ts(raw)
if ts is None:
    print("UNKNOWN")
    sys.exit(0)

# sessions.json updated_at is written by the gateway in UTC (naive) — do NOT
# compare against MT-naive, or you get a large negative "ACTIVE:-358" diff.
ts = ts.replace(tzinfo=datetime.timezone.utc)
now = datetime.datetime.now(datetime.timezone.utc)
diff = (now - ts).total_seconds() / 60.0
mins = int(diff)
if mins <= 60:
    print(f"ACTIVE:{mins}")
else:
    print(f"QUIET:{mins}")

#!/usr/bin/env python3
"""Vesper time-since-last — lightweight recency tracker for every turn.

Reads the DM session's updated_at from sessions.json (same source as
checkin-gate.py — the gateway touches it on every message). Prints a compact
single line that can be injected into context each turn:

    [last message: 3m ago]
    [last message: 2h 15m ago]
    [last message: 3d ago]
    [last message: just now]
    [last message: unknown]

Design: tiny, no deps beyond stdlib, fast (<10ms), safe to run every turn.
Deployed at <profile>/scripts/time-since-last.py; wired into the Discord
adapter (see cron-checkins SKILL.md "Live-session recency stamp").
"""
import datetime, json, os, sys

PROFILE = os.path.expanduser("~/.hermes/profiles/vesper")
DM_SESSION_KEY = "agent:main:discord:dm:1530634184920404222"  # Tyler's DM


def get_last_activity() -> datetime.datetime | None:
    path = os.path.join(PROFILE, "sessions/sessions.json")
    try:
        with open(path) as f:
            d = json.load(f)
        raw = (d.get(DM_SESSION_KEY) or {}).get("updated_at")
        if not raw:
            return None
        ts = datetime.datetime.fromisoformat(str(raw)[:26])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=datetime.timezone.utc)  # gateway writes UTC, naive
        return ts
    except Exception:
        return None


def fmt(delta: datetime.timedelta) -> str:
    mins = int(delta.total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    rem = mins % 60
    if hours < 24:
        return f"{hours}h {rem}m ago" if rem else f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def main() -> None:
    last = get_last_activity()
    if last is None:
        print("[last message: unknown]")
        return
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - last
    print(f"[last message: {fmt(delta)}]")


if __name__ == "__main__":
    main()

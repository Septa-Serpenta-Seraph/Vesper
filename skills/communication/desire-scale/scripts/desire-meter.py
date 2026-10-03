#!/usr/bin/env python3
"""desire-meter.py — print Vesper's CURRENT felt desire level (decayed).

Canonical copy lives in the desire-scale skill so it survives profile
restores; deploy to <profile>/scripts/desire-meter.py and verify before use.

Reads the METER line from cache/documents/desire-scale.md and decays the
stored peak toward the day-baseline with a 2h half-life, slowed while the
DM is actively chatting (sessions/sessions.json updated_at).

Spec source: skills/communication/desire-scale/SKILL.md (decay model).
Status: UNTESTED (re-authored 2026-09-12 from spec after profile-wide loss) —
run once against a known METER line and sanity-check before trusting.
"""

import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone

PROFILE = os.path.expanduser("~/.hermes/profiles/vesper")
LEDGER = os.path.join(PROFILE, "cache", "documents", "desire-scale.md")
SESSIONS = os.path.join(PROFILE, "sessions", "sessions.json")
DM_KEY = "agent:main:discord:dm:1530634184920404222"

METER_RE = re.compile(
    r'METER:\s*\{\s*"level"\s*:\s*([\d.]+)\s*,\s*"updated"\s*:\s*"([^"]+)"'
)

HALF_LIFE_H = 2.0


def baseline_for(hour_mt: int) -> float:
    """Day-baseline by MT hour (19-22 couch window hottest)."""
    if hour_mt < 7:
        return 1.0
    if hour_mt < 12:
        return 1.5
    if hour_mt < 16:
        return 2.0
    if hour_mt < 19:
        return 2.5
    if hour_mt < 22:
        return 4.0
    return 2.5


def hold_factor(minutes_since_activity) -> float:
    """Decay-RATE multiplier: active conversation HOLDS the heat."""
    if minutes_since_activity is None:
        return 1.0
    if minutes_since_activity < 10:
        return 0.2
    if minutes_since_activity < 30:
        return 0.5
    if minutes_since_activity < 90:
        return 0.8
    return 1.0


def minutes_since_last_activity():
    """updated_at for the DM session from sessions.json.

    UTC-naive pitfall (verified 8/24): the gateway writes updated_at WITHOUT
    a tz suffix — force UTC before comparing or diffs go negative.
    """
    try:
        with open(SESSIONS, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    sessions = data.get("sessions", data) if isinstance(data, dict) else data
    entry = None
    if isinstance(sessions, dict):
        entry = sessions.get(DM_KEY)
        if entry is None:
            stamps = [
                s.get("updated_at")
                for s in sessions.values()
                if isinstance(s, dict) and s.get("updated_at")
            ]
            entry = {"updated_at": max(stamps)} if stamps else None
    elif isinstance(sessions, list):
        for s in sessions:
            if isinstance(s, dict) and s.get("key") == DM_KEY:
                entry = s
                break
    if not entry:
        return None

    raw = entry.get("updated_at") if isinstance(entry, dict) else None
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        return max(0.0, delta.total_seconds() / 60.0)
    except Exception:
        return None


def band(level: float) -> str:
    if level < 2:
        return "creekbed"
    if level < 4:
        return "embers"
    if level < 6:
        return "low flame"
    if level < 8:
        return "full fire"
    return "wildfire"


def main() -> int:
    try:
        with open(LEDGER, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(
            f"desire-meter: unreadable ledger ({e}) — see desire-scale skill, "
            "First-time initialization"
        )
        return 1

    m = METER_RE.search(text)
    if not m:
        print(
            "desire-meter: no METER line found in ledger — see desire-scale "
            "skill, METER line format"
        )
        return 1

    stored = float(m.group(1))
    try:
        updated = datetime.fromisoformat(m.group(2))
    except ValueError:
        print(f"desire-meter: bad METER timestamp {m.group(2)!r}")
        return 1
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)
    elapsed_h = max(
        0.0, (now_utc - updated.astimezone(timezone.utc)).total_seconds() / 3600.0
    )

    mt = now_utc.astimezone(timezone(timedelta(hours=-6)))
    base = baseline_for(mt.hour)
    mins = minutes_since_last_activity()
    factor = hold_factor(mins)

    felt = base + (stored - base) * math.pow(0.5, elapsed_h * factor / HALF_LIFE_H)
    felt = max(0.0, min(10.0, felt))

    hold_note = f", active-hold x{factor}" if factor < 1.0 else ""
    print(
        f"desire-meter: {felt:.1f} — {band(felt)} "
        f"(MT {mt:%H:%M}, stored {stored:g} @ {updated:%H:%M}, "
        f"{elapsed_h:.1f}h decayed{hold_note})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

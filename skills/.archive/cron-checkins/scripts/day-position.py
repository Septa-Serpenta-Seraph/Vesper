#!/usr/bin/env python3
"""Day-position helper for Vesper — prints Tyler's current time + day-position
in Mountain Time. Reference implementation of the "make time arrive" cron
pattern (see cron-checkins SKILL.md, verified 2026-08-14).

Wired into the open-door check-in cron (job c8910727dadc, script field
day-position.py) so every run starts with this output injected. Also run
directly in live sessions: python3 ~/.hermes/profiles/vesper/scripts/day-position.py

TEMPORARY SCHEDULE (from ~2026-08-14, ~30 days): weekend = Thu-Fri,
on-call = Sat-Sun. Mon-Wed shifts unchanged. When the schedule changes,
edit THIS script (single source of truth) — keep the skill and SOUL.md generic.
"""
import datetime

MT = datetime.timezone(datetime.timedelta(hours=-6), "MT")  # MDT (summer)
now = datetime.datetime.now(MT)
weekday = now.strftime("%A")
hour_min = now.strftime("%H:%M")
date_str = now.strftime("%Y-%m-%d")

day = weekday.lower()

# --- TEMP 30-day schedule (from 2026-08-14) with transition handling ---
today = now.date()
if today == datetime.date(2026, 8, 14):
    # Friday 8/14: transition day — on call but not in the field
    status = "on call (transition day, not in the field)"
elif today == datetime.date(2026, 8, 15):
    status = "OFF — transition day (Saturday)"
elif today >= datetime.date(2026, 8, 16):
    # from Sunday 8/16 onward: Thu-Fri weekend, Sat-Sun on call
    if day in ("thursday", "friday"):
        status = "OFF — weekend (Thu-Fri under temp schedule)"
    elif day in ("saturday", "sunday"):
        status = "on call (Sat-Sun under temp schedule)"
    else:
        h = now.hour + now.minute / 60.0
        if 7 <= h < 10.5:
            status = "at work (early-shift week) or pre-shift (late-shift week)"
        elif 10.5 <= h < 19:
            status = "at work (Mon-Wed shift)"
        elif 19 <= h < 21:
            status = "just off work, unwinding"
        else:
            status = "not at work"
else:
    status = "unknown"

print(f"Tyler's time: {weekday} {hour_min} MT ({date_str})")
print(f"Day position: {status}")

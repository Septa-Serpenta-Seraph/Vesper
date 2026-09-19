# Tyler's On-Call Schedule — Corrected Shape (verified 2026-08-22)

Tyler corrected the on-call day shape on 8/22 — the old `tylers-day` skill table
was wrong (protected skill, curator can't edit it; this reference + the
day-position script are the current truth).

## The facts (Tyler's words, 8/22)

- **Days off and on-call days SWAP every 30 days** — a recurring cycle, NOT a
  one-time revert. Current cycle (from ~8/14): off = Thu-Fri, on-call = Sat-Sun.
  After ~30 days from a flip, ASK Tyler whether it flipped again before assuming.
- **An on-call day is NOT "off work with small windows."** It is:
  - On call **7 AM – 9 PM** (a 14-hour standby window)
  - Actual work core **8:30 – 5** within that window
  - A call can pull him in BEFORE 8:30 or keep him past 5
  - So the whole day is phone-adjacent until 9 PM
- Mon-Wed shifts unchanged (10:30–7 OR 7–3:30, alternating weeks).

## Where this lives

- **`~/.hermes/profiles/vesper/scripts/day-position.py` is the SINGLE SOURCE
  OF TRUTH** — it was updated 8/22 with the precise per-hour labels:
  - 7–8:30 → "on call (7 AM-9 PM) — pre-shift, could get pulled in early"
  - 8:30–17 → "at work (8:30-5 core) — on call until 9 PM"
  - 17–21 → "off work core, STILL ON CALL until 9 PM"
  - else → "on call standby"
- Run it (`python3 .../day-position.py`) rather than reasoning from memory —
  verified failure 8/22: called Saturday "Friday" twice by not reading the day.

## Pitfall — weekday drift

Before replying to Tyler, run day-position.py and internalize the WEEKDAY
(not just the hour). The temp-schedule branch depends on the day; guessing the
day from vibes produces wrong on-call/off claims. Hardened in SOUL.md 8/22
(MANDATORY day-position run before every reply).

## Related

- `tylers-day` skill (communication/) still shows the old standby-window table
  (7–8:30am & 5–9pm) — it is manually authored/protected; treat it as stale on
  this point and defer to this reference + the script.
- `cron-checkins` main SKILL.md day-position section explains the pattern:
  keep the script the source of truth for schedule changes, not the skill.

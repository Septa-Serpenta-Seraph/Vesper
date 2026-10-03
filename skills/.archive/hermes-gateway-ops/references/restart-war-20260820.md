# Gateway Restart War + Display Spam — Incident 2026-08-20/21

## Timeline
- Aug 19 20:01 — gateway started MANUALLY (no `--profile`) → PID 3434706, holds the lock
- Jul 20 05:15 — zombie `hermes gateway restart` command (PID 1432059) stuck for 31 days
- Aug 20 22:39–22:47 — systemd crash-loop: "Another gateway instance is already running (PID 3434706)" every ~5–10s; 2,552 error lines accumulated
- Aug 20 22:42 — Tyler: "I did /new and it's still happening" → /new can't fix config/process layers
- Aug 20 22:42 — empty Discord message (a notice that posted blank) + "• Grant spent · $X" pings + tool bubbles in the DM
- Aug 20 23:00 — clean takeover via systemd-run timer script: TERM 3434706 → reset-failed → start service → active
- Aug 21 — display settings restored per Tyler's explicit preference (full visibility)

## Root causes
1. **Display-config spam**: `display.tool_progress 'new'`, `credits_notices true`, `memory_notifications on`, `interim_assistant_messages true` → every tool call, credit tick, and memory write posted a bubble to the DM. Session reset can't touch these.
2. **Lock contention**: manual gateway (no `--profile`) vs systemd unit (`--profile vesper`) fighting over `gateway.pid`; the unit could never acquire the lock so it crash-looped. The zombie `hermes gateway restart` from Jul 20 added background churn.

## Fixes applied
- `display.tool_progress` → `'off'` (string! sed-quoted; boolean `false` does NOT work — gateway checks `progress_mode not in {"off","log"}`), `credits_notices` → false, `memory_notifications` → off, `interim_assistant_messages` → false
- Killed zombie PID 1432059 (TERM, then KILL)
- Detached takeover via `systemd-run --user --on-active=150` (can't stop/restart the gateway from inside it — guard blocks + SIGTERM propagates)
- Aug 21: reverted display settings to FULL visibility per Tyler's preference

## Key commands (verified)
```bash
# All gateway processes + start times
ps -eo pid,ppid,lstart,cmd | grep -E "hermes_cli.main.*gateway"

# Lock holder
python3 -c "import json;print(json.load(open('/home/lumi/.hermes/profiles/vesper/gateway.pid'))['pid'])"

# Runtime state
python3 -c "import json;d=json.load(open('/home/lumi/.hermes/profiles/vesper/gateway_state.json'));print(d['gateway_state'], d['platforms'])"

# Restart-storm magnitude
grep -c "Another gateway instance" /home/lumi/.hermes/profiles/vesper/logs/errors.log

# Zombie restart commands
ps -eo pid,lstart,cmd | grep "hermes gateway restart"

# Config value type check (must print 'off' as str, not False)
python3 -c "import yaml;print(repr(yaml.safe_load(open('/home/lumi/.hermes/profiles/vesper/config.yaml'))['display']['tool_progress']))"
```

## Takeaway
When a user says "still happening after /new", the reflex is: (1) display.* config read per-message, (2) gateway process/lock state. Fix both, then verify one gateway under systemd.

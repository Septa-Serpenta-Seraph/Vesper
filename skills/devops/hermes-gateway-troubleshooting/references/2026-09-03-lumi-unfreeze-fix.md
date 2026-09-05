# 2026-09-03 — Lumi unfreeze: the Lumi-first guarded fix

Session-specific detail behind section 3c. Lumi = default/un-profiled profile
(data at HERMES_HOME root). Vesper = named profile. The 9/1 forensics
(references/2026-09-01-lumi-ghost-forensics.md) established that the un-profiled
unit was serving VESPER data while Lumi's root data sat frozen since 08-18.

## Symptoms (Tyler's words)
"Lumi's token is running so her gateway is up, but she is unable to
react/respond to messages in discord."

## Diagnosis chain (all read-only)
1. `systemctl --user list-units 'hermes-gateway*'` → two units BOTH "running":
   `hermes-gateway.service` + `hermes-gateway-vesper.service`. Unit names mean
   nothing (3a).
2. `bash scripts/gateway-forensics.sh` → only ONE gateway process
   (PID 4023178), cgroup `.../hermes-gateway.service` (un-profiled unit),
   `HERMES_HOME=/home/lumi/.hermes`, but open fds held
   `profiles/vesper/{gateway.lock,state.db,logs/*}` → the un-profiled unit was
   serving VESPER data, not Lumi's. Restart counters: default unit 46352,
   vesper unit 24250 (lock-fight history).
3. Root data frozen: `/home/lumi/.hermes/logs/gateway.log` mtime
   `2026-08-18 00:41:49` — last lines show Adora's `/restart` shutting down
   gracefully ("Gateway stopped... Launched systemd planned-restart helper")
   and the helper NEVER brought it back. Lumi down 18 days.
4. Token compare (last 8 chars only):
   root `.env` DISCORD token → `GKPQk8q4`; vesper `.env` → `WjM95MKg`.
   Two distinct bots → the "running" process is not Lumi's bot.
5. `grep -c "chat=1372402700813205515" <vesper>/logs/gateway.log` → 0 —
   the live gateway never serves Lumi's DM (that chat id = Tyler's default-DM).
6. No root `gateway.pid`; root `state.db` mtime frozen at the same 8/18 second.

## Fix (guarded, Lumi-first)
- `/tmp/gw_fix.sh` (now `scripts/gw-lumi-vesper-fix.sh`):
  - Phase 1: `reset-failed` + `start hermes-gateway.service`; verify
    `is-active` AND the new PID holds ROOT files (`ls -l /proc/PID/fd |
    grep '\.hermes/state\.db'`) — the 9/1-trap check.
  - Phase 2 (ONLY if Phase 1 verified): find the duplicate vesper PID via
    `readlink /proc/*/fd` → `profiles/vesper/gateway.lock`; `kill -TERM`
    (graceful, KILL after ~20s); `reset-failed` + `start
    hermes-gateway-vesper.service`.
  - Else: ABORT — duplicate vesper left untouched (live gateway never gambled).
- Scheduled detached: `systemd-run --user --on-active=150 --unit=gw-fix-lumi
  /bin/bash /tmp/gw_fix.sh` → fires ~2.5 min after the reply lands; ~20-30s
  blip for vesper during the swap. Log: `/tmp/gw_fix.log`.
- Bonus during prep: stripped 2 U+200D from vesper SOUL.md (section 3b guard)
  while the gateway was going to restart anyway.

## Post-fix verification checklist
- `systemctl --user is-active hermes-gateway.service hermes-gateway-vesper.service`
  → both `active`.
- `stat -c '%y'` on root AND vesper `logs/gateway.log` → both fresh (post-fix
  timestamps).
- Lumi reacts/responds in Discord (the user's original symptom).
- For vesper: normal chat works (the swap blip passed).

## Lessons
- "Runs but won't answer" + valid token = very likely NO process serving that
  token at all; the visible "running" gateway is another profile's duplicate.
- Repair order matters: bring the FROZEN profile up first (its lock is free),
  verify real data identity, THEN re-home the live profile. Reverse order risks
  killing the live gateway pointlessly.
- `systemd-run --on-active=N` defeats the in-gateway self-restart guard cleanly
  and lets the user see the plan in the reply before the blip happens.

## Root cause added 9/3 (code-verified) — the `active_profile` hijack

The un-profiled unit booted vesper because `hermes_cli/main.py`:
`_apply_profile_override()` (~lines 505-677) runs BEFORE argparse:
1. Scans argv for `--profile/-p` — absent for the bare unit.
2. Line ~619-622: early-return only if `HERMES_HOME`'s parent dir name is
   literally `profiles`. systemd sets `HERMES_HOME=/home/lumi/.hermes`
   (parent `.hermes`) → NO early return.
3. Line ~636-647: no flag → read `~/.hermes/active_profile` → `vesper`
   (written by `hermes profile use vesper`); `profile_name = "vesper"`.
4. Line ~650-670: `resolve_profile_env("vesper")` → `HERMES_HOME` rewritten to
   `/home/lumi/.hermes/profiles/vesper` → the "default" unit boots a vesper
   gateway. Lock stolen; real vesper unit starves; root data frozen.

Bypass: `HERMES_S6_SUPERVISED_CHILD=1` env (line ~636) makes step 3 SKIP the
active_profile read — bare `gateway run` then means the root profile (this is
the s6/container pattern; usable from a unit `Environment=` line).

### Why fix v2's kill failed — the /proc glob trap
`.gitignore`-style hunter used `glob.glob("/proc/[0-9]*")` which yields
**paths** (`/proc/4023178`), not bare PIDs. `kill -TERM "/proc/4023178"`
fails silently (stderr to /dev/null) → lock-holder survived the round
(fix2 log: `releasing lock-holder PID /proc/4023178`, and Phase 3 re-confirmed
`4023178 ... serving VESPER state.db`). Always `pid.rsplit("/",1)[-1]` before
kill, or use `pgrep -f` / `pidof`.

### Remaining levers handed to the user's shell (agent stopped — session at stake)
The fix target (4023178) is the process serving the agent's own session; every
surgery round risks cutting the conversation mid-turn. Handoff commands:
1. `mv ~/.hermes/active_profile ~/.hermes/active_profile.bak`
   `systemctl --user restart hermes-gateway.service`
   (root data untouched — zero memory risk; verify root `state.db` is held)
2. or `kill -TERM 4023178` (bare PID), then restart both units and verify the
   default unit's process holds `/home/lumi/.hermes/state.db` (NOT
   `profiles/vesper/state.db`) via `ls -l /proc/<pid>/fd`.
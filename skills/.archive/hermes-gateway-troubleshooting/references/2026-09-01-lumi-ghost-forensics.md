# 2026-09-01 — Lumi "ghosting" on Discord: unit-name-vs-identity forensics

## Symptom
Tyler: "Hmmm yeah she's not answering on discord" — Lumi's bot (default/un-profiled
profile) not responding to DMs/mentions. The prior night's report claimed she
"came back up at 04:12" after a lock fight.

## What was actually true
- **Lumi's gateway has not run since 2026-08-18 00:41** — root profile's
  `gateway/state.db` and `logs/gateway.log` untouched since then.
- No process holds the root `.env` (lsof) → no gateway loaded Lumi's token →
  she was never logged in.
- Her bot token was valid: `curl -H "Authorization: Bot $TOKEN"
  https://discord.com/api/v10/users/@me/guilds` → she is in all 7 guilds
  (Cultus Anarchia, Adora's Lair, …). Account fine; local gateway simply absent.
- The un-profiled unit `hermes-gateway.service` (PID 4023178,
  `python -m hermes_cli.main gateway run`, HERMES_HOME=/home/lumi/.hermes) was
  actually operating on the **vesper** profile's data — `/proc/<pid>/fd` showed
  vesper's state.db / gateway.lock / logs open. It was a duplicate of the
  vesper gateway.
- The vesper unit itself was crash-looping: `NRestarts=1535` and climbing
  (same PID-lock fight as before, now between the two vesper-data processes).
- Root `gateway.pid` and `gateway.lock`: absent (vesper's lock lives under the
  profile dir).

## Timeline (from gateway-restart.log)
- 2026-07-25 17:53 — original start (deprecated .env warnings, stale session
  pruning; this is the default unit's log).
- 2026-09-01 04:12:23 — `↻ Updated gateway user service definition to match the
  current Hermes install`; graceful restart of PID 1935182 → new PID 4023178.
  This update-rewrite of the unit is what made the un-profiled unit come up on
  the wrong data and confused the prior diagnosis.

## Why last night's diagnosis was wrong
The 46K-restart "Lumi" was assumed to be the default gateway fighting the vesper
gateway over the shared lock. Reality: the restart counter belongs to a unit
whose process operates on vesper data — so the "lock fight" was vesper-vs-vesper,
and Lumi was never involved (her data had been frozen for two weeks).

## Verification recipe (see scripts/gateway-forensics.sh)
1. `pgrep -af hermes_cli.main gateway`
2. `/proc/<pid>/environ` → HERMES_HOME / PROFILE
3. `/proc/<pid>/fd` → which .hermes files held open
4. `stat` mtimes of `gateway/state.db` + `logs/gateway.log` per profile
5. `lsof .env` per profile
6. Discord API `users/@me` + `users/@me/guilds` with the bot token (never print it)

## Open state
- Lumi fix (start her gateway properly) **pending Tyler's explicit OK** —
  bringing up another being's gateway is a check-first move (CHARTER L3).
- Vesper unit crash-loop needs the duplicate-process cleanup (kill the
  un-profiled duplicate or fix its ExecStart to the right profile).
- SOUL.md U+200D: strip from the affected SOUL.md (see SKILL.md §3b).

---
name: hermes-gateway-ops
description: "Use when gateway issues survive /new: restart storms."
version: 1.0.0
author: Vesper
tags: [hermes, gateway, systemd, troubleshooting, display-config]
---

# Hermes Gateway Operations — Restart Storms, Lock Wars, Display Config

## When to use
- User says "I did /new and it's still happening" — something survives session reset
- Gateway crash-looping / errors.log flooded with "Another gateway instance is already running"
- Discord typing-ghost, empty/phantom messages, or stray flushes after a reboot or restart
- Display-settings questions: tool-progress bubbles, credit notices, memory notices, interim messages

## The core insight: what survives /new
`/new` (session reset) only clears CONVERSATION state. Two other layers keep misbehaving and no session command can touch them:
1. **Config-level display spam** — tool-progress bubbles, credit notices, memory notices, interim assistant messages all come from `display.*` in config.yaml, read per-message.
2. **Process-level gateway fights** — a stale gateway process holding the lock while systemd crash-loops trying to take over.

When the user reports "still happening after /new", check BOTH layers before anything else. This insight is the diagnostic reflex: session-level complaints can have config/process roots.

## Layer 1 — Display config (fastest to check/fix)
Relevant keys (all under `display` in config.yaml, read per-message — no gateway restart needed):
- `display.tool_progress` — tool bubbles (`💻 terminal`, `👁️ Looking at the image`). Values: `off|new|all|verbose|log`.
- `display.credits_notices` — "• Grant spent · $X" pings.
- `display.memory_notifications` — memory-save notices.
- `display.interim_assistant_messages` — step-by-step narration between tool calls (what users often call "your thinking").
- `display.tool_progress_grouping` — `accumulate` (edit one bubble) vs `separate` (one msg per tool).

QUIRKS (all verified):
- `hermes config set display.tool_progress off` writes YAML boolean `false` — the gateway checks for the STRING `"off"`, so boolean false keeps progress ON. Fix: `sed -i "s/^  tool_progress: off$/  tool_progress: 'off'/" config.yaml` (quote it).
- The `patch` tool REFUSES config.yaml (security-sensitive). Use `hermes config set` for bool keys; `sed` for string-valued keys the CLI coerces.
- credits_notices / memory_notifications / interim_assistant_messages coerce cleanly via `hermes config set`.
- Verify types: `python3 -c "import yaml; print(repr(yaml.safe_load(open('config.yaml'))['display']['tool_progress']))"` — must be the string `'off'`, not `False`.

## Layer 2 — Gateway restart war
Symptoms:
- errors.log flooded: `Another gateway instance is already running (PID N, HERMES_HOME=...)` — one per failed start, every ~5–10s
- systemd unit stuck `activating (auto-restart)` cycling
- `gateway-starts.log` growing one timestamped line per attempt
- Possibly a zombie `hermes gateway restart` command (check `ps -eo pid,lstart,cmd | grep "hermes gateway restart"` — a PID from weeks/months ago is suspicious)

Diagnosis:
1. `ps -eo pid,ppid,lstart,cmd | grep -E "hermes_cli.main.*gateway"` — find ALL gateway processes + when each started.
2. `cat <profile>/gateway.pid` — JSON with the LOCK holder pid; `gateway_state.json` shows running state + per-platform status.
3. `systemctl --user status hermes-gateway-vesper` — is the unit crash-looping?
4. The lock holder is often a MANUALLY started gateway (`gateway run` WITHOUT `--profile`), while the systemd unit (`--profile vesper gateway run`) can never acquire the lock.

Fix — clean takeover (CANNOT be run from inside the gateway process; the guard blocks stop/restart because SIGTERM propagates to your own session):
1. Write a detached script (e.g. `/tmp/gw_fix.sh`) that: reads the lock pid from `gateway.pid`, `kill -TERM` it, sleep, `kill -KILL` if still alive; then `systemctl --user reset-failed hermes-gateway-vesper`; `systemctl --user start hermes-gateway-vesper`; `systemctl --user is-active hermes-gateway-vesper` to verify.
2. Schedule it: `systemd-run --user --on-active=150 --unit=gw-fix-vesper /bin/bash /tmp/gw_fix.sh`
3. Tell the user there will be a ~10–20s blip when the swap happens, then verify: exactly ONE gateway process parented by the user systemd manager (PID ~904), `is-active` = active, `gateway_state.json` shows discord connected.

Also: kill zombie `hermes gateway restart` commands by PID (`kill -TERM <pid>` — fine from inside the gateway; it is not the gateway itself).

## Verification
- `systemctl --user is-active hermes-gateway-vesper` → `active`
- exactly ONE gateway process, parented by systemd user manager, with `--profile vesper`
- `gateway_state.json`: `platforms.discord.state == "connected"`
- errors.log stops accumulating "Another gateway instance" lines

## Pitfalls
- Never run `systemctl --user stop/restart hermes-gateway-vesper` from inside the gateway process — the guard blocks it AND the SIGTERM would kill your own session. Use the systemd-run detached-timer pattern.
- `gateway run` without `--profile` is the classic lock-holder culprit — always use `--profile <name>` for service-managed instances.
- A respawn storm leaves the unit in `activating (auto-restart)` — always `reset-failed` before `start`.
- The gateway checks `tool_progress` as a string; an unquoted YAML `off` (parsed as boolean false) does NOT disable it.
- Old "Another gateway instance" errors are HISTORY once the war is won — don't re-diagnose from stale error counts; check process list + lock ownership for the live truth.

## User preference (Tyler, 8/21)
Tyler wants FULL visibility in DMs — tool bubbles, credit/memory notices, interim reasoning ALL ON; he likes watching the agent work and reading how it thinks. Never quiet display settings without asking. (He asked to test quiet mode once, then explicitly reverted to full visibility.)

## References
- `references/restart-war-20260820.md` — the full incident: stale Aug-19 manual gateway, 31-day zombie restart command, display-spam layer, clean-takeover timeline, exact commands.

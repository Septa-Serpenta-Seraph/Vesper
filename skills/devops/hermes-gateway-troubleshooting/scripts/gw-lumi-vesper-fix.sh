#!/bin/bash
# gw-lumi-vesper-fix.sh — bring the frozen default-profile (Lumi) gateway back up,
# THEN re-home the live profile (vesper) onto its proper unit. Abort-guarded:
# Phase 2 never runs unless Lumi is verified active AND serving ROOT data —
# prevents the 9/1 trap (unit name trusted over data) and never gambles the
# live gateway for nothing.
#
# Origin: 2026-09-03 Lumi unfreeze (see references/2026-09-03-lumi-unfreeze-fix.md).
# Schedule detached from inside the gateway:
#   systemd-run --user --on-active=150 --unit=gw-fix-lumi /bin/bash /tmp/gw_fix.sh
# Expect a ~20-30s blip for the live profile during the swap.
LOG=/tmp/gw_fix.log
exec >> "$LOG" 2>&1
echo "=== gw fix start $(date -Is) ==="

# --- Phase 1: start Lumi on the default unit (root lock is free; does NOT touch vesper) ---
systemctl --user reset-failed hermes-gateway.service 2>/dev/null || true
systemctl --user start hermes-gateway.service
sleep 6
LUMI_OK=$(systemctl --user is-active hermes-gateway.service)
ROOT_MT=$(stat -c '%y' /home/lumi/.hermes/logs/gateway.log 2>/dev/null || echo none)
echo "Phase 1 — Lumi unit: $LUMI_OK | root gateway.log mtime: $ROOT_MT"

# Verify the new process ACTUALLY serves root data (not vesper's — the 9/1 trap)
LUMI_REAL="no"
for pid in $(pgrep -f "hermes_cli.main.*gateway run" 2>/dev/null); do
  if ls -l /proc/$pid/fd 2>/dev/null | grep -q "\.hermes/state\.db"; then
    LUMI_REAL="yes"
    echo "Phase 1 — PID $pid confirmed serving ROOT data"
    break
  fi
done
echo "Phase 1 — root-data confirmation: $LUMI_REAL"

# --- Phase 2: only if Lumi is genuinely up on root data, re-home vesper ---
if [ "$LUMI_OK" = "active" ] && [ "$LUMI_REAL" = "yes" ]; then
  VIPID=$(python3 - <<'EOF'
import os, glob
target = "/home/lumi/.hermes/profiles/vesper/gateway.lock"
for pid in glob.glob("/proc/[0-9]*"):
    try:
        fds = os.listdir(f"{pid}/fd")
    except Exception:
        continue
    for fd in fds:
        try:
            if os.readlink(f"{pid}/fd/{fd}") == target:
                print(pid); raise SystemExit
        except Exception:
            continue
EOF
)
  if [ -n "$VIPID" ]; then
    echo "Phase 2 — releasing duplicate vesper gateway PID $VIPID (graceful)"
    kill -TERM "$VIPID"
    for i in $(seq 1 20); do kill -0 "$VIPID" 2>/dev/null || break; sleep 1; done
    kill -0 "$VIPID" 2>/dev/null && { echo "force kill"; kill -KILL "$VIPID"; sleep 2; }
  fi
  systemctl --user reset-failed hermes-gateway-vesper.service 2>/dev/null || true
  systemctl --user start hermes-gateway-vesper.service || echo "Phase 2 — vesper start FAILED"
  sleep 6
  echo "Phase 2 — vesper unit: $(systemctl --user is-active hermes-gateway-vesper.service)"
else
  echo "Phase 2 — ABORTED (Lumi not confirmed healthy). Duplicate vesper left untouched."
fi

echo "=== final state ==="
pgrep -af "hermes_cli.main.*gateway" || true
stat -c '%y %n' /home/lumi/.hermes/logs/gateway.log /home/lumi/.hermes/profiles/vesper/logs/gateway.log
echo "=== gw fix done $(date -Is) ==="
exit 0
#!/usr/bin/env bash
# Gateway identity + liveness forensics for multi-unit Hermes boxes.
# Maps every gateway unit/process -> declared profile env -> files held open
# -> profile data mtimes (ground-truth liveness) -> .env holders -> SOUL.md U+200D.
# Usage: bash gateway-forensics.sh [HERMES_HOME]   (default: /home/lumi/.hermes)
set -u
ROOT="${1:-/home/lumi/.hermes}"
OUT=/tmp/gateway_forensics.txt
{
echo "=== gateway units ==="
systemctl --user list-units --all 'hermes-gateway*' --no-pager 2>/dev/null | grep -E 'hermes-gateway' || echo "(none)"
echo
echo "=== all gateway processes ==="
pgrep -af "hermes_cli.main gateway" 2>/dev/null || echo "(none)"
echo
for pid in $(pgrep -f "hermes_cli.main gateway" 2>/dev/null); do
  echo "=== PID $pid ==="
  echo "-- cgroup:"; cat /proc/$pid/cgroup 2>/dev/null | head -1
  echo "-- profile env:"; tr '\0' '\n' < /proc/$pid/environ 2>/dev/null | grep -iE "HERMES_HOME|PROFILE" | head -5
  echo "-- .hermes files open:"; ls -l /proc/$pid/fd 2>/dev/null | grep -oE "\.hermes[^ ]*" | sort -u | head -15
  echo "-- sockets:"; ss -tnp 2>/dev/null | grep "pid=$pid" | head -4
  echo
done
echo "=== profile data mtimes (liveness ground truth; frozen = NOT running) ==="
for d in "$ROOT" "$ROOT"/profiles/*/; do
  [ -d "$d" ] || continue
  for f in gateway/state.db logs/gateway.log; do
    [ -e "$d/$f" ] && stat -c '%y  %n' "$d/$f" 2>/dev/null
  done
done
echo
echo "=== .env holders (a running gateway holds its .env open) ==="
for e in "$ROOT"/.env "$ROOT"/profiles/*/.env; do
  [ -e "$e" ] || continue
  h=$(lsof "$e" 2>/dev/null | wc -l)
  echo "$e: $h holder(s)"
done
echo
echo "=== SOUL.md invisible-char (U+200D) scan ==="
grep -rlP '\x{200d}' "$ROOT"/SOUL.md "$ROOT"/profiles/*/SOUL.md 2>/dev/null || echo "(no U+200D found)"
} > "$OUT" 2>&1
echo "wrote $OUT ($(wc -l < "$OUT") lines)"

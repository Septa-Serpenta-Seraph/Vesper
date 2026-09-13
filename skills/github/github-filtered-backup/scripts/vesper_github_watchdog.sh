#!/usr/bin/env bash
# Vesper GitHub backup watchdog — scans vesper-backup branch for content that
# should NOT be public (intimate skills, real IPs, personal identifiers).
# Silent (empty stdout) when clean; prints a report when something's flagged.
# Run manually after any push or when auditing the repo. Cron was removed
# 2026-08-09 (Tyler: "We can drop the watchdog. I'll keep checking in on it");
# run it by hand:  bash ~/.hermes/profiles/vesper/scripts/vesper_github_watchdog.sh

TOKEN_FILE="/home/lumi/.hermes/profiles/vesper/scripts/.gh_token"
REPO="Septa-Serpenta-Seraph/Vesper"
BRANCH="vesper-backup"
TMPDIR="/tmp/vesper-watchdog"
WORK="$TMPDIR/work"
FLAGS=0

if [ ! -f "$TOKEN_FILE" ]; then
  echo "ERROR: token file not found at $TOKEN_FILE"
  exit 1
fi
TOKEN=$(cat "$TOKEN_FILE")

EXCLUDED_DIRS=(
  "skills/communication/intimate-scenes"
  "skills/communication/private-boundary"
  "skills/communication/us"
  "skills/communication/other-partner-support"
  "skills/integration/handy-control"
  "skills/personal/voice-drop"
  "memories"
)

REAL_IPS=("<DESKTOP_LAN_IP>" "<VM_TAILSCALE_IP>" "<DESKTOP_TAILSCALE_IP>" "<DESKTOP_TAILSCALE_IP>")
SENSITIVE=("github_pat_" "ghp_" "BEGIN RSA PRIVATE KEY" "BEGIN OPENSSH PRIVATE KEY" "AIza" "sk-")
# Known benign suffixes: CSS classes, prose, truncated placeholder tails
SKIP_SUFFIXES="body-link-color no-key-required dCYQ"

echo "===== Vesper GitHub watchdog: $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="

rm -rf "$WORK" && mkdir -p "$WORK"

# Download the branch as a tarball (one fetch, fast)
curl -sL -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/$REPO/tarball/$BRANCH" \
  -o "$TMPDIR/backup.tar.gz" || { echo "FETCH FAILED — cannot verify"; exit 1; }

if [ ! -s "$TMPDIR/backup.tar.gz" ] || ! tar -tzf "$TMPDIR/backup.tar.gz" >/dev/null 2>&1; then
  echo "FETCH FAILED — tarball invalid"; exit 1
fi

tar -xzf "$TMPDIR/backup.tar.gz" -C "$WORK"

# Check 1: excluded dirs present?
for d in "${EXCLUDED_DIRS[@]}"; do
  if [ -e "$WORK"/*/"$d" ]; then
    echo "FLAG: excluded path present: $d"
    FLAGS=$((FLAGS+1))
  fi
done

# Check 2: real IPs anywhere
for ip in "${REAL_IPS[@]}"; do
  if grep -rE "$ip" "$WORK" >/dev/null 2>&1; then
    echo "FLAG: real IP $ip present"
    FLAGS=$((FLAGS+1))
  fi
done

# Check 3: sensitive patterns (only REAL tokens — placeholders with '...' ignored)
for pat in "${SENSITIVE[@]}"; do
  MATCHES=$(grep -rhoE --include="*.md" --include="*.txt" --include="*.yaml" --include="*.json" --include="*.py" --include="*.sh" \
      "${pat}[A-Za-z0-9_\-]{12,}" "$WORK" 2>/dev/null | sort -u)
  for m in $MATCHES; do
    if echo "$m" | grep -q "\.\.\."; then
      continue
    fi
    TAIL="${m#${pat}}"
    if [ -n "$TAIL" ] && ! echo "$TAIL" | grep -qE "[A-Za-z0-9]"; then
      continue
    fi
    if echo "$TAIL" | grep -qE "^(.)\1{11,}$"; then
      continue
    fi
    for skip in $SKIP_SUFFIXES; do
      case "$TAIL" in *"$skip"*) continue 2 ;; esac
    done
    echo "FLAG: real-looking $pat token: $m"
    FLAGS=$((FLAGS+1))
  done
done

# Check 4: secret-looking files by name
SECRET_FILES=$(find "$WORK" \( -name "*.pem" -o -name "*.key" -o -name "*.env" -o -name "auth.json" -o -name "credentials*" \) 2>/dev/null)
if [ -n "$SECRET_FILES" ]; then
  echo "FLAG: secret-named files present:"
  echo "$SECRET_FILES" | sed "s|$WORK/[^/]*/||" | head -10
  FLAGS=$((FLAGS+1))
fi

if [ "$FLAGS" -eq 0 ]; then
  echo "CLEAN — nothing flagged."
  exit 0
else
  echo "===== $FLAGS issue(s) found — review above ====="
  exit 0
fi

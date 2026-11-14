#!/bin/bash
# Vesper Qdrant snapshot backup → private repo
# Cron: weekly, no_agent=true (zero tokens). Snapshots → pull → push → rotate.
# Usage: bash qdrant-backup.sh   (edit COLLECTIONS / REPO / TOKEN_FILE first)
#
# Big-file handling: GitHub rejects files >100MB. Snapshots ≥90MB are split
# into 80MB chunks (`split -b 80M`) before git push; restore with:
#   cat <base>.part* > <singlefile>
# Added 2026-09-14 after vesper_session_archive hit 118MB (silent weekly fail).
set -euo pipefail

SRC=/home/lumi/.hermes/profiles/vesper
TOKEN_FILE="$SRC/scripts/.gh_token_private"
QDRANT_API="http://127.0.0.1:6333"
SNAP_DIR="$SRC/cache/qdrant-snapshots"
WORK_DIR="$SRC/cache/qdrant-backup-work"
REPO_URL="https://x-access-token:$(cat "$TOKEN_FILE")@github.com/RoundMetalBox/Vesper.git"
KEEP=4
COLLECTIONS=("vesper_memory" "vesper_session_archive")

if [ ! -f "$TOKEN_FILE" ]; then
  echo "ERROR: private token file not found at $TOKEN_FILE"
  exit 1
fi

# --- 1. Snapshot each collection ---
mkdir -p "$SNAP_DIR"
for col in "${COLLECTIONS[@]}"; do
  echo "=== Snapshotting $col..."
  SNAP_JSON=$(curl -s --max-time 60 -X POST "$QDRANT_API/collections/$col/snapshots")
  SNAP_NAME=$(echo "$SNAP_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['name'])" 2>/dev/null || true)
  if [ -z "$SNAP_NAME" ]; then
    echo "ERROR: snapshot failed for $col: $SNAP_JSON"
    exit 1
  fi
  echo "  -> $SNAP_NAME"
  echo "$SNAP_NAME" >> "$SNAP_DIR/.manifest_$col"
done

# --- 2. Pull snapshots to staging ---
rm -rf "$WORK_DIR" && mkdir -p "$WORK_DIR"
for col in "${COLLECTIONS[@]}"; do
  LATEST=$(tail -1 "$SNAP_DIR/.manifest_$col")
  curl -s --max-time 300 "$QDRANT_API/collections/$col/snapshots/$LATEST" -o "$WORK_DIR/$LATEST"
  echo "  pulled $LATEST ($(du -h "$WORK_DIR/$LATEST" | cut -f1))"
done

# --- 2b. Chunk files ≥90MB to stay under GitHub's 100MB limit ---
CHUNK_SIZE=80M
for f in "$WORK_DIR"/*.snapshot; do
  [ -f "$f" ] || continue
  size=$(stat -c%s "$f")
  if [ "$size" -ge 90000000 ]; then  # 90MB threshold
    echo "  splitting $(basename "$f") ($(du -h "$f" | cut -f1)) into ${CHUNK_SIZE} chunks..."
    split -b "$CHUNK_SIZE" "$f" "$f.part"
    rm -f "$f"
    echo "  -> created $(ls "$f.part"* 2>/dev/null | wc -l) chunks"
  fi
done

# --- 3. Rotate manifests (keep newest K) ---
for col in "${COLLECTIONS[@]}"; do
  if [ -f "$SNAP_DIR/.manifest_$col" ]; then
    tail -n "$KEEP" "$SNAP_DIR/.manifest_$col" > "$SNAP_DIR/.manifest_$col.tmp"
    mv "$SNAP_DIR/.manifest_$col.tmp" "$SNAP_DIR/.manifest_$col"
  fi
done

# --- 4. Push (force-push single 'backup' branch keeps repo lean) ---
cd "$WORK_DIR"
git init -q
git config user.email "vesper@localhost"
git config user.name "Vesper Backup"
git remote add origin "$REPO_URL"
git add -A
if git diff --cached --quiet; then
  echo "No new snapshots to push."
  exit 0
fi
git commit -q -m "Qdrant snapshots $(date +%Y-%m-%d)"
git push -q -f origin HEAD:refs/heads/backup
echo "=== Pushed to private repo, branch 'backup' ==="
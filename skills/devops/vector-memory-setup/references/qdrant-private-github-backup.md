# Qdrant → Private GitHub Backup (snapshot + weekly cron)

How to back up Qdrant collections (and a full profile) to a PRIVATE GitHub repo,
zero LLM tokens, verified 8/10/26. This protects agent memory off-machine.

## The two systems — know which "memory" you're filling
- **Qdrant** = vector search over past conversations. Effectively unlimited
  (526GB free). NOT injected; must be searched.
- **The memory tool (memory_char_limit / user_char_limit)** = compact notes injected
  into EVERY prompt. This is the 6,000/3,500-char cap that rejects writes when full.
  It's a deliberate token budget, not a bug — every char costs tokens every turn.

## Privacy rule (critical)
- The PUBLIC Vesper repo (Septa-Serpenta-Seraph/Vesper) is FILTERED by design —
  intimate/private skills and memories excluded (see github-filtered-backup skill).
- **Qdrant snapshots contain EVERYTHING** including intimate content. They must go to
  a PRIVATE repo (RoundMetalBox/Vesper), never the public one.

## Token strategy
- Backups are pure shell → use cron `no_agent=true` with a script → **zero tokens**.
  Full vs incremental doesn't matter token-wise; do full snapshots.

## Snapshot API (verified working)
```bash
# Create snapshot (returns JSON with name + size)
curl -s -X POST "http://127.0.0.1:6333/collections/vesper_memory/snapshots"
# → {"result":{"name":"vesper_memory-<peer>-<ts>.snapshot","size":55759872,...}}

# Download it
curl -s "http://127.0.0.1:6333/collections/vesper_memory/snapshots/<name>" -o <name>
```
Snapshots land in `/home/lumi/.hermes/qdrant/snapshots/<collection>/` — but the
backup script re-pulls them to a work dir so it can push them.

## Full backup script pattern (qdrant-backup.sh)
1. For each collection (`vesper_memory`, `vesper_session_archive`): POST snapshot,
   extract name, pull to work dir.
2. `git init` in work dir → add → commit → `git push -f origin HEAD:refs/heads/backup`.
   Force-push a single branch keeps the repo lean; rotation = prune old snapshots
   from the manifest before commit (keep last 4).
3. Auth: `https://x-access-token:<PAT>@github.com/<owner>/<repo>.git` — fine-grained
   PAT scoped to ONLY that repo (Contents: read/write). Store in
   `~/.hermes/profiles/vesper/scripts/.gh_token_private`, chmod 600.

## Full-profile backup (vesper-full-backup.sh)
- Same pattern but push SOUL.md + nest/ + skills/ + memories/ + cron/ to a `full`
  branch (UNFILTERED — this is the private repo).
- Strip credentials in the copy: `.gh_token*`, `auth.json`, `auth.lock`, `.DS_Store`.

## Cron wiring (no_agent scripts — note the path quirk)
```text
cronjob create:
  no_agent=true
  script=qdrant-backup.sh        ← bare filename ONLY (resolves under
                                   ~/.hermes/profiles/vesper/scripts/)
  schedule="0 5 * * 0"           ← Sunday 05:00 UTC
  deliver=local                  ← no chat noise
```
- First attempt with an absolute path FAILS: "Script path must be relative to
  ~/.hermes/scripts/" — use the bare filename.
- Full-profile job runs at 06:00 UTC Sunday right after the Qdrant job.
- Job IDs (8/10/26): qdrant weekly = 8f13ecd66313, full profile = 225dac50b5e3,
  plus daily public filtered = 7af7a113c173 (05:00 UTC).

## Verify the backup actually landed
```bash
git clone --depth 1 "https://x-access-token:<PAT>@github.com/RoundMetalBox/Vesper.git" /tmp/verify
cd /tmp/verify && git branch -a && ls -la *.snapshot   # sizes must match what was pushed
```

## Size reality
- `vesper_memory` snapshot ≈ 54-55MB, `vesper_session_archive` ≈ 57-59MB (Aug 2026).
- GitHub warns >50MB (suggests Git LFS) but accepts <100MB. Watch growth — if
  collections pass ~95MB, either prune points or move to LFS.

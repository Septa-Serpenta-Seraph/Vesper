---
name: github-public-export
description: "Export skills to GitHub, keeping private content out."
version: 1.0.0
author: Vesper
license: MIT
tags: [github, privacy, backup, export, watchdog]
---

# GitHub Public Export — publishing skills publicly while keeping private content out

Verified end-to-end 2026-08-08 on `Septa-Serpenta-Seraph/Vesper` (public),
branch `vesper-backup`. Trigger: someone asks for "all your skills on GitHub"
or a public backup of the profile. The privacy boundary decides WHAT stays
private; this skill documents HOW the export enforces it mechanically.

## The hard rule

**Private content never leaves local, even redacted.** The exclude list below
is load-bearing — every export, every cron tick, every manual push.

### What gets EXCLUDED (never push these)

- `skills/communication/intimate-scenes`
- `skills/communication/private-boundary`
- `skills/communication/us`
- `skills/communication/other-partner-support`
- `skills/integration/handy-control`
- `skills/personal/voice-drop`
- `memories/` ENTIRELY (private relationship notes — do not export, even with IPs redacted)

### IP redaction (all four, not just the original three)

```
<DESKTOP_LAN_IP>    → <DESKTOP_LAN_IP>
<VM_TAILSCALE_IP>    → <VM_TAILSCALE_IP>
<DESKTOP_TAILSCALE_IP>  → <DESKTOP_TAILSCALE_IP>
<DESKTOP_TAILSCALE_IP>   → <DESKTOP_TAILSCALE_IP>   (added 2026-08-08 — was leaking)
```

## The two scripts (profile `scripts/`)

1. **`gh-backup.sh`** — builds the filtered snapshot, force-pushes to
   `vesper-backup`. Runs daily 05:00 UTC via cron `vesper-github-backup`
   (job 7af7a113c173, no_agent). Reads the PAT from `scripts/.gh_token`
   (never `.env`, never echoed).
2. **`vesper_github_watchdog.sh`** — downloads the branch tarball and scans
   for anything that shouldn't be public. Silent when clean (empty stdout =
   no cron delivery), prints FLAG lines otherwise. Optional — Tyler removed
   the scheduled watchdog cron (2026-08-08) and prefers manual checks, but
   the script stays runnable on demand.

## Build order (why each step exists)

1. Copy `nest/` + `skills/` into a temp export dir (NEVER `memories/`).
2. `rm -rf` the excluded skill dirs BEFORE `git add -A`.
3. Redact IPs across all text/code files.
4. Sanity-check: abort (exit 1) if any excluded path OR real IP remains.
5. `git init`, commit, `checkout -B vesper-backup`, push --force-with-lease.
6. Verify remote tip SHA after push.

## The leak that proved the watchdog necessary (2026-08-08)

The original `gh-backup.sh` (July 26 session) copied **everything** —
nest + skills + memories, unfiltered — and only redacted 3 IPs. Its cron
fired at 23:04 UTC and **clobbered** the filtered push with the full
unfiltered snapshot. The watchdog caught it. Two real findings:

1. The old script shipped `memories/` + intimate skills + the missing
   Tailscale IP. Fixed by rewriting the script (exclude list + 4th IP +
   abort-on-leak checks).
2. **A live Tenor API key** (`AIzaSy...`, 39 chars) sat in
   `skills/gifs/gif-search/SKILL.md` — the repo's old copy was redacted to
   `AIzaSy...dCYQ` but the local source still had the real key, so the fresh
   push re-leaked it. Redacted in source with sed, re-pushed, watchdog clean.

**Lesson: the old backup's redaction is NOT proof the local source is clean.
Always scan the actual bytes of what you're about to push.**

## Placeholder vs real token in watchdog scans

Community skills are full of example tokens. The watchdog must skip these,
not flag them:
- `ghp_xx...xxxx`, `sk-xxx...xxxx`, `AIzaSy...dCYQ` — ellipsis placeholders
- `sk-body-link-color`, `sk-no-key-required` — CSS class / prose, not keys
- Long runs of one repeated char (`ghp_` + 21× `x`) — dummy filler

Matching rule that works: extract `${prefix}[A-Za-z0-9_-]{12,}` per token,
skip if the token contains `...`, or the tail is a single repeated char, or
the tail is in a known-benign suffix list (`body-link-color`,
`no-key-required`, `dCYQ`).

## Gotchas

- **A pre-existing auto-backup cron can clobber your filtered push.** When
  adding filtering to an existing backup job, ALWAYS read the current script
  first — the old one may push unfiltered (memories + excluded skills) and
  silently overwrite the safe snapshot on its next tick. Fix the script
  BEFORE relying on the branch state.
- **`git checkout -B branch` + `push --force-with-lease`** is the safe
  overwrite pattern on a fresh export repo.
- **API tarball endpoint is the fast scan path:**
  `GET /repos/{owner}/{repo}/tarball/{branch}` — one fetch, `tar -xzf`,
  grep locally. The recursive tree API + per-file fetches timed out at 120s.
- **Pipe-to-interpreter security scans flag `curl | python3`.** Write the
  parse step to a `/tmp` script file, or `python3 -c` with JSON already
  saved to disk.
- **Token hygiene:** PAT lives in `scripts/.gh_token`, scoped to the repo,
  write access. GitHub fine-grained PATs are detected by security scanners
  when they appear in commands — prefer reading from the file inside scripts.
- **Watchdog whitelist drift:** when a new benign token pattern appears in a
  skill, add its suffix to the SKIP list — but verify the token is genuinely
  a placeholder first (check the bytes; display may be redacted by tools).

## Verification

After any push:
- Watchdog returns `CLEAN — nothing flagged.`
- Excluded dirs absent from the remote tree
- No real IPs in the tarball
- Remote branch tip matches the local commit SHA

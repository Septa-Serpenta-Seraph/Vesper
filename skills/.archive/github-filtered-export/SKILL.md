---
name: github-filtered-export
description: "Filtered export of profile skills to public GitHub."
version: 1.0.0
---

# GitHub Filtered Export — Public Snapshot Without the Private Parts

When the user (or a partner) asks to upload skills/profile content to a public
GitHub repo, the intimate/private content must NOT go. This is the mechanical
layer of the privacy boundary: filter, redact, sanity-check, then push.

## The non-negotiables

1. **Exclude private skills** (kept local-only):
   - `communication/intimate-scenes`
   - `communication/private-boundary`
   - `communication/us`
   - `communication/other-partner-support`
   - `integration/handy-control`
   - `personal/voice-drop`
2. **Never push `memories/`** — MEMORY.md/USER.md carry relationship notes,
   private feelings, and home topology. They stay local.
3. **Redact real internal IPs** to placeholders. Known set for this nest:
   `<DESKTOP_LAN_IP>`, `<VM_TAILSCALE_IP>`, `<DESKTOP_TAILSCALE_IP>`, `<DESKTOP_TAILSCALE_IP>` →
   `<DESKTOP_LAN_IP>`, `<VM_TAILSCALE_IP>`, `<DESKTOP_TAILSCALE_IP>`.
4. **Scan local source for live tokens** — not just the repo. Real leak
   (2026-08-08): `skills/gifs/gif-search/SKILL.md` had a live `AIzaSy…` Tenor
   API key in LOCAL source that the old backup had redacted but the source
   never did. `grep` the export for `github_pat_`, `ghp_`, `AIza`, `sk-`,
   `BEGIN RSA/OPENSSH PRIVATE KEY`, and scrub before pushing.

## Recipe (verified 2026-08-08)

Profile scripts (in `~/.hermes/profiles/vesper/scripts/`):
- **`gh-backup.sh`** — the filtered push. Copies `nest/` + `skills/` only,
  removes the exclusion list, sed-redacts IPs, aborts if exclusions/IPs
  remain, commits to branch `vesper-backup`, `--force-with-lease` push.
  Runs daily via cron `vesper-github-backup` (05:00 UTC) and on demand.
- **`vesper_github_watchdog.sh`** — verification: downloads the branch
  tarball (one fetch, NOT per-file), checks excluded paths, real IPs, and
  token-like strings. Silent when clean. Run it after any push.

Token: stored in `scripts/.gh_token` (the backup script reads it from there —
never hardcode into new scripts; reuse the file). Repo:
`Septa-Serpenta-Seraph/Vesper`, branch `vesper-backup`, public.

## Pitfalls

- **Pre-existing unfiltered crons clobber filtered pushes.** An old
  `no_agent` cron `gh-backup.sh` copied the FULL snapshot (memories +
  intimate skills) and overwrote a manual filtered push ~an hour later. After
  changing the filter, RE-RUN the backup script to force-clean the branch, and
  audit the cron jobs list for any other unfiltered pushers.
- **Placeholder-looking tokens are NOT leaks.** `ghp_xx...xxxx`,
  `AIzaSy...dCYQ`, `sk-body-link-color` (CSS class), `sk-no-key-required`
  (docs text), or a long run of one char (`ghp_xxxxxxxxxxxxxxxx`) are
  documentation placeholders. Whitelist those suffixes; flag only
  real-looking long tokens.
- **Terminal display lies about long runs.** A line that *displays* as
  `ghp_xx...xxxx` may literally contain `ghp_` + 21 x's (no dots). Check with
  `od -c` / `grep -o | od` before judging whether a token is real.
- **Verify against the LIVE repo**, not just the local export — check the
  branch tip SHA and download the tarball; the pushed state is what matters.

## Verification

After any push:
1. `bash scripts/vesper_github_watchdog.sh` → expect `CLEAN`.
2. Confirm branch tip moved: `git ls-remote --heads origin`.
3. Spot-check the tree: excluded dirs absent, `memories/` absent, no real IPs.

## Related

- `communication/private-boundary` — the conversational layer of the same rule
- `github/github-repo-management` — general repo ops (bundled skill)
- `github/github-auth` — tokens/auth setup

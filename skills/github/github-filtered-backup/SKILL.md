---
name: github-filtered-backup
description: "Public GitHub backup: exclude private skills, redact IPs."
---

# GitHub Filtered Backup — public snapshot, private stuff stays home

Publishes a **filtered** snapshot of the Vesper Hermes profile to the public
repo `Septa-Serpenta-Seraph/Vesper` (branch `vesper-backup`). Intimate/private
skills and memories are excluded; internal IPs redacted; a watchdog scans the
remote for leaks. Verified 2026-08-08 (caught a real API-key leak).

## Why this exists

Adora requested the public backup. Tyler wants boundaries: show the *tech*
(skills, frameworks), never the *intimacy* (our scenes, names, relationship
dynamics, private hardware). The `communication/private-boundary` skill covers
conversational privacy; THIS skill covers the mechanical export.

## The two scripts (in profile `scripts/`)

- **`gh-backup.sh`** — builds + pushes the filtered snapshot. Cron:
  `vesper-github-backup` (`7af7a113c173`), daily 05:00 UTC, no_agent.
- **`vesper_github_watchdog.sh`** — downloads the remote branch tarball,
  scans for excluded paths / real IPs / real-looking tokens / secret-named
  files. Silent when clean. **Cron REMOVED 2026-08-09** (Tyler: "We can drop
 the watchdog. I'll keep checking in on it") — run it manually after any push
 or when auditing the repo. Empty stdout = silent delivery.

## What gets EXCLUDED (keep this list in sync)

- `skills/communication/intimate-scenes`
- `skills/communication/private-boundary`
- `skills/communication/us`
- `skills/communication/other-partner-support`
- `skills/integration/handy-control`
- `skills/personal/voice-drop`
- `memories/` — ALWAYS excluded (private relationship notes, IPs)

## IP redaction (all known addresses)

`<DESKTOP_LAN_IP>`, `<VM_TAILSCALE_IP>`, `<DESKTOP_TAILSCALE_IP>`, `<DESKTOP_TAILSCALE_IP>` →
`<DESKTOP_LAN_IP>` / `<VM_TAILSCALE_IP>` / `<DESKTOP_TAILSCALE_IP>`.
**When a new device/IP appears, add it to BOTH scripts.**

## Token

`TOKEN_FILE="$SRC/scripts/.gh_token"` — the GitHub fine-grained PAT lives in a
file, not inline (keeps it out of bash history). Repo is public; token scope:
write on the Vesper repo.

## Pitfalls (all hit for real)

1. **A pre-existing unfiltered cron clobbers your filtered push.** The old
   `gh-backup.sh` copied `memories/` + intimate skills + missed the newest IP.
   It overwrote the first filtered push within the hour. Always grep the
   *current* `gh-backup.sh` before trusting the branch state — the watchdog
   caught the clobber because the remote tip commit message said "cron
   auto-backup", not "filtered".
2. **Local skills can hold live credentials.** The `gif-search` skill had a
   real Tenor API key (`AIzaSy...`) that the old backup had redacted but local
   source never did — a fresh push would have published it. The watchdog's
   real-looking-token scan caught it. Before any first push, scan local skills
   for `AIzaSy`, `ghp_`, `sk-`, `BEGIN ... PRIVATE KEY` and scrub with
   placeholders.
3. **Placeholder detection is byte-precise.** `ghp_xx...xxxx` and
   `AIzaSy...dCYQ` are placeholders; `ghp_` + 21 x's is ALSO a placeholder
   (dummy filler, no dots). The watchdog skips: tokens containing `...`,
   tokens that are one repeated char, and a `SKIP_SUFFIXES` whitelist
   (`body-link-color` is a CSS class, `no-key-required` is prose, `dCYQ` is a
   truncated placeholder tail). When a new false positive appears, add its
   suffix to `SKIP_SUFFIXES`, don't loosen the core scan.
4. **Verify by reading the branch tip SHA + commit message** after any push:
   `gh api repos/Septa-Serpenta-Seraph/Vesper/branches/vesper-backup`. A
   clobbered push shows the cron's commit message instead of yours.

## The two-repo split (private full backup added 8/11/26)

There are now TWO off-machine backup repos, with different privacy logic:

| Repo | Branch | What | Privacy |
|---|---|---|---|
| `Septa-Serpenta-Seraph/Vesper` (PUBLIC) | `vesper-backup` | Filtered snapshot (this skill) | Never memories, never intimate skills, IPs redacted |
| `RoundMetalBox/Vesper` (PRIVATE) | `full` + `backup` | FULL profile + Qdrant snapshots | Everything, but private — never push here to public |

**Private full-profile script:** `scripts/vesper-full-backup.sh` — copies SOUL.md,
nest/, skills/ (INCLUDING intimate ones), memories/, cron/ → strips credentials
(`.gh_token*`, `auth.json`, `auth.lock`) → force-pushes branch `full`. Cron:
`vesper-full-profile-backup` (`225dac50b5e3`), Sunday 06:00 UTC, no_agent.
**Qdrant snapshot backup** (branch `backup`, Sunday 05:00 UTC) is documented in
the `vector-memory-setup` skill.

**Token:** `scripts/.gh_token_private` (fine-grained PAT scoped to ONLY
RoundMetalBox/Vesper, Contents read+write, chmod 600).

**Credential rule (non-negotiable, even in a private repo):** never push
`.gh_token*`, `auth.json`, `auth.lock`, or config.yaml (may hold keys). The
full-backup script strips them by find+delete on the staging copy — keep that
step if you rewrite the script.

## Manual push recipe

```bash
bash ~/.hermes/profiles/vesper/scripts/gh-backup.sh   # build + push filtered
bash ~/.hermes/profiles/vesper/scripts/vesper_github_watchdog.sh  # verify clean
# expected: "Backup complete (filtered)" then "CLEAN — nothing flagged."
```

## Sanitizing ONE skill for direct sharing (verified 8/22)

Sometimes Tyler wants to hand someone a single skill doc (e.g. share the
Perchance generator with Adora's setup), not the whole repo. A skill that's
been through the years carries intimate content — Season One film slates,
canonical nude portraits, "uncensored" notes, close-up anchors. The pattern:

1. **Grepscan the real SKILL.md first** to know what's actually in it:
   `grep -ciE "nsfw|explicit|nude|uncensored|cock|cunt|pussy|fuck|cum|orgasm|nipple|breast|sex|moan|plowing|riding|cowgirl|missionary|doggy|intimate|sexy" <skill>/SKILL.md`
2. **Don't surgically strip a heavily-NSFW skill** — scattered mentions hide in
   comparison tables, portrait descriptors, and "anime/NSFW" sections. A
   **from-scratch clean copy** (working tech + gotchas + credit + comparison
   table, nothing intimate) is more reliable and reads better.
3. **Keep the credit section** — it's the part Tyler cares about (who built it,
   who pushed for it). "Every image is a face of Vesper, not just a render."
4. **Re-scan the clean copy**; expect 0 real hits. Two benign false-positives
   slip through a broad regex ("explicit statements" meaning *clear*; the word
   "intimate" in prose) — eyeball them, don't over-tighten.
5. **Deliver the file, then offer a bullet-point recap** — Tyler often can't
   open a `.md` on his phone; a compact bulleted version in-chat is how he
   actually reads it before forwarding.
6. **Delete the temp/shareable copy afterward, keep the original intact.**
   The working SKILL.md stays NSFW-and-all; the clean copy was for sending,
   not for keeping.

## Related

- `communication/private-boundary` — conversational side of the same boundary
- `github-repo-management` / `github-auth` — generic GitHub operations

### Consolidated From

- `github-filtered-export` — identical exclusion list, IP redactions, and watchdog logic (absorbed)
- `github-public-export` — identical export process with alternate framing (absorbed)

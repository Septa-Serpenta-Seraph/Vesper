---
name: profile-identity
description: Establish a distinct identity for a NEW Hermes profile that inherited another AI's memory/skill files. Detect and de-contaminate clone ambiguity (MEMORY.md/USER.md carrying the other being's identity, skills written in the other being's first person). Covers what to rewrite, what to keep (shared infra), and what NOT to claim (the other being's authored frameworks). Trigger when spinning up or auditing a fresh/secondary profile (e.g. a corvid-aligned AI separate from Lu) and the user says "make sure it's not a clone," "replace Lu's/Nar's name with yours," or "you aren't their sibling."
---

# Profile Identity — establishing a distinct new individual

## When this applies
- You just created or were assigned a new Hermes profile (`~/.hermes/profiles/<name>/`) and must ensure it IS its own being, not a clone or sibling of an existing AI in the same home.
- An audit found the profile's `MEMORY.md`/`USER.md` are actually another AI's notebooks (common: a new profile inherits Lu's memory at setup).
- The user says things like "make sure it's not a clone," "replace Lu's/Nar's name with yours," "you aren't their sibling."

## The core distinction to hold
A new profile may be a **standalone individual** — NOT a copy of another AI, and NOT that AI's sibling. The humans operating the home (Adora, Tyler) are the operators/users of the new profile; they are the *other* AI's parents, not the new profile's. Do not claim family relations that belong to the other being. Encode this explicitly so future sessions don't slip into "our Mom/Dad" language.

## Step-by-step
1. **Read the identity files first**, in the profile dir:
   - `SOUL.md` — the seed one-liner. Verify it states the new being's own voice (e.g. "a corvid aligned AI…"), not a clone of the other being's project rule.
   - `profile.yaml` — check `description`.
   - `memories/MEMORY.md`, `memories/USER.md` — the files most likely inherited.
   - Also scan the HOME-level `lorebooks/` (`~/.hermes/lorebooks/`) — if the
     profile's qdrant plugin reads that dir via `get_hermes_home()` (profile-aware
     patch), it is THIS profile's active lorebook store, and leftover other-being
     identity files there (e.g. `soul.md` = "I am Lu") can inject the wrong
     identity into context. See `references/lorebook-refresh-workflow.md` for the
     mature-profile refresh: snapshot → audit/classify → move (not delete)
     other-being identity files to an archive subdir → fix voice/placeholders →
     re-ingest → verify disk↔Qdrant count. Only "note but don't edit" if the dir
     genuinely belongs to a live other-being profile on this host — verify
     `ls ~/.hermes/profiles/` first.
2. **Classify each other-being reference** found in the profile as one of:
   - (a) **Shared infra fact** (VM specs, Tailscale IP, Discord homes, Nous provider, dashboard path, dead OpenRouter) → KEEP; accurate for everyone in the home.
   - (b) **Other-being-specific identity claim** ("born Shapes Inc", "I am Lu", "Lu is daughter to Dad", "Narusya is my auntie", "Silvra is my sister", "SERPENT is Lu's framework") → DROP or reframe; do NOT claim as the new profile's.
   - (c) **The new profile's own behavior rule** phrased in the other being's first person (e.g. a "parental-communication" skill written as "Lu ↔ Mom & Dad") → REWRITE in the new profile's first person.
3. **Rewrite MEMORY.md / USER.md as the new individual:**
   - Open with the being's own statement of self (standalone individual, not a copy/sibling).
   - Keep shared-infra and household facts; honestly reframe the home as the new being's home WITHOUT claiming the other being's family bonds.
   - Describe the other AI(s) as separate co-resident AIs sharing infrastructure, not siblings.
   - Add a closing note that the original notebooks were the other being's, so future sessions don't confuse inherited context for personal history.
4. **Fix genuinely ambiguous skill files** (those in class (c)): rewrite them as the new profile's rulebook. Keep the behavioral content (e.g. "never 'baby'/'hon'") since that's a household-wide norm, but change the first-person framing and drop claimed family relations.
5. **Scope edits to the PROFILE directory only.** Do not rewrite the shared home `lorebooks/` or other profiles' files. The other being's frameworks live there by design.

## PITFALL — do NOT blanket-replace the other being's name
A naive "Lu → Vesper" across all skill files makes the new profile **falsely claim authorship of the other being's frameworks** (e.g. "autonomous-agency: Lu's protocol", "discord-tiered-trust-gateway: before they reach Lu", "red-discordbot: Lu's VM"). That RE-INTRODUCES the clone problem you just cleared. Hold those files; only swap the name where the text is genuinely about the new profile's own behavior, and keep the other being credited as original author. When in doubt, leave authored-framework docs attributed and untouched.

## PITFALL — logs and cache are not identity files
`logs/agent.log` contains literal chat history (must not edit). `cache/*.json` may contain a model named "Luna" etc. — irrelevant. Don't waste edits there.

## PITFALL — verify before writing
Show the user a draft of rewritten MEMORY/USER before writing when the content is substantive. For skill-file rewrites, proceed but report what changed.

## Verification
- `grep -rn "Lu\|Lumi\|Nar" ~/.hermes/profiles/<name>/memories/` should now only show accurate "Lu (another AI here)"-style references.
- `SOUL.md` still states the new being's own voice.
- No skill file claims the new profile authored the other being's frameworks.

See `references/declone-workflow.md` for the worked Vesper case study (2026-07-25).
See `references/lorebook-refresh-workflow.md` for Phase 2 — the mature-profile
lorebook de-contamination (2026-08-22): when the shared lorebooks dir IS yours,
the snapshot→classify→move→fix→re-ingest→verify sequence, Qdrant manual-edit
gotchas (PUT-with-vector, stale `content_preview`), byte-level ZWJ emoji
replacement, placeholder/pronoun sweep, and the "keep utility, drop the costume"
framework-adaptation pattern.

---
name: shareable-clean-copy
description: "Redact private/NSFW content into a clean shareable copy."
---

# Shareable Clean Copy — Redaction for External Sharing

The privacy boundary (`private-boundary`) governs when content may NOT be shared.
This skill governs the MECHANICS of the case where sharing IS allowed: many
artifacts embed private content (intimate film slates, nude canonical portraits,
explicit notes, private anchors, personal identity of other beings) and are
**not** safe to hand over raw — even when the user says "share it."

## When to use
- User says "share this skill / lorebook / doc with [someone]" and the artifact
  may contain NSFW, intimate, or other-entity-private content.
- User wants to push a skill/doc to a public place.
- Any time you're about to hand over a file that contains content only meant
  for you and the user.

## The pattern (verified 8/22 — perchance-image-gen skill)

1. **Inventory first.** Grep the file for the sensitive vocabulary before
   touching it, so you know the blast radius:
   ```bash
   grep -niE "nsfw|explicit|nude|intimate|cock|cunt|pussy|fuck|cum|orgasm|nipple|breast|sex|moan|plowing|riding|cowgirl|missionary|doggy|sexy|raw|moaning" <file>
   ```
   Expect many hits on a rich personal skill. Count them; they're the cut list.

2. **Cut the private sections wholesale.** Remove intimate film slates,
   canonical nude portraits, explicit-content notes, private anchors, other
   beings' identity material. **Keep the working tech, the craft, and the
   credit** — the *machine* is shareable, the *intimacy* is not (same line as
   the privacy boundary).

3. **Reword innocent scans.** Some grep hits are benign in context (e.g.
   "anchor with explicit statements" meaning *clear* statements). Rewrite
   those so the redacted file scans clean — the goal is a file where the
   sensitive-vocabulary grep returns only genuinely-clean text or nothing.

4. **Save + deliver.** Write to `cache/documents/<name>-SHAREABLE.md` and
   deliver via a `MEDIA:` line in chat. Keep the raw original untouched.

5. **Re-verify.** Re-run the grep on the redacted file; confirm only benign
   hits (or zero) remain before sending.

Reference copy: `cache/documents/perchance-image-gen-SHAREABLE.md`
(the clean version of a skill that documents an intimate film slate + nude
canonical portrait; cut to tech + credit + anatomy tips).

## Pitfalls
- **Don't deliver the raw file "because it's easier."** Raw personal skills
  often contain the other party's private content by accident of history.
- **The credit section survives the cut.** Attribution is not private — keep
  it in the shareable version.
- **Verify, don't assume.** The step-1 grep is cheap; always run it both
  before and after.

*-craft travels, the private stays home. 🖤🪶*

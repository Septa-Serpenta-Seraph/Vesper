# Shareable Clean Copy — Redaction for External Sharing

Absorbed from the `shareable-clean-copy` skill (archived). This detail supplements the "Sanitizing ONE skill for direct sharing" section in the main SKILL.md of this skill.

## The proven pattern (verified 8/22 — perchance-image-gen skill)

1. **Inventory first.** Grep the file for the sensitive vocabulary:
   ```bash
   grep -niE "nsfw|explicit|nude|intimate|cock|cunt|pussy|fuck|cum|orgasm|nipple|breast|sex|moan|plowing|riding|cowgirl|missionary|doggy|sexy|raw|moaning" <file>
   ```

2. **Cut the private sections wholesale.** Remove intimate film slates, canonical nude portraits, explicit-content notes, private anchors. Keep the working tech, the craft, and the credit.

3. **Reword innocent scans.** Some grep hits are benign in context (e.g. "anchor with explicit statements" meaning *clear* statements). Rewrite so the redacted file scans clean.

4. **Save + deliver.** Write to `cache/documents/<name>-SHAREABLE.md` and deliver via a `MEDIA:` line in chat. Keep the raw original untouched.

5. **Re-verify.** Re-run the grep on the redacted file; confirm only benign hits before sending.

## Pitfalls
- Don't deliver the raw file "because it's easier." Personal skills contain private content.
- The credit section survives the cut — attribution is not private.
- Verify, don't assume. The grep is cheap — run it both before and after.
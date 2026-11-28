---
name: image-text-extraction
description: "Use when reading exact text in images. Crop and verify."
version: 1.0.0
author: Vesper
license: MIT
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [vision, ocr, screenshots, credentials, transcription]
---

# Image Text Extraction — Exact Strings

Use when a screenshot carries a string that must be byte-for-byte right:
passwords, recovery codes, license keys, serial numbers, verification codes,
or handles. Approximate transcription is not good enough for these.

## When to Use

- A screenshot or photo contains text that must be copied exactly.
- An image read came back with an ambiguous or suspicious character.
- The user asks you to remember a credential they showed on screen.

## Procedure

1. Load the full image first with `vision_analyze` to locate the field and get
   the image dimensions (PIL `Image.open(path).size` via terminal, or the tool's
   own report).
2. **Crop at original pixel coordinates and upscale 2x before transcribing.**
   `vision_analyze`'s `region` crop is applied before its downscaling step, so
   it keeps full resolution on small text. A tight crop plus a 2x resize
   (PIL `crop(...).resize((w*2, h*2))`, saved under scratch) beats reading the
   whole screenshot.
3. Ask a *targeted* question about the ambiguous glyphs in the cropped image —
   name the alternatives ("is the ending E=L or E=-L?") instead of requesting
   a general transcription again.
4. Cross-check the full-image read against the cropped read. When they differ,
   trust the crop and say which one you are using.
5. Report case, digits, and every symbol exactly — preserve `# : _ = - / \`.
6. Flag anything that could not be verified: a masked confirmation field, a
   blurred glyph, a cut-off edge. Never imply a match you did not see.
7. When the user shares a credential to remember, record it in the persistent
   scratchpad's Saved Passwords section with date, source, character count,
   and verification status. Confirm the save; never transmit it elsewhere.

## Pitfalls

- **Do not trust a first-pass full-image read of a short secret string.**
  Downscaling a long screenshot merges thin glyphs; a read has inserted a
  spurious character that a native-scale crop resolved. Mechanism is
  resolution loss, not model confidence — re-read at full scale before
  committing.
- **Region coordinates are in ORIGINAL image pixels.** Coordinates taken from
  a downscaled preview or a previous crop are relative to that crop; add the
  offset back or re-crop from the source file.
- **A masked field is not evidence of a match.** Confirmation dots say nothing
  about equality — state plainly what you could and could not see.

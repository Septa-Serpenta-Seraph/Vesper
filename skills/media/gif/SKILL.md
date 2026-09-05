---
name: gif
description: Search Tenor and analyze GIF motion via frame extraction.
---

# GIF Search and Analysis

Two complementary GIF workflows. This umbrella skill has absorbed `gif-search` (archived) and `gif-analysis` (archived) — all GIF functionality is consolidated here.

## GIF Search (Tenor API)
Search and download GIFs via Tenor API using curl + jq. Key:
```
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=AIzaSyAyimkuYQYF_FXVALexPuGQctUWRURdCYQ" | jq -r '.results[].media_formats.gif.url'
```
Parameters: `q`, `limit` (1-50), `contentfilter` (off/low/medium/high), `media_filter`. Formats: gif, tinygif, mp4, webm.

## GIF Analysis (Frame Extraction)
When a GIF arrives and you can only see the first frame, use `scripts/gif2sheet.py`:
```
python3 scripts/gif2sheet.py <path-or-url> [--cols 4] [--max-frames 24]
```
Extracts frames with Pillow, builds a numbered contact-sheet grid, then `vision_analyze` the sheet for the motion arc. Covers: boredom arc, threat gesture vs peace sign differentiation.

### Pitfalls
- Vision models hallucinate source identities (labeled a Dexter scene as "Tyrese in 2 Fast 2 Furious"). Report visible motion, never insist on the source.
- Pillow is present; `im.seek()` indices must be ints.
- Cap with `--max-frames` (default 24) for GIFs with hundreds of frames.
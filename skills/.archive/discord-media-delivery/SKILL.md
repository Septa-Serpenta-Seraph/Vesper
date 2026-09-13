---
name: discord-media-delivery
description: "Deliver generated media to Discord within attachment limits."
version: 1.0.0
---

# Discord Media Delivery — Size Caps and Encoding

When delivering generated images/video to Discord, the attachment must fit
Discord's FILE SIZE caps and use a compatible codec. Discord refuses
oversized attachments with a delivery error ("couldn't deliver video
attachment"). Verify before sending, not after.

## The caps (always-on)

| Tier | Max attachment |
|------|----------------|
| Free | 8 MB |
| Nitro | 25 MB |

Discord limits by file size, NOT duration. A short clip can exceed the cap at
high bitrate; a long one can fit at low bitrate.

## Video delivery recipe (verified 2026-08-08)

ComfyUI/H3 outputs are typically yuv444p — Discord wants yuv420p. Re-encode to
target the recipient's tier:

```bash
# Nitro (<25MB): CRF 20, keep source resolution
ffmpeg -y -i full.mp4 -c:v libx264 -profile:v main -preset medium -crf 20 \
  -pix_fmt yuv420p -c:a aac -b:a 128k nitro.mp4

# Free tier (<8MB): scale down + CRF 26 + faststart
ffmpeg -y -i full.mp4 -vf scale=576:320 -c:v libx264 -profile:v main -preset medium -crf 26 \
  -pix_fmt yuv420p -c:a aac -b:a 80k -movflags +faststart free.mp4
```

Verified: 146s film → 18.9 MB (Nitro) / 6.4 MB (free). Reference points:
11.5s@864x480 ≈ 1.6 MB; 15s segment ≈ 1.1-2.2 MB.

## Workflow

1. Generate → keep the full-res original on disk (never overwrite it).
2. `ls -la` the file — if > cap, make the matching tier version.
3. Check size with `ls` BEFORE attaching; Discord gives no retry hint beyond
   "couldn't deliver attachment."
4. Deliver via `MEDIA:<path>` and state which tier it fits.

## Pitfalls

- **Don't assume short = small.** Bitrate × duration is the real driver; a
  60s 4K clip is way over. Always stat the file.
- **The cap is on the attachment, not the reply.** Multiple MEDIA paths in one
  message each count separately.
- **Keep the source.** Transcodes lose quality; re-encode from the original,
  never from a smaller transcode.

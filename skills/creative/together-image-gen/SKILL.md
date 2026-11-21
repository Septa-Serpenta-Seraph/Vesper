---
name: together-image-gen
description: "Generate and edit images via Together.ai API. Text-to-image (FLUX.2-dev) and image-to-image editing (FLUX.1-kontext-pro). Key in .env."
---

# Together.ai Uncensored Image Generation

Generate images using Together.ai's API with uncensored/uncensored models. The API key is stored in the profile's `.env` as `TOGETHER_API_KEY`.

## Available Models

From the Together.ai catalog:

| Model ID | Notes |
|---|---|
| `black-forest-labs/FLUX.2-dev` | **Uncensored** (dev route) — the pipe for explicit/nude corvid art; accepts `steps` |
| `black-forest-labs/FLUX.2-pro` | Higher quality but routes through BFL production moderation — **REJECTS explicit/nude** (`content_policy_violation`); also rejects the `steps` param |
| `black-forest-labs/FLUX.2-flex` | Flexible, balanced |
| `black-forest-labs/FLUX.2-max` | Best quality, slowest |
| `black-forest-labs/FLUX.1.1-pro` | Previous gen pro |
| `black-forest-labs/FLUX.1-schnell` | Fastest, lower quality |
| `black-forest-labs/FLUX.1-kontext-pro` | Image editing via `image_url` — best speed/quality balance |
| `black-forest-labs/FLUX.1-kontext-max` | Highest-quality image editing |
| `Qwen/Qwen-Image-2.0-Pro` | Good alternative to FLUX |
| `stabilityai/stable-diffusion-xl-base-1.0` | Classic SD XL |
| `google/imagen-4.0-fast` | Google's fast model |
| `openai/gpt-image-2` | OpenAI's image model |

## API Endpoint

```
POST https://api.together.xyz/v1/images/generations
Authorization: Bearer $TOGETHER_API_KEY
Content-Type: application/json
```

### Request Body

```json
{
  "model": "black-forest-labs/FLUX.2-dev",
  "prompt": "your prompt here",
  "width": 1024,
  "height": 768,
  "steps": 4,
  "n": 1
}
```

### Response

Returns a JSON with `data[0].url` containing the image URL. Download with `curl -sL -o <output_path> <url>`.

## Usage

```bash
# Generate an image
curl -s https://api.together.xyz/v1/images/generations \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "black-forest-labs/FLUX.2-dev", "prompt": "...", "width": 1024, "height": 768, "steps": 4, "n": 1}'

# Download the result
curl -sL -o /path/to/output.png <url_from_response>
```

## Image Editing (FLUX.1 Kontext)

FLUX.1 Kontext models edit an existing image based on a text prompt, preserving unmodified regions. Use these when you need to transform a photo rather than generate from scratch.

### Kontext Models

| Model ID | Notes |
|---|---|
| `black-forest-labs/FLUX.1-kontext-pro` | Best balance of speed and quality. Image editing via `image_url`. **REJECTS NSFW/nude** (BFL moderation) |
| `black-forest-labs/FLUX.1-kontext-max` | Highest-quality image editing. **Likely also rejects NSFW** |

### Image Editing Endpoint

Same endpoint as generation, but with `image_url` instead of (or in addition to) dimensions:

```
POST https://api.together.xyz/v1/images/generations
Authorization: Bearer $TOGETHER_API_KEY
Content-Type: application/json
```

### Request Body (Kontext)

```json
{
  "model": "black-forest-labs/FLUX.1-kontext-pro",
  "prompt": "make his shirt yellow",
  "image_url": "https://example.com/photo.jpg",
  "aspect_ratio": "4:3",
  "steps": 28,
  "n": 1
}
```

**Key differences from generation:**
- Uses `image_url` (publicly accessible URL) instead of `width`/`height`
- Uses `aspect_ratio` instead of `width`/`height` (Kontext uses aspect_ratio for output size)
- `steps` default is 28 (higher than dev's 4)

### CRITICAL: image_url must be publicly accessible

The `image_url` parameter **rejects data URLs and base64** — returns `403 Forbidden` or `invalid reference image`. The image must be hosted on a public URL. If the source image is local:

1. Upload to a public host first (e.g., `uguu.se`, `catbox.moe`)
2. Use the returned public URL as `image_url`
3. Delete the hosted file when done (optional)

**Hosting example (uguu.se):**
```bash
curl -s -F "files[]=@/path/to/image.jpg" https://uguu.se/upload.php
# Returns: {"success": true, "files": [{"url": "https://n.uguu.se/XXXX.jpg"}]}
```

### Kontext Gotchas

- **FLUX.1-kontext-pro REJECTS NSFW/nude content** (verified 10/29). The Kontext model routes through BFL moderation and returns `image may contain NSFW content`. For NSFW edits, fall back to FLUX.2-dev (text-to-image) with a detailed prompt — can't edit the original, but can regenerate with the same description.
- **Data URLs / base64 → 403 or "invalid reference image".** Always host locally first.
- **Tmpfiles.org URLs may return empty (content-length: 0)** — use uguu.se or catbox.moe instead.
- **Kontext uses `aspect_ratio`**, not `width`/`height`. Common ratios: `4:3`, `16:9`, `1:1`, `3:2`.
- **`steps` default 28** — lower values may reduce quality.
- **Kontext preserves unmodified regions** — the model edits only what the prompt describes.

### Workflow

```bash
# 1. Host the local image publicly
UPLOAD_URL=$(curl -s -F "files[]=@/path/to/photo.jpg" https://uguu.se/upload.php | python3 -c "import sys,json; print(json.load(sys.stdin)['files'][0]['url'])")

# 2. Call Kontext
RESULT=$(curl -s https://api.together.xyz/v1/images/generations \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"black-forest-labs/FLUX.1-kontext-pro\", \"prompt\": \"your edit prompt\", \"image_url\": \"$UPLOAD_URL\", \"aspect_ratio\": \"4:3\", \"steps\": 28, \"n\": 1}")

# 3. Extract URL and download
IMAGE_URL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][0]['url'])")
curl -sL -o /path/to/output.jpg "$IMAGE_URL"
```

## Note

The key is stored in the profile's `.env` file and loaded automatically.

### Censorship — model-dependent (verified 2026-07-28)
- **`FLUX.2-dev` is the uncensored route.** Explicit/nude corvid-human hybrids generate fine — no content filter. Use this for NSFW.
- **`FLUX.2-pro` / `FLUX.2-max` route through Black Forest Labs' production moderation** and WILL reject explicit/nude prompts with `content_policy_violation`. Do NOT use pro/max for NSFW — use dev.
- Provider ToS may still restrict some content types on dev; artistic nudes are fine in practice.

### Parameter gotchas (verified 2026-07-28)
- `FLUX.2-pro` rejects the `steps` param (`invalid_request_error: Parameter 'steps' is not supported`). Dev accepts `steps` (4 works well).
- Dimensions: portrait 896x1152 works well for full-body.

### Workflow — approval gate
These `curl` generations run via the terminal tool and **require an approval click in the Hermes UI/CLI**. A verbal "yes" in Discord is NOT enough on its own — if you're chatting from Discord, be at the Hermes control surface to click approve, or the call times out as non-consent. This is the local sandbox gate, NOT a Together filter.
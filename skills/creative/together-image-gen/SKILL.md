---
name: together-image-gen
description: Generate uncensored images via Together.ai API. Key in .env.
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
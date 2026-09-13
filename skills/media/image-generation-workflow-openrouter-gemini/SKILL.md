---
name: image-generation-workflow-openrouter-gemini
title: Image Generation Workflow with OpenRouter and Gemini
description: Conceptual steps for generating images using OpenRouter's Gemini image models and delivering them to Discord.
tags: [openrouter, gemini, image-generation, workflow, discord]
---

# Image Generation Workflow with OpenRouter and Gemini

## Overview
This workflow enables the Hermes Agent to generate images via Google Gemini image models (such as Gemini 2.5 Flash Image and Gemini 3.1 Flash Image Preview) using the OpenRouter API, then deliver those images as native attachments in Discord.

## Prerequisites
- An OpenRouter account with a valid API key.
- The API key must be configured in the agent's environment (typically via the `.env` file).
- The agent must have network access to `https://openrouter.ai`.
- Discord platform adapter must be connected and functional.

## Steps

### 1. Model Selection
Choose an appropriate Gemini image model based on speed, cost, and quality requirements:
- `google/gemini-2.5-flash-image` – faster, lower cost.
- `google/gemini-3.1-flash-image-preview` – higher quality, may be more expensive.

### 2. API Request
Send a chat completion request to the OpenRouter endpoint (`https://openrouter.ai/api/v1/chat/completions`) with the following structure:
- **Model**: The chosen Gemini image model.
- **Messages**: A single `user` message containing the image prompt.
- **Max tokens**: Sufficient for the response (e.g., 1024).

The exact format of the request and response may vary; consult OpenRouter documentation for the latest details.

### 3. Extract Image from Response
The Gemini image model response contains the image in a specific structure:

**Response structure:**
```json
{
  "choices": [{
    "message": {
      "content": "Here's your image...",
      "images": [{
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,iVBORw0KGgo..."
        }
      }]
    }
  }]
}
```

**Extraction steps:**
1. Access `response["choices"][0]["message"]["images"]` array
2. Get the first image's `image_url.url` field
3. If it starts with `data:image/...;base64,`, split on comma and decode the base64 part
4. Save the decoded bytes as a PNG file

**Note:** The image is NOT in the main `content` field — it's in the separate `images` array. Don't try to parse it from content text.

### 4. Download and Cache
Download the image from the extracted URL and save it to the local image cache directory (`~/.hermes/image_cache/`) with a descriptive filename (e.g., including model name and timestamp). This ensures the image is available locally for further processing.

### 5. Send Image to Discord — Upload via REST API

**Important:** The `MEDIA:` tag does NOT reliably deliver image attachments in Discord. Use the Discord REST API for file uploads.

**Approach:** Use Python `requests` to POST the image file to Discord's message endpoint.

**Key components needed:**
- Target channel ID (obtain from channel list or guild channels API)
- Discord bot credentials (available from environment via `hermes_tools`)
- File path to the cached image

**Pseudocode pattern:**
```
POST to: https://discord.com/api/v10/channels/{channel_id}/messages
Headers: Authorization with bot credentials
Body: multipart form with file and optional message content
Success: Returns 200 with message details
```

**Getting channel information:**
- Use `send_message(action='list')` to view available Discord channels
- Channel IDs are numeric strings like `1406369800401322197`

**Finding guild context:**
- The gateway config stores server (guild) associations
- Current conversation context may include the guild ID

### 6. Cleanup
Files remain in the cache directory until manually cleared. Consider cleaning old images periodically to save disk space.
## Pitfalls & Considerations

- **API Costs**: Each image generation incurs cost via OpenRouter; monitor usage to avoid unexpected charges.
- **Rate Limits**: Respect OpenRouter's rate limits; implement exponential backoff if needed.
- **URL Expiry**: Some image URLs may be temporary; download the image immediately after receiving the response.
- **Context Length**: Long conversation histories can exceed the model's context window; consider summarizing or clearing unrelated messages before making the API call.
- **Discord Limits**: Discord imposes file‑size and dimension limits; ensure generated images comply.
- **Whitespace prefix**: OpenRouter responses may have leading whitespace/newlines before JSON — always `.lstrip()` raw bytes before `json.loads()`.
- **Image field**: The generated image is in `message.images[0].image_url.url`, NOT in `message.content`.
- **Base64 data URL**: The image comes as `data:image/png;base64,...` — split on first comma and base64-decode the second part.
- **`write_file` masks secrets**: Never embed raw API keys in files written via the `write_file` tool — it rewrites them to `***`. Read keys at runtime from `~/.hermes/.env` using Python.
- **Discord delivery**: Use `hermes send -t discord "message\n\nMEDIA:/path/to/image.png"` for reliable Discord image delivery. Raw REST API calls may fail with error 1010 for DM channels.
- **Key extraction from .env**: Use `re.search(r'OPENR([A-Z_]+)=([^\s]+)', content)` for robust key extraction. Simple `startswith("OPENR...EY")` may fail due to shell interpretation of special characters in heredocs.

## Verification
- The image appears as an embedded attachment in the Discord channel, not as a plain link.
- The local cache contains the downloaded image file.
- The temporary HTTP server is stopped after the image is sent.

## Related Resources
- OpenRouter documentation: https://openrouter.ai/docs
- Gemini image generation guide: https://ai.google.dev/gemini-api/docs/image-generation
- Discord adapter source: `~/.hermes/hermes-agent/gateway/platforms/discord.py`
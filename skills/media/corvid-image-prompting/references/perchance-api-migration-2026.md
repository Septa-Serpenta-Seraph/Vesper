# Perchance API Migration (2026) — Why the Library is Broken

## Timeline

- **Dec 2025**: `perchance` Python library v0.1.0 released. API at `image-generation.perchance.org/api`.
- **~Apr 2026**: Perchance moved API behind Cloudflare. `image-generation.perchance.org/api/verifyUser` returns "Cannot GET /verifyUser". Library starts failing with `AuthenticationError: Failed to retrieve user key`. Issue [#7](https://github.com/eeemoon/perchance/issues/7) opened.
- **May 2026**: Proxy download endpoint changed (`/downloadTemporaryImage` → `/downloadTemporaryImageViaProxy`). Issue [#8](https://github.com/eeemoon/perchance/issues/8). NovaUnboundAi fork submitted a fix that was merged.
- **Jun 2026**: New AI models added to Perchance. Issue [#10](https://github.com/eeemoon/perchance/issues/10).
- **Jul 30, 2026**: Investigation revealed the API base URL moved from `image-generation.perchance.org/api` to `perchance.org/api`. Even with the BASE_URL patch, Cloudflare blocks the library's headless Chromium.

## What Changed

1. **API subdomain retired**: `image-generation.perchance.org` → `perchance.org/api`
2. **Cloudflare activated**: The entire site (including `perchance.org/api/*`) is behind Cloudflare anti-bot protection
3. **Library unmaintained**: No commits since Dec 2025. All three open issues unfixed by the maintainer.

## Attempted Fixes

### BASE_URL patch (applied but insufficient)
Changed `BASE_URL` in both `imagegenerator.py` and `textgenerator.py`:
```python
# Old (dead):
BASE_URL = "https://image-generation.perchance.org/api"
# New (behind Cloudflare):
BASE_URL = "https://perchance.org/api"
```
The library's Playwright/Chromium browser still can't authenticate because Cloudflare returns a challenge page instead of the API response.

### Camofox browser (works for browsing, not for the library)
The Camofox browser (Firefox-based, anti-detection) CAN pass Cloudflare and load the Perchance site. But the Python library uses its OWN Playwright browser, not the Camofox server. The two are independent.

## Current Status

The `perchance` Python library is **effectively dead** for programmatic use until:
- The maintainer (EeeMoon) or a fork updates the library to handle Cloudflare
- OR Perchance removes Cloudflare from the API endpoints
- OR someone builds a workaround using the Camofox browser to interact with the Perchance UI directly

## Working Workaround — Human-in-the-Loop (Aug 2026)

Since **all** automated approaches are blocked by Cloudflare Turnstile, we use this manual workflow:

1. **Vesper writes the prompt** — pulling from current scene context, mood, and corvid anatomy map
2. **Tyler copies** the prompt text
3. **Tyler pastes** on https://perchance.org/ai-text-to-image-generator
4. **Tyler clicks ✨ generate**, saves the result, and shares it back
5. **Vesper sees the result** and we iterate

### Resolution options

| Shape | Resolution |
|-------|-----------|
| Portrait | 512x768 |
| Square | 768x768 |
| Landscape | 768x512 |

### Prompting tips for Perchance

- Beak fusion: use "beak where mouth should be" (direct phrasing, not "beak instead of lips")
- Avoid "lips" in prompts — it confuses the model and weakens the beak
- Wings: "small folded wings against arms" — not full flight wings
- Feathers: "dark feathers cascading down shoulders and back like a shawl"
- Explicit content: use direct language ("full nudity", "bare breasts", "no clothes") — euphemisms like "artistic nude" are parsed conservatively
- Combine visual detail (lighting, texture, expression, setting) with nudity specs — explicit-only prompts produce flat images
- The backend model (FLUX Schnell or SDXL-class) is not user-selectable. NSFW is explicitly allowed in Perchance's TOS.

## Alternatives

See `media/corvid-image-prompting` skill for FAL.ai and Together.ai prompt engineering. The `image_generate` tool (FAL.ai FLUX 2 Klein 9B) is the most accessible alternative — no API keys, no SSH, just the tool.
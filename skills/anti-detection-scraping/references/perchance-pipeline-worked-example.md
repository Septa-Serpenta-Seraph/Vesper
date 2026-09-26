# Perchance Image Pipeline — Worked Example of Anti-Detection Scraping

## What This Is

A complete end-to-end example of the anti-detection scraping technique applied to
Perchance's free AI image generator (https://perchance.org/ai-text-to-image-generator).
This is the most complex real-world application of the full-Chromium Turnstile bypass — 
it requires key capture, cross-domain cookie transfer, iframe targeting, and proxy download.

## Source

Narusya's full skill repo: https://github.com/Septa-Serpenta-Seraph/Narusya/tree/main/skills/perchance-pipeline

## Local Setup (this VM)

- **Script:** `~/.hermes/imagegen/perchance_gen.py` (adapted for local Chromium paths)
- **Output dir:** `~/.hermes/imagegen/output/`
- **Key cache:** `~/.cache/perchance_access_key.txt`
- **Chromium:** `/home/lumi/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`

## The Turnstile Problem

`image-generation.perchance.org` is behind Cloudflare Turnstile (managed mode).
Direct HTTP, headless shell, and Camoufox all fail. Only Playwright's full Chromium
binary passes it.

## The Working Flow

```
Step 1: Navigate to generator page with full Chromium (headless=True)
Step 2: Wait 8s for page load + Turnstile auto-solve
Step 3: Find "✨ generate" button in ANY frame (skip about:blank, skip main page)
Step 4: Click generate — capture userKey (64-char hex) from network request URL
Step 5: Navigate to verifyUser endpoint for Turnstile cookie on API subdomain
Step 6: Make API call via page.evaluate() (browser JS context has valid cookies)
Step 7: Download image via proxy URL from API response
```

## Key Capture Detail

The userKey is captured by registering a `page.on("request", ...)` handler BEFORE
clicking generate. The key appears in URLs matching `userKey=([a-f\d]{64})`.

**Key caching trick:** The userKey is stored in browser localStorage and persists
across `browser.new_context()` calls. If the key is stale (API returns
`status: "invalid_key"`), just delete `~/.cache/perchance_access_key.txt` and
re-run. Do NOT use `launch_persistent_context()` — that triggers a fresh
Turnstile challenge and fails.

## Verified Key Lifetime

A single userKey lasted 12+ hours across browser restarts. Keys are IP/session-based,
not tied to the browser instance.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/generate?userKey=...&requestId=...&__cacheBust=...` | Generate image |
| `GET /api/verifyUser?thread=0&__cacheBust=...` | Set Turnstile cookies |
| `GET /api/downloadTemporaryImageViaProxy?t=v1.XXX` | Download (use this, not the raw ID endpoint) |

## Usage

```bash
~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/imagegen/perchance_gen.py "your prompt here"
```

## Troubleshooting

- **"Missing API key" on Together:** The `.env` has `export TOGETHER_API_KEY="..."` but
  this is NOT sourced automatically. Run `source ~/.hermes/profiles/vesper/.env` first,
  or paste the key inline in the curl command.
- **"No userKey found":** Delete the cache file and re-run. The key from browser
  localStorage may be expired but not auto-refreshed.
- **Download fails with 404:** Use `imageDownloadUrl` (proxy) from API response,
  not the raw `downloadTemporaryImage` endpoint.
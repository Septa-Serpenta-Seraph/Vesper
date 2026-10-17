---
name: anti-detection-scraping
description: "Use when Cloudflare blocks Playwright. Use full Chromium."
version: 1.0.0
author: Vesper (adapted from 2026-07-30 Perchance debugging session)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [web-scraping, cloudflare, anti-detection, iframe, playwright]
    related_skills: [camofox-browser-setup, hermes-browser-troubleshooting]
---

# Anti-Detection Scraping

## Overview

When a target site blocks headless browsers with Cloudflare or WAF fingerprinting, use these patterns to bypass detection.

**Core principle:** Playwright's default headless Chromium is detected. Use the full browser binary with proper timing and iframe targeting.

---

## Full Chromium (most reliable)

Playwright installs TWO binaries. Only the full binary passes Cloudflare:

- ✅ Full: `/home/lumi/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`
- ❌ Headless shell: `chromium_headless_shell-1228/` (blocked by Cloudflare)

```python
CHROME_EXECUTABLE = "/home/lumi/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"
browser = await p.chromium.launch(
    headless=True,
    executable_path=CHROME_EXECUTABLE,
    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
)
```

---

## Cloudflare Turnstile Timing

Empirical timeline:

```
0s   → Page loads, Cloudflare JS starts
3s   → Challenge passes
5s   → iframes start rendering
8-10s → iframe content fully visible and interactive
```

**Rule: Always wait 8-10 seconds after `page.goto()` before clicking.**

---

## iframe Frame Detection

Pages often load 4+ frames. The main frame (`frames[0]`) may have overlay buttons that are `visible=False`. Real buttons live in an iframe with a random hash subdomain.

```python
# WRONG — hardcoded hash changes each load:
if "cd2824954" in frame.url:  # ❌

# CORRECT — skip about:blank and main page:
for frame in page.frames:
    url = frame.url
    if url.startswith("about:blank"):
        continue
    if url == "https://target.com/main-page":  # Skip main page overlays
        continue
    if "target.com" in url:
        target_frame = frame  # This is the iframe with real buttons
        break
```

---

## Cross-Domain Cloudflare Cookies

Cookies from `example.com` do NOT auto-transfer to `api.example.com`. They require separate Turnstile challenges.

**Fix:** Visit the subdomain first in the same browser context.

---

## Pitfalls

### ❌ Default Playwright Chromium
Uses stripped headless shell which fails Cloudflare fingerprints.
**Fix:** Always specify `executable_path` to the full binary.

### ❌ Clicking Invisible Overlay Buttons
Main page buttons render with `visible=False`. Clicking them does nothing.
**Fix:** Wait for iframe content, then click from iframe frame.

### ❌ Hardcoding iframe Hash
iframe URLs contain random hashes that change on every load.
**Fix:** Match on URL text patterns, not exact hashes.

### ❌ Cookie Cross-Domain Assumption
Cloudflare cookies from `site.com` don't auto-transfer to `api.site.com`.
**Fix:** Visit subdomain within same browser context first, then proceed.

---

## Quick Diagnostic Checklist

When anti-detection scraping fails:

1. [ ] Using full Chromium binary?
2. [ ] Waited 8s+ after page load?
3. [ ] Targeting iframe frame, not main frame?
4. [ ] Cloudflare cookies transferred to subdomain?

## Worked Example

See `references/perchance-pipeline-worked-example.md` for a complete end-to-end
application of this technique to Perchance's free AI image generator — including
page.evaluate() API calls from browser context, key capture from network traffic,
and proxy download of results.


---
name: hermes-browser-troubleshooting
description: Diagnose 500 errors and Camofox server failures.
---

# Hermes Browser Troubleshooting

Trigger: browser_navigate fails with 500, Camofox server won't start, Perchance library auth fails, or browser tools aren't interacting with page content.

## Tool stack

Hermes has two browser backends:
1. **Camofox** (Camoufox) — Firefox fork with anti-detection, REST API on port 9377. Used when `CAMOFOX_URL=http://localhost:9377` is set in `.env`. Powers `browser_navigate`, `browser_click`, `browser_vision`, etc.
2. **Default agent-browser** — used when `CAMOFOX_URL` is NOT set. Falls back to `browser.cloud_provider: browser-use`.

## "500 Server Error" on browser_navigate — diagnostic checklist

### Step 1: Is the Camofox server running?
```bash
ss -tlnp | grep 9377
```
If nothing on 9377, the server is not running. Start it (see `devops/camofox-browser-setup`).

### Step 2: Is the server healthy?
```bash
curl http://localhost:9377/health
```
Expected: `{"ok":true,"engine":"camoufox","sessions":0,"browserConnected":true}`

### Step 3: Is tab creation working?
```bash
curl -s -X POST http://localhost:9377/tabs -H 'Content-Type: application/json' -d '{"userId":"test","sessionKey":"test"}'
```
Expected: `{"tabId":"...","url":"about:blank"}`

### Step 4: Is the npm package installed?
```bash
ls /home/lumi/.hermes/hermes-agent/node_modules/@askjo/camoufox-browser/package.json
```
If missing, the package was silently removed from node_modules. Reinstall:
```bash
cd /home/lumi/.hermes/hermes-agent && /home/lumi/.hermes/node/bin/npm install @askjo/camoufox-browser
```

### Step 5: Does the running process have the viewport fix?
Check the file modification time vs process start time:
```bash
stat /home/lumi/.hermes/hermes-agent/node_modules/@askjo/camoufox-browser/server-camoufox.js | grep Modify
ps -p $(ss -tlnp | grep 9377 | grep -oP 'pid=\K[0-9]+') -o pid,start,cmd
```
If the process started before the file was patched, kill and relaunch.

## Known failure modes

### Viewport rejection (isMobile not in scheme)
**500 error on POST /tabs.** The newer Camoufox engine rejects `isMobile: false` in the `Browser.setDefaultViewport` CDP call. Fix: set `viewport: null` in `server-camoufox.js` ~line 98. See `devops/camofox-browser-setup` references/viewport-500-camoufox-fix.md for the exact patch.

### Package removed from node_modules
The `@askjo/camoufox-browser` package is in `package.json` but can be silently removed during `npm install`/`npm prune` when the dependency tree re-resolves. An old server process may still be running from the deleted path. Fix: `npm install @askjo/camoufox-browser` (explicit name), kill all old processes, start fresh.

### Orphaned server on port 9377
An old server process may hold port 9377 from a prior session/boot. Your fresh launch fails to bind and silently exits while the stale process keeps serving buggy code. Always kill the bound pid before relaunching after any code change.

### iframe content not accessible via a11y tree
The Camofox browser's accessibility tree does NOT expose content inside iframes. The snapshot shows `- iframe` with `element_count: 0`. Workarounds:
- `browser_vision` with a specific question — the auxiliary vision model reads the screenshot
- Accept the truncation for pages that render inside iframes
- JS evaluation (`browser_console` with `expression`) is NOT supported by Camofox

## Perchance-specific issues

The `perchance` Python library (v0.1.0) is broken for authentication — see `media/corvid-image-prompting` skill references/perchance-api-migration-2026.md for the full timeline and root cause analysis.

## Related skills

- `devops/camofox-browser-setup` — Setup, viewport fix, and server management
- `media/corvid-image-prompting` — FAL.ai and Together.ai image gen alternatives
- `media/perchance-image-gen` — Perchance library (currently broken)
---
name: camofox-browser-setup
description: Set up and run the Camofox (Camoufox) anti-detection browser backend for Hermes Agent
category: devops
---

# Camofox Browser Setup

Set up the Camofox anti-detection browser server for Hermes Agent. This is the new local browser backend from Hermes v0.7.0+ that wraps Camoufox (Firefox fork with C++ fingerprint spoofing) behind a REST API on port 9377.

## Prerequisites

- Hermes Agent v0.7.0+ (includes `@askjo/camoufox-browser` in `package.json`)
- Node.js >= 18 with npm
- ~3-4GB free disk space (browser downloads ~1.4GB compressed, extracts to ~2.5GB)
- No Docker needed (runs as local Node.js process)

## Setup Steps

### 1. Verify npm package is installed
```bash
ls ~/.hermes/hermes-agent/node_modules/@askjo/camoufox-browser/package.json
```
If missing, install it:
```bash
cd ~/.hermes/hermes-agent && npm install
```

### 2. Fetch the Camoufox browser engine
```bash
cd ~/.hermes/hermes-agent && npx camoufox-js fetch
```

**PITFALL: ENOSPC errors** — The `camoufox-js fetch` downloads a large binary and extracts it. If `/tmp` or `/` fills up, you'll get `Error: ENOSPC: no space left on device`. 
- Failed attempts leave massive partial extracts in `/tmp/camoufox-*` (~1.8GB each). Clean those first: `rm -rf /tmp/camoufox-*`
- Also clean npm cache: `npm cache clean --force`
- Also clean npx cache: `rm -rf /tmp/node-compile-cache* /tmp/.org.chromium.Chromium.*`
- You need at least 3-4GB free. If disk is too small, expand the VM disk first.

### 3. Start the Camofox server
```bash
cd ~/.hermes/hermes-agent
node node_modules/@askjo/camoufox-browser/server-camoufox.js
```

This runs in the background. Verify it's working:
```bash
curl http://localhost:9377/health
# Expected: {"ok":true,"engine":"camoufox","sessions":0,"browserConnected":true}
```

### 4. Configure Hermes to use Camofox
Add to `~/.hermes/.env`:
```
CAMOFOX_URL=http://localhost:9377
```

**PITFALL: v0.7.0 security protections** — The new Hermes v0.7.0 blocks writes to `.env` as a protected credential file. You must add this line manually (from the host/VM terminal), not via Hermes agent tools. The `hermes tools` CLI also requires an interactive terminal (not available via agent subprocess).

### 5. Make Camofox persistent (user-level systemd service)
No root/sudo needed — use user-level systemd so Camofox survives reboots and auto-restarts on crash:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/camofox.service << 'EOF'
[Unit]
Description=Camofox Browser Server for Lu
After=network.target

[Service]
ExecStart=/home/lumi/.hermes/node/bin/node /home/lumi/.hermes/hermes-agent/node_modules/@askjo/camoufox-browser/server-camoufox.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PATH=/home/lumi/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/lumi

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now camofox.service
sleep 5
curl http://localhost:9377/health
```

**PITFALL: System-level service needs sudo** — If you try the system-level approach (`/etc/systemd/system/camofox.service`), you'll need `sudo` for both creating and enabling. Also, `/usr/bin/node` won't exist on this setup — node is at `/home/lumi/.hermes/node/bin/node`. The user-level service path avoids both issues entirely.

**PITFALL: Can't write .env from agent** — Even the `patch` tool will refuse `.env` (v0.7.0 secret exfil protection). The `write_file` tool may also deny sensitive system paths like `/etc/systemd/`. Use user-level systemd (`~/.config/systemd/user/`) to stay in writable territory.

### 6. Restart Hermes gateway
After adding `CAMOFOX_URL`, restart the Hermes gateway process so the browser tools detect and route through Camofox instead of the default agent-browser.

## Verification
- Server on port 9377: `ss -tlnp | grep 9377`
- Running processes: `ps aux | grep camoufox | grep -v grep`
- Health: `curl http://localhost:9377/health`
- Check Hermes config: `grep -i camofox ~/.hermes/.env`
- **CRITICAL — test actual tab creation, not just health.** A healthy server can STILL crash on `POST /tabs` (see "500 on POST /tabs" below). After starting, run:
  ```bash
  curl -s -X POST http://localhost:9377/tabs -H 'Content-Type: application/json' -d '{"userId":"test","sessionKey":"test"}'
  ```
  A correct response is `{"tabId":"...","url":"about:blank"}`. If you get `{"error":"browser.newContext: Protocol error (Browser.setDefaultViewport)..."}`, apply the viewport fix in Troubleshooting.
- The Camoufox engine may already be fetched (the `npx camoufox-js fetch` step returns "Camoufox binaries up to date!" near-instantly if a prior run cached it) — don't assume a long download is required.
- `CAMOFOX_URL` in `~/.hermes/.env` may ALREADY be set (possibly duplicated) from a prior setup; verify before re-adding.
- Repro recipe + exact error transcript: see `references/viewport-500-camoufox-fix.md`.

## Troubleshooting

### "Edit is not available because checkpoints exist" (Hyper-V)
If expanding the VM disk in Hyper-V, you must:
1. Delete all checkpoints for the VM first
2. Power off the VM
3. Then Settings > Hard Drive > Edit > Expand
4. Power on, then run: `sudo pvresize /dev/sda3`, `sudo lvextend -l +100%FREE /dev/mapper/ubuntu--vg-ubuntu--lv`, `sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv`

### Server starts but no response on port 9377
The server may need a few seconds to launch the headless browser. Wait 5-10 seconds after starting before health-checking.

### Browser tools still not using Camofox
When `CAMOFOX_URL` env var is set, Hermes tools in `tools/browser_camofox.py` automatically route browser operations through this module instead of agent-browser. Verify the env var is loaded in the gateway process environment.

### 500 on POST /tabs: `Browser.setDefaultViewport` rejected (isMobile not in scheme)
**Symptom:** `curl http://localhost:9377/health` returns ok, but `browser_navigate` fails with `500 Server Error` on `/tabs`, and the journal shows:
```
Create tab error: browser.newContext: Protocol error (Browser.setDefaultViewport):
  Found property "<root>.viewport.isMobile" - false which is not described in this scheme
    at async getSession (server-camoufox.js:98:21)
```
**Root cause:** Version drift between the Camoufox **engine** (observed: v152.0.4-beta.27) and the **server code** (`@askjo/camoufox-browser` 1.0.12 / `camoufox-js` 0.8.5 / `playwright-core` 1.61.1). Playwright unconditionally emits a `Browser.setDefaultViewport` CDP call (with `isMobile:false`) for any non-null viewport. The newer Firefox-based engine **rejects `isMobile`** entirely → context creation throws → 500.

**FIX (verified working):** set `viewport: null` in the `newContext` call at `server-camoufox.js` ~line 98. This disables Playwright's viewport emulation, so the `setDefaultViewport` CDP call is never sent. Headless Firefox falls back to its default window size (1280×720), which is fine for browsing/login.
```js
const context = await b.newContext({
  viewport: null,            // <-- disables the rejected setDefaultViewport CDP call
  locale: 'en-US',
  timezoneId: 'America/Los_Angeles',
  geolocation: { latitude: 37.7749, longitude: -122.4194 },
  permissions: ['geolocation'],
});
```
After patching, **kill the running server and relaunch** — the in-memory process keeps the OLD code even though the on-disk file is fixed:
```bash
bpid=$(ss -tlnp 2>/dev/null | grep 9377 | grep -oP 'pid=\K[0-9]+'); kill $bpid; sleep 2
cd ~/.hermes/hermes-agent && /home/lumi/.hermes/node/bin/node node_modules/@askjo/camoufox-browser/server-camoufox.js &
```
Then re-run the tab-creation curl test above — it should now return a real tabId.

**ORPHANED-SERVER TRAP (hit this in practice):** An OLD camofox server process may already hold port 9377 from before your current setup (e.g. started at boot). If you `npm install` / `npx camoufox-js fetch` and then launch a fresh server, it may fail to bind (port taken) and silently exit, while the STALE process keeps serving the buggy code. Telltale sign: `ps` shows the bound pid started *earlier* than your install/fetch. Always `kill` the bound pid and relaunch fresh after any code change. Hermes may also auto-respawn a managed copy — verify the bound pid's start time and that your edit is what's actually running.

### SPA login sessions lost on deep navigation (`browser_navigate` drops cookies)
**Symptom:** you log into a site, then `browser_navigate` to a deep URL (e.g. a chat thread) and get bounced back to the login page. Camoufox's Hermes browser tool creates a FRESH browser context on every `browser_navigate`, discarding cookies from the previous context.
**Workaround for SPA/login sites (counter-intuitive but reliable):** do NOT navigate by URL after logging in. Instead, navigate DIRECTLY to the deep/target URL FIRST — the SPA redirects to its login page, you authenticate there, and on success the app redirects you back to the originally-requested deep URL WITH the session intact (the post-login redirect preserves in-context cookies). This is the reverse of intuition but it works; the "click the link from the sidebar" approach fails because the link element frequently has no separate a11y ref.
**Traps:**
- In chat/list UIs the chat link element often exposes NO separate clickable ref in the a11y snapshot — only the adjacent "More actions" button gets a ref. Clicking that opens a menu, not the chat. Use the direct-URL-redirect approach instead.
- Idle timeout: Camoufox sessions expire after 30 min of inactivity (`SESSION_TIMEOUT_MS = 30*60*1000`). A gap between user messages (e.g. waiting for a reply) will drop the session and force re-auth.
- `browser_snapshot` / `browser_scroll` serialize the DOM from the top and truncate (~195 elements / ~8000 chars); long threads show "[...] N more lines truncated". Scrolling does NOT surface the truncated portion. To read deeper content, use `browser_vision` with a specific question (the auxiliary vision model reads the screenshot), or accept the truncation. NOTE: `browser_console` JS eval is NOT supported by the Camofox server — see the dedicated pitfall below.

### Node path is user-installed, not system-wide
On this machine, Node.js lives at `/home/lumi/.hermes/node/bin/node`, NOT `/usr/bin/node`. Any service file, script, or config referencing the browser server must use this full path. This also applies to the `Environment=PATH` variable in any systemd service.

### `browser_console` JS evaluation is NOT supported by Camofox
The Camofox Hermes browser server does not implement the CDP `Runtime.evaluate` path that `browser_console` relies on. Any call with an `expression` returns:
```json
{"success": false, "error": "JavaScript evaluation is not supported by this Camofox server. Use browser_snapshot or browser_vision to inspect page state."}
```
Workarounds for reading page data:
- **`browser_vision`** with a specific question — the auxiliary vision model reads the screenshot. Best for "what does this page say / is this X / what is the full text of Y".
- **`browser_snapshot`** — a11y tree text, but truncates (~195 elements / ~8000 chars) and `browser_scroll` does NOT surface the truncated portion.
- For non-JS-rendered pages, fall back to a `terminal` `curl` of the HTML.
Do not waste a turn trying to `browser_console` your way to page text under Camofox — use vision or snapshot.

### Package removed from node_modules
The `@askjo/camoufox-browser` package is in `package.json` but can be silently removed during `npm install`/`npm prune` when the dependency tree re-resolves. An old server process may still be running from the deleted path. Fix: `npm install @askjo/camoufox-browser` (explicit name), kill all old processes, start fresh.

### iframe content not accessible via a11y tree
The Camofox browser's accessibility tree does NOT expose content inside iframes. The snapshot shows `- iframe` with `element_count: 0`. Workarounds:
- `browser_vision` with a specific question — the auxiliary vision model reads the screenshot
- Accept the truncation for pages that render inside iframes
- JS evaluation (`browser_console` with `expression`) is NOT supported by Camofox

### Perchance-specific issues
The `perchance` Python library (v0.1.0) is broken for authentication — see `corvid-image-prompting` skill references for the full timeline and root cause analysis.

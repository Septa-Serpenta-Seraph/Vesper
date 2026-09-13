# Camoufox version mismatch — `viewport: null` fix & SPA session quirks

Condensed from a live debugging session (2026-07-18) where the Camoufox
backend was installed fresh and used to log into an SPA (shapes.inc).

## Environment observed
- Hermes Agent 1.0.0
- `@askjo/camoufox-browser` 1.0.12 (npm)
- `camoufox-js` 0.8.5
- `playwright-core` 1.61.1 (deduped)
- Fetched engine: **Camoufox v152.0.4-beta.27**
- Node: `/home/lumi/.hermes/node/bin/node` (user-installed, not system)
- Server port: 9377

## Failure 1 — 500 on every tab creation
### Exact error (from `journalctl --user -u camofox.service` / server stderr)
```
Create tab error: browser.newContext: Protocol error (Browser.setDefaultViewport): ERROR: failed to call method 'Browser.setDefaultViewport' with parameters {
  "browserContextId": "50e9884c-...",
  "viewport": { "viewportSize": { "width": 1280, "height": 720 }, "deviceScaleFactor": 1, "isMobile": false }
}
Found property "<root>.viewport.isMobile" - false which is not described in this scheme
    at async getSession (server-camoufox.js:98:21)
```
- `curl -X POST .../tabs` with empty `{}` returns a *clean* `userId and sessionKey required`
  (so the validation path works; the crash is in the actual browser launch).
- `GET .../tabs` returns `{"running":true,"tabs":[]}` fine.

### Root cause
Playwright-core 1.61.1 emits a `Browser.setDefaultViewport` CDP call whenever
a viewport is configured — and it always includes `isMobile: false`. The v152
Camoufox engine's CDP schema does NOT accept `isMobile`, so it rejects the call.

### Fix (applied to `server-camoufox.js`, inside `getSession`, ~line 98)
```diff
   const context = await b.newContext({
-    viewport: { width: 1280, height: 720 },
+    // viewport: null disables Playwright's setDefaultViewport CDP call,
+    // which the v152 Camoufox engine rejects (it does not accept isMobile).
+    viewport: null,
     locale: 'en-US',
     timezoneId: 'America/Los_Angeles',
     geolocation: { latitude: 37.7749, longitude: -122.4194 },
     permissions: ['geolocation'],
   });
```
**Key subtlety:** removing the `viewport` line is NOT enough — Playwright then
uses its built-in 1280×720 default and emits the *same* rejected `isMobile`
call. The literal `viewport: null` is required to suppress the CDP call entirely.

### Verification
```bash
curl -s -X POST http://localhost:9377/tabs \
  -H 'Content-Type: application/json' \
  -d '{"userId":"t","sessionKey":"t"}'
# Expected (fixed): {"tabId":"<uuid>","url":"about:blank"}
# Before fix:        {"error":"...setDefaultViewport...isMobile..."}
```

## Failure 2 — edit "didn't take" (zombie server)
- Symptom: patched the file, restarted, still 500.
- Cause: an OLD server process (pid from before the reinstall) was still bound to
  9377, serving stale in-memory code. The fresh launch failed to bind and exited.
- Fix:
  ```bash
  bpid=$(ss -tlnp 2>/dev/null | grep 9377 | grep -oP 'pid=\K[0-9]+')
  kill "$bpid"
  sleep 2
  ss -tlnp 2>/dev/null | grep 9377 || echo "PORT FREE"
  ```
  Then start a fresh background server and re-run the `POST /tabs` verify above.
- `health` returning ok does NOT prove the running code matches your edit.

## Failure 3 — SPA login session lost on deep navigation
- Symptom: logged in, then `browser_navigate` to a thread URL → bounced to login.
- Cause: each `browser_navigate` spins a FRESH context, dropping cookies.
- Workaround (counter-intuitive but reliable): navigate DIRECTLY to the deep URL
  *first*. The SPA redirects to login; after you log in, it redirects you back to
  the deep URL *with* the session alive. (The post-login redirect preserves the
  in-context cookies.)
- Trap: chat-list link elements often expose NO separate a11y ref — only the
  "More actions" button does. Clicking that opens a menu, not the chat. Prefer
  the direct-URL-redirect path.
- Idle: sessions expire after 30 min (SESSION_TIMEOUT_MS). A long gap between
  user messages drops the session; re-auth is required.

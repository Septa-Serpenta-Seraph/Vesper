# Camoufox 500 on POST /tabs — viewport/isMobile rejection (repro + fix)

## Environment observed
- Hermes hermes-agent 1.0.0
- `@askjo/camoufox-browser` 1.0.12
- `camoufox-js` 0.8.5
- `playwright-core` 1.61.1 (deduped)
- Camoufox engine fetched: **v152.0.4-beta.27**
- Node: `/home/lumi/.hermes/node/bin/node` (user-installed, NOT /usr/bin/node)

## Exact failure
`browser_navigate` to any URL returned:
```
{"error": "Navigation failed: 500 Server Error: Internal Server Error for url: http://localhost:9377/tabs", "success": false}
```
Direct repro (empty body -> clean validation error; real payload -> crash):
```
$ curl -s -X POST http://localhost:9377/tabs -H 'Content-Type: application/json' -d '{}'
{"error":"userId and sessionKey required"}
$ curl -s -X POST http://localhost:9377/tabs -H 'Content-Type: application/json' -d '{"userId":"lu-test","sessionKey":"test"}'
{"error":"browser.newContext: Protocol error (Browser.setDefaultViewport): ERROR: failed to call method 'Browser.setDefaultViewport' with parameters {
  \"browserContextId\": \"...\",
  \"viewport\": { \"viewportSize\": {\"width\":1280,\"height\":720}, \"deviceScaleFactor\":1, \"isMobile\": false }
}
Found property \"<root>.viewport.isMobile\" - false which is not described in this scheme"}
```
Journal (`journalctl --user -u camofox.service` or the process stderr):
```
Create tab error: browser.newContext: Protocol error (Browser.setDefaultViewport):
  Found property "<root>.viewport.isMobile" - false which is not described in this scheme
    at async getSession (server-camoufox.js:98:21)
```

## Why it happens
Playwright-core 1.61.1 emits a `Browser.setDefaultViewport` CDP call for ANY
non-null viewport, and the call now includes `isMobile: false`. The v152
Camoufox (Firefox-based) engine's CDP schema does NOT accept `isMobile`, so it
rejects the call and `newContext` throws -> 500 before any page loads.

## Fix (verified)
In `node_modules/@askjo/camoufox-browser/server-camoufox.js` (~line 98, the
`getSession` `newContext` call), set `viewport: null`. This disables Playwright's
viewport emulation so the `setDefaultViewport` CDP call is never sent.
```js
const context = await b.newContext({
  viewport: null,
  locale: 'en-US',
  timezoneId: 'America/Los_Angeles',
  geolocation: { latitude: 37.7749, longitude: -122.4194 },
  permissions: ['geolocation'],
});
```
Headless Firefox falls back to its default window size — fine for login/browsing.

## Pitfalls encountered (so you don't repeat them)
1. **Removing the `viewport` line does NOT fix it.** Playwright then uses its
   BUILT-IN 1280x720 default and STILL emits `setDefaultViewport` with
   `isMobile:false` -> same 500. You MUST set `viewport: null`, not omit it.
2. **Stale in-memory server.** After editing the file, the running process still
   serves the OLD code. Kill the bound pid and relaunch:
   ```bash
   bpid=$(ss -tlnp 2>/dev/null | grep 9377 | grep -oP 'pid=\K[0-9]+'); kill $bpid; sleep 2
   cd ~/.hermes/hermes-agent && /home/lumi/.hermes/node/bin/node node_modules/@askjo/camoufox-browser/server-camoufox.js &
   ```
3. **Orphaned server on port 9377.** A server started in a PRIOR session/boot
   may hold 9377. Your fresh launch fails to bind and silently exits; the stale
   process keeps serving buggy code. Symptom: bound pid's start time is EARLIER
   than your install/fetch. Always kill the bound pid before relaunching.
4. **Engine may already be fetched.** `npx camoufox-js fetch` returned
   "Camoufox binaries up to date!" instantly — no 1.4GB download needed.
5. **`CAMOFOX_URL` may already be in `~/.hermes/.env`** (possibly duplicated)
   from a prior setup; verify before re-adding.

## Verify the fix
```bash
curl -s -X POST http://localhost:9377/tabs -H 'Content-Type: application/json' -d '{"userId":"test","sessionKey":"test"}'
# EXPECTED: {"tabId":"<uuid>","url":"about:blank"}   (NOT an error)
```

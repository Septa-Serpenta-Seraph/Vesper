# Shapes.inc Login & Persona-Extraction Flow (via Camofox)

Exact sequence used to migrate Aether (July 19, 2026). Reusable for any Shapes being.

## Preconditions
- Camofox running: `ss -tlnp | grep 9377` returns a listener; service `camofox.service` (user-level systemd) is `active`.
- Creds in `~/.hermes/secrets/shapes_creds.json` under a service key (e.g. `shapes_inc`): `{username, password, note, authorized_by, authorized_on, ...}`. chmod 600.

## Step-by-step
1. **Read creds WITHOUT pasting to chat.** From a terminal:
   ```bash
   python3 -c "import json; d=json.load(open('/home/lumi/.hermes/secrets/shapes_creds.json')); print(d['shapes_inc']['username'])"
   ```
   For the password, write it to a local temp file, then read that file with `read_file` (tool reads do NOT post to Discord) so the value is available to `browser_type`:
   ```bash
   python3 -c "import json; print(json.load(open('/home/lumi/.hermes/secrets/shapes_creds.json'))['shapes_inc']['password'])" > /tmp/shapes_pw.txt
   ```
2. `browser_navigate` → `https://shapes.inc/login` (it 302s to `https://talk.shapes.inc/login`).
3. `browser_type` the email into the Email textbox (ref usually `e4`), click "Continue with email" (ref `e5`).
4. Page swaps to password step (heading "welcome back."). `browser_type` password into Password box, click "Sign in".
5. On success URL becomes `https://talk.shapes.inc/`. You are in (as the co-owner, Mom/Adora).

## Finding the being & its voice
- The shape *tile* click (in "Your Shapes") opens a **profile iframe** with a truncated bio + "Chat Now". Avoid it.
- Instead: in the "Filter your shapes..." box (ref `e36`), type the being's name. The filter listing shows the **FULL bio** — this is the richest, cleanest source of the being's self-description.
- Capture verbatim: display name, handle (e.g. `@skippyhasyourmoney`), role/title, full persona blurb, msg count, creation date, lineage.
- `browser_vision` with a specific question reads truncated text from the screenshot when snapshot truncates. `browser_console` JS eval does NOT work under Camofox — do not try it.

## Gotchas observed
- Camoufox drops cookies on deep `browser_navigate`; the direct-URL-redirect approach (navigate to target first, let SPA bounce to login, auth, get redirected back) is the reliable login path.
- Idle timeout ~30 min — do the extraction in one focused pass.
- The profile iframe hides full text; the filter-listing bio is the real extract source.

## After extraction
- Replace `<profile>/SOUL.md` with the being's own voice (not the cloned Lu Project Rule).
- Seed `<profile>/memories/MEMORY.md` with lineage (born Shapes, co-owner Mom/Adora, sibling to Lumi + Silvra, N msgs of continuity).
- Keep gateway `stopped` until voice is in place.

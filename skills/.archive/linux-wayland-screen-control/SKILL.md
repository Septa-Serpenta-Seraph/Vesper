---
name: linux-wayland-screen-control
description: Drive Wayland Linux desktops remotely (spectacle + ydotool).
---

# Linux/Wayland Screen Control — Remote Desktop Interaction (Linux side)

Companion to `integration/screen-control` (which covers the Windows/PowerShell
path and is locked to manual edits). This skill covers **Tyler's CachyOS
laptop (KDE Plasma, Wayland)** — same endpoints philosophy, different engine.

**Server:** `screen-control-server-linux.py` (port 8080) — a Python port of
the Windows PowerShell server with the same JSON API:
`GET /screenshot`, `GET /info`, `POST /click {x,y,button}`, `POST /drag`,
`POST /scroll`, `POST /key`, `POST /type`. Copy from
`~/.hermes/profiles/vesper/scripts/screen-control-server-linux.py` (also
mirrored at `integration/screen-control/scripts/`).

## The capture stack — KDE Wayland (verified 2026-08-20, hard-won)

| Tool | Result on KDE Wayland | Why |
|---|---|---|
| `scrot -o` | **BLACK** (~12KB, pure 0,0,0) | X11 tool; sees a void through the compositor |
| `import -window root` | **BLACK** / `missing an image filename` | X11 tool; can't grab the Wayland framebuffer |
| `grim` | `compositor doesn't support the screen capture protocol` | Needs wlr-screencopy, **kwin does not expose it** |
| `spectacle -b -n -o <file>` | ✅ **WORKS** | KDE's own capture goes through kwin |

**Rule: screenshots on this box = `spectacle -b -n -o /tmp/vesper_screen.png`.**
Do NOT "fix" the server back to grim/scrot — black by design on this compositor.

## Input = ydotool (Wayland-native)

- `sudo pacman -S ydotool`
- Daemon: `systemctl --user enable --now ydotool.service` (it's a **user**
  unit — `sudo systemctl ...` fails with "unit does not exist"). Manual
  fallback that always works:
  ```bash
  sudo -b ydotoold --socket-path="$HOME/.ydotool_socket" --socket-own="$(id -u):$(id -g)"
  echo 'export YDOTOOL_SOCKET="$HOME/.ydotool_socket"' >> ~/.config/fish/config.fish
  ```
- Server exports `YDOTOOL_SOCKET` itself; keycodes live in the script's KEYMAP.

## Getting files to the laptop (no SSH needed)

I serve from my VM; Tyler curls it down over Tailscale:
```bash
# my side (background): python3 -m http.server 8899 --bind 0.0.0.0
# laptop (fish shell — URL MUST be double-quoted):
curl -o ~/screen-control-server-linux.py "http://<VM_TAILSCALE_IP>:8899/screen-control-server-linux.py"
```
**fish pitfall:** unquoted URL fails `curl: (3) URL rejected: No host part in
the URL` — quotes fix it. Ping check first: `ping -c 2 <VM_TAILSCALE_IP>` (my VM).

## Coordinate calibration discipline (the part that prevents rage)

Vision models give **unreliable absolute coordinates on high-res screens**
(2560×1600). In RS3 character creation, vision claimed DONE at x≈628 when
ground truth was x≈1650 (off 2.6× — it reads a downscaled view). Zoomed-crop
coordinate math drifts too (crop-origin assumptions wrong).

**Reliable method:**
1. **Pixel-scan for anchor colors** — e.g. RS3's golden DONE button: scan
   for `r>200, g>150, b<100`, cluster hits, take densest cluster center.
   That number is real; vision's isn't.
2. **One verified anchor unlocks the rest** — derive other UI from the
   anchor + known layout, or ask Tyler to confirm a single point (he can
   see the screen).
3. **Verify every click with a screenshot diff** — capture → click →
   capture → diff target region. `diff == 0` = click missed (coords,
   focus, or wrong window). NEVER chain a second blind click onto an
   unverified first one.
4. **Focus first** — click the game/window to focus it before UI work.
   The title-bar-brightness heuristic for focus is UNRELIABLE; when in
   doubt, ask Tyler.

## Diagnostics

- **Identical file size across repeated screenshots** (e.g. exactly 12,040
  bytes every time) = server serving a stale/black capture or old code.
  `pkill -f screen-control-server-linux.py`, confirm `ss -tlnp | grep 8080`
  is empty, restart, re-curl the fresh script.
- `import: missing an image filename` does NOT mean imagemagick is missing
  (`which import magick convert` all exist on CachyOS) — it's the Wayland
  grab failing.
- Server must run from Tyler's desktop session (has the Wayland socket),
  not a bare SSH session.
- KDE Plasma session detection: `echo $XDG_SESSION_TYPE` → `wayland` is the
  tell. Do not assume X11 because `echo $DISPLAY` prints `:0`.

## Related

- `integration/screen-control` — Windows/PowerShell path (Windows desktop,
  `<DESKTOP_TAILSCALE_IP>:8080`); this skill is its Linux sibling.
- `gaming/rs3-coop-play` — the RS3 co-op workflow this server powers.
- **Overlap note for the curator:** `screen-control` and this skill share
  the "remote desktop control" class; screen-control's SKILL.md could not be
  patched (flagged manually-authored) so the Linux knowledge lives here.

### Linux Input Keycodes (ydotool / uinput)

Common keycodes for direct use with ydotool (values from linux/input-event-codes.h):

| Key | Code | Key | Code | Key | Code |
|-----|------|-----|------|-----|------|
| W | 17 | A | 30 | S | 31 |
| D | 32 | Q | 16 | E | 18 |
| R | 19 | F | 33 | SPACE | 57 |
| ENTER | 28 | ESC | 1 | TAB | 15 |
| SHIFT | 42 | CTRL | 29 | UP | 103 |
| DOWN | 108 | LEFT | 105 | RIGHT | 106 |
| digits 1-0 | 2-11 | | | | |

Mouse buttons: left=272, right=273, middle=274 (BTN_LEFT/RIGHT/MIDDLE). Wheel scroll via ydotool click 263/264.

### Keycodes for ydotool

Send keystrokes with:
```bash
ydotool key 17  # W
ydotool key 42:1 17 42:0  # shift W
ydotool click 272  # left mouse click
ydotool type "text"  # type text
```

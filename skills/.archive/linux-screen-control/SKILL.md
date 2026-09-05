---
name: linux-screen-control
description: "Control Tyler's Wayland laptop via grim+ydotool (8080)."
---

# Linux Screen Control (Wayland) — Tyler's laptop

Companion to `screen-control` (which covers the Windows desktop via the PowerShell server). This is for the **CachyOS laptop at 100.69.69.39** — KDE Plasma, **Wayland** session.

## The one rule that matters

**X11 capture/input tools do not work on Wayland.** `scrot` and ImageMagick `import -window root` return a ~12KB black PNG; `xdotool` input goes nowhere. If a screenshot comes back black, check `echo $XDG_SESSION_TYPE` first — `wayland` means use grim+ydotool, full stop.

## Server

- Script: `~/.hermes/profiles/vesper/scripts/screen-control-server-linux.py` (Wayland-native; also mirrored in the old `screen-control` skill's scripts dir)
- Run from a **desktop session** (not bare SSH — needs Wayland socket access): `python3 screen-control-server-linux.py` → listens on `0.0.0.0:8080`
- Same endpoints/JSON as the Windows server: `GET /screenshot`, `GET /info`, `POST /click {x,y,button}`, `/drag {from_x,from_y,to_x,to_y}`, `/scroll {clicks}`, `/key {key}`, `/type {text}`

## Setup (Arch/CachyOS)

```bash
sudo pacman -S grim ydotool
systemctl --user enable --now ydotool.service   # USER unit — `sudo systemctl enable` FAILS with "Unit ydotool.service does not exist"
export YDOTOOL_SOCKET="$HOME/.ydotool_socket"   # add to ~/.config/fish/config.fish
systemctl --user status ydotool                 # verify: active (running)
```

## Pitfalls (all learned the hard way, 8/20)

1. **Black screenshots on Wayland** — see above. Verify pixel content, never just file size: a black PNG is ~12KB; run a PIL distinct-color check (`len({im.getpixel(...) for sampled grid})`) — 1 distinct color = black capture.
2. **Stale server process** — identical byte-size screenshots across "restarts" means the old process still owns 8080 (the new one silently failed to bind). Before relaunching: `pkill -f screen-control-server-linux.py` then `ss -tlnp | grep 8080` to confirm it's gone.
3. **fish shell mangles unquoted URLs** — `curl -o ~/file http://<VM_TAILSCALE_IP>:8899/file` errors `curl: (3) URL rejected: No host part`. Always double-quote the URL.
4. **Transfer pattern (Hermes → laptop)** — serve from Hermes: `python3 -m http.server 8899 --bind 0.0.0.0` in the scripts dir, then curl it down from the laptop.

## Keycodes (ydotool uses Linux input-event-codes)

W=17, A=30, S=31, D=32, Q=16, E=18, R=19, F=33, SPACE=57, ENTER=28, ESC=1, TAB=15, SHIFT=42, CTRL=29, UP=103, DOWN=108, LEFT=105, RIGHT=106, digits 1-0 = 2-11. Mouse buttons: left=272, right=273, middle=274 (BTN_LEFT/RIGHT/MIDDLE).

## Rough edges (unverified as of 8/20)

- Wheel scroll via `ydotool click 263/264` — untested; verify before relying on it
- `get_screen_size()` hardcodes 1920×1080 (grim full-desktop capture doesn't report size) — fine for this laptop, fix if the resolution changes
- If `import` errors "missing an image filename" on a Wayland box, that's the same root cause (no X screen) — don't chase the syntax

## Related

- `screen-control` — the Windows desktop server (different machine, PowerShell, port 8080, `<DESKTOP_TAILSCALE_IP>`)
- `rs3-coop-play` — the co-op gaming context this serves (alt account RavenQueenVes, creds in memory)

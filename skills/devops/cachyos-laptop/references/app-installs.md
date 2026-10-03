# App Installs on CachyOS — when `pacman -S` says target not found

Session-proven 2026-09-29 (Zoom, therapy-urgent). General rule first:

## Crisis triage order (learned 9/29 — meeting in <5 minutes)

When the install is blocking a time-critical event (therapy call, job interview):
1. **Zero-install path FIRST, one line, no options dump.** "Browser join now"
   beats a perfect install guide the user can't finish in time. Tyler needed
   Zoom live for therapy in ~5 min; the full pacman essay was noise at that
   moment. One command → "Go." Details after the crisis.
2. **Vendor-tarball `pacman -U` as the real install** (below) — AUR helper
   failures under time pressure are a trap; skip the helper entirely.
3. Full comparison/fallback menu only once the meeting is safe.

## The pattern

1. **Don't claim repo membership without checking.** `pacman -S zoom` failed with
   `target not found` because **Zoom is NOT in the official Arch repos** — it's
   AUR/vendor-tarball only. I initially told Tyler it was in `[extra]`; the error
   proved me wrong and cost him time mid-crisis. `pacman -Si <pkg>` or
   `pacman -Ss <pkg>` FIRST, then advise. (Second trap same day: Zoom's
   download page lists Ubuntu/Debian/Fedora/etc. but NOT Arch — the missing
   distro in the dropdown does NOT mean no package exists; check the CDN.)
2. **AUR helpers can fail** (paru failed here — stale cache or build issue).
   Don't keep retrying the same helper under time pressure; switch routes.
3. **Check whether the VENDOR ships a native pacman-installable tarball.** Many
   proprietary app vendors (Zoom, etc.) build their own `.pkg.tar.xz`. That
   installs with plain `pacman -U` — no AUR helper, no makepkg.

## Zoom — the working recipe (verified 9/29)

```bash
# Zoom's own CDN tarball for Arch — the same one the AUR package repackages:
curl -Lo /tmp/zoom.pkg.tar.xz https://zoom.us/client/latest/zoom_x86_64.pkg.tar.xz
sudo pacman -U /tmp/zoom.pkg.tar.xz
```

- Deps resolve automatically from normal repos. If `pacman -U` lists missing
  deps, run the exact `sudo pacman -S <deps>` it names, then repeat the `-U`.
- Launch: `zoom` or the app launcher.
- **Wayland note (CachyOS defaults to Wayland):** joining calls works fine;
  *screen sharing* needs the PipeWire portal (`xdg-desktop-portal-kde` or the
  DE-appropriate portal package) — fix the portal, not Zoom.
- Zero-install emergency (when a meeting starts in minutes):
  the meeting link → zoom.us → **"Join from your browser"** (small bottom link).
  Full video/audio, nothing installed.
- Flatpak fallback: `flatpak install flathub us.zoom.Zoom` (heavier, but works).
---
name: desktop-remote-control
description: Remote desktop via HTTP server for Windows and Linux.
---

# Desktop Remote Control — HTTP Server + Vision Pipeline

Remote desktop control by serving a screenshot + input API from the target machine. Works over Tailscale/LAN/SSH tunnel. Two proven server engines:

## Windows Path (PowerShell `screen-control-server.ps1`)
- Serves `GET /screenshot` (PNG), `POST /click`, `/drag`, `/key`, `/scroll`, `/rightclick`
- Runs as admin for `mouse_event` P/Invoke
- **Pitfall:** PowerShell over SSH — use `cmd /c` for commands, here-strings for HTML, avoid `$_` in strings
- **Access:** Tailscale `http://<DESKTOP_TAILSCALE_IP>:8080` or via SSH tunnel

## Linux Wayland Path (Python `screen-control-server-linux.py`)
- Same JSON API: `GET /screenshot`, `GET /info`, `POST /click`, `/drag`, `/scroll`, `/key`, `/type`
- **Capture:** `spectacle -b -n -o` (grim/scrot produce black on KDE Wayland)
- **Input:** `ydotool` (keycodes from linux/input-event-codes.h)
- **Access:** Served from Tyler's CachyOS laptop over Tailscale

## Key Principles
- **Coordinate calibration:** Vision models give unreliable absolute coordinates (2.6x off on high-res screens). Use pixel-scan for anchor colors, verify every click with screenshot diff, NEVER chain blind clicks.
- **Focus first:** Click the target window to focus before UI work.
- **Game-specific:** Cities Skylines (road drawing via drag, camera via right-drag + key), RS3 (pixel-scan for golden DONE button).

## Absorbed Skills

This umbrella absorbs `powershell-desktop-control` and `linux-wayland-screen-control`. Their full content with support files remains in `~/.hermes/skills/.archive/`.

Also absorbed `screen-control` (archived). Its game-specific content for Cities: Skylines
co-op, game focus protocol, and PowerShell server endpoints is preserved at
`references/game-co-op-patterns.md`.

### Windows PowerShell Server Detail
Full PowerShell server script at: `~/.hermes/skills/.archive/powershell-desktop-control/SKILL.md`
Pitfalls: execution policy blocks scripts (`Set-ExecutionPolicy Bypass`), HTML in strings (use here-strings), `$_` terminator issues.

### Linux Wayland Server Detail
Full Python server + script at: `~/.hermes/skills/.archive/linux-wayland-screen-control/SKILL.md`
KDE Wayland capture stack: spectacle (works) > grim (black) > scrot (black). ydotool daemon as a user service. Keycode table included in the archived skill.
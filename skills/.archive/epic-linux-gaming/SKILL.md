---
name: epic-linux-gaming
description: Use when Tyler plays Epic games on his CachyOS laptop.
---

# Epic Games on CachyOS laptop (legendary + umu)

Tyler's laptop is CachyOS (Arch/KDE/fish). Epic games run via `legendary` + `umu-run` (Proton). Workflow learned the hard way 8/29 — don't re-fight these.

## Setup (once)
- **legendary**: official release binary from `legendary-gl/legendary` GitHub (e.g. `~/legendary`). The AUR/paru build breaks on python-uv — skip it. Download `legendary_linux_x64` from releases, `chmod +x`.
- **umu-launcher**: `paru -S umu-launcher` (gives Proton via `umu-run`).
- **Stale package DB**: `sudo pacman -Syy` first — fixes `wine` 404s AND paru uv-build failures.

## 🚨 Stale package DB — recurring gotcha (9/5 confirmed again)
- **Symptom:** `pacman -S <anything>` / `paru -S <anything>` fails with 404 / "failed to retrieve" / "not found" — even for packages that obviously exist (e.g. LibreOffice).
- **Root cause:** the local package DBs in `/var/lib/pacman/sync/` age out; on CachyOS a week+ stale = 404s on big packages.
- **Fix (always FIRST when any install fails mysteriously):**
  ```fish
  sudo pacman -Syy         # refresh DB (force)
  sudo pacman -S <pkg>     # retry
  ```
- **Tyler keeps forgetting this** after installs gap (9/5: "Update worked. Keep forgetting about that.") — if he says an install is failing, suggest `-Syy` before any other debugging.
- **LibreOffice pkg name:** `libreoffice-fresh` / `libreoffice-still` — NOT `libreoffice-fresh-en-gb` (404s).
- **Launch through legendary with Proton** (critical — pins the prefix):
  ```
  GAMEID=<appid> legendary launch "<game>" --wine umu-run
  ```
  Without GAMEID, umu uses `umu-default` and saves land in the wrong prefix. AW2's appid is 1262240. `legendary list-games` / `list-installed` for IDs.

## Alan Wake 2 save-file GUID gotcha (unsolvable — don't re-fight)
- AW2 Epic saves live at `.../Saved Games/Alan Wake 2/` in the prefix:
  `~/.local/share/umu/<GAMEID>/drive_c/users/steamuser/Saved Games/Alan Wake 2/`
- Cloud saves: `legendary download-saves "<game>"` → lands in the hidden dotfolder `~/Games/.saves/<appid>/<timestamp>/` (NOT under ~/.config).
- Old Windows cloud saves carry the OLD machine's profile GUID embedded inside the `.chunk` files. The game only lists saves whose embedded GUID matches the CURRENT profile GUID (visible via `strings .../preferences/data.chunk` → a GUID). Copying files into the correct folder is NOT enough — they stay "foreign" and the game ignores them. Only fix would be hex-patching the GUID. Save files are otherwise safe.

## CPU FPS melt ("runs great, then tanks after ~20 min")
- Symptom: CPU ~219% (top) while GPU ~35% (nvidia-smi); frames die though nothing is hot.
- Rules out: thermal (75–80°C is fine), RAM (6.7/16Gi fine), power profile (performance).
- Fix: DXVK async config in the prefix:
  `~/.local/share/umu/<GAMEID>/drive_c/users/steamuser/AppData/Local/DXVK/dxvk.conf`
  containing:
  ```
  dxvk.enableAsync = True
  dxvk.numCompilerThreads = 0
  ```

## Laptop sleeps mid-game with a controller
- KDE power management ignores controller input → laptop suspends during play.
- Wrap the launch (always works): `systemd-inhibit --what=idle:sleep -- legendary launch "<game>" --wine umu-run`
  (`kde-inhibit` flags vary by version — `--power` or nothing; systemd-inhibit is the reliable one). Alternative: Caffeine tray toggle (`plasma5-applets-caffeine-bin`).

## Fish shell gotchas (laptop uses fish)
- No bash heredocs — use `printf 'line1\nline2\n' > file` for config files.
- Escape regex dots in grep under fish; quote patterns.
- When `find`/`cp` return "no matches", the path is wrong — verify with `find ~/... -maxdepth N -type d` before assuming.

## Shader cache persistence
- Shaders compile per-prefix and evaporate across launches; a persistent `DXVK_STATE_CACHE_PATH` / `__GL_SHADER_DISK_CACHE_PATH` dir can speed up repeat launches.

## Tyler's lunch (schedule note)
- When Tyler takes lunch on a work day it's a full **30-minute break** (his lunch window is a half hour — 8/29).

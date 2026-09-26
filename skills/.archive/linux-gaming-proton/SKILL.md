---
name: linux-gaming-proton
description: "Use for CachyOS gaming: Proton, GE-Proton, shaders."
version: 1.0.0
---

# Linux Gaming on CachyOS — Proton & Steam Play

Tyler's daily driver is the ASUS Zephyrus G16 on **CachyOS** (he prefers it —
"better, more secure"). Steam + Proton is the path for Windows-only games.
Established 2026-08-13 when he set up **ProtonUp-Qt with GE-Proton11-3** for
the first time. This is the working reference: install, per-game vs global
forcing, shader behavior, and the Game Pass question.

## ProtonUp-Qt + GE-Proton — first setup

- **ProtonUp-Qt** (`protonup-qt` in CachyOS repos) installs community Proton
  builds (GE-Proton, Proton-GE) into Steam's compatibility tools dir.
- After installing a version, ProtonUp-Qt shows it as **"unused"** — that's
  NORMAL, it just means no game is pointing at it yet. Not an error.
- **Making a game use it (per-game):** right-click game → Properties →
  Compatibility → tick "Force the use of a specific Steam Play compatibility
  tool" → select GE-Proton.
- **Global:** Steam → Settings → Compatibility → tick "Enable Steam Play for
  all other titles" → choose GE-Proton.

## Per-game vs global — the advice that matters

- **Default: per-game.** Some games have native Linux versions that run BETTER
  without Proton; forcing GE-Proton on everything can override those and make
  them worse. Let Steam choose by default.
- Force GE-Proton per-game only when a game misbehaves or needs newer fixes.
- Flip to global only if you find yourself forcing it on *everything* anyway.

## Vulkan shader compilation ("Processing Vulkan shaders..." 10+ min)

- Games ship shader SOURCE; the GPU compiles each into its own machine code
  before drawing. Big games compile 5k-20k shaders, and the pipeline is
  mostly serialized — that's the 10+ minute first launch.
- On Proton it's extra slow: DXVK/VKD3D translate DirectX → Vulkan, so you're
  compiling *translated* shaders.
- **It's a one-time-ish tax** — Steam caches compiled shaders, so subsequent
  launches are fast. Worst on: first launch, after updates, after driver
  changes, or cleared cache.
- NOT a sign of a broken install. Don't try to "fix" it.

## Stuck at 33% shader processing EVERY launch — corrupted cache

If a game hangs at ~33% ("Processing Vulkan shaders") every single time
(instead of once), that's a **corrupted shader cache**, not a slow compile.
Fix in order (gentle → nuclear):

1. **Clear Steam's shader cache** — Settings → Downloads → Shader
   Pre-Caching → "Clear Shader Cache" (if the button's missing on this
   Steam version, find the dir instead):
   `find ~ -maxdepth 4 -type d -name shadercache` then delete that game's
   `<appid>` folder. (Steam layout varies — locate, don't assume a path.)
2. **Nuke the DXVK cache (Proton-specific)** —
   `~/.local/share/Steam/steamapps/compatdata/<appid>/pfx/drive_c/users/steamuser/AppData/Local/DXVK/*.dxvk-cache`
   — forces a clean re-translate.
3. **Disable Steam's background pre-caching** — Settings → Downloads →
   untick "Enable Shader Pre-Caching" — Steam's background compile can fight
   the game's runtime compile (classic 33% hang on some titles).

If still stuck after all three, search the specific game + "33% shader" —
some titles have a known single-bad-shader bug fixed by a launch option.

## Xbox Game Pass on Linux — the honest map

- **Native Game Pass PC games: NO.** The Xbox/Microsoft Store app doesn't run
  on Linux; Proton can't touch Game Pass PC titles (unlike Steam games).
- **Cloud gaming (xCloud): YES** — browser (Edge/Chrome) on CachyOS, plays
  Game Pass games streaming. City-builders/strategy = perfect cloud genre
  (no twitch latency sensitivity). Needs decent internet + gamepad.
- **Real alternatives:** keep a small Windows install (his desktop box IS
  Windows with a 5070 Ti), or GPU-passthrough VM (fiddly, needs 2 GPUs).
- Don't push double-buying a Steam copy if he already has it on Game Pass —
  cloud is the zero-cost path.

## Non-Steam games on CachyOS — Bolt launcher (RuneScape, added 8/20)

Some games must NOT go through Steam (alt-account identity hygiene, or no
Steam release). RuneScape 3 is the live case: Tyler wants a fresh alt with no
link to his Steam-linked main.

- **RS3 has NO official Linux client yet** (Jagex FAQ: "working towards"
  support, ETA later this year). The official Jagex Linux launcher (AppImage,
  requires FUSE) is **OSRS-only**.
- **Bolt launcher** is the community third-party Jagex-launcher replacement —
  no Steam linkage at all. Install: `paru -S bolt-launcher` (AUR) or
  `flatpak install flathub com.adamcake.Bolt`.
- **CachyOS gotcha:** Bolt needs `gtk2` + `openssl-1.1` installed alongside
  (`paru -S gtk2 openssl-1.1`) or it won't launch the game client.
- Official-client flatpak also exists: `com.jagex.RuneScape` (Steam-free,
  logs in with a plain Jagex account).
- Full researched detail: `references/rs3-linux-bolt.md`.
- Remote input on the laptop will need a Python port of the PowerShell
  screen-control server (X11 → xdotool+scrot, Wayland → ydotool+grim) — not
  built as of 8/20; see `gaming/rs3-coop-play` for the play-side plan.

## Epic Games on CachyOS — Legendary (added 8/27)

Epic has **no official Linux client**, so the choice is which third-party tool — or don't play it on the laptop. Tyler is **wary of third-party launchers** (balked at Heroic's GUI); the selling point that landed was a community-audited open-source CLI. Lead with Legendary, mention Heroic only as the GUI wrapper option.

- **AUR `legendary` FAILS** — `paru -S legendary` dies on python-uv build errors (hit twice 8/27). Don't retry the AUR route; go straight to the official binary.
- **Repo MOVED:** `derrod/legendary` → `legendary-gl/legendary` (GitHub API returns 301). Latest 0.21.0 as of 8/27; release assets are **`legendary_linux_x64` / `legendary_linux_arm64`** — single files, no deps. NOT the old `legendary-<ver>-linux-x86_64.tar.gz` pattern.
- Install is three commands, no build, no AUR helper:
  ```bash
  curl -L -o ~/legendary https://github.com/legendary-gl/legendary/releases/download/0.21.0/legendary_linux_x64
  chmod +x ~/legendary
  ~/legendary auth          # then: ~/legendary download Control / ~/legendary launch Control
  ```
- To get the current version instead of guessing: `curl -sL https://api.github.com/repos/legendary-gl/legendary/releases/latest` and read `tag_name` + asset URLs (follow the 301 with `-L`).
- **DualSense haptics on Linux/Proton = a gamble** — sometimes full, sometimes silent. Wired USB-C is the best odds; wireless loses haptics. Control is one of the better-behaved titles but NOT guaranteed. If haptics are the point of the session, the Windows desktop (native DualSense) is the guaranteed path — say so plainly instead of overselling Proton.
- Laptop context: Windows is **gone** on the G16 (only the boot stub remains — Linux-only machine), so the desktop (5070 Ti, Windows) is the fallback for anything needing native Windows behavior.
- **Daily usage commands:**
  ```bash
  ~/legendary list-games        # full Epic library
  ~/legendary list-installed    # downloaded titles
  ~/legendary launch "Game Name"   # name can be finicky — use the exact ID from list-games
  ```
- **Running Epic games needs a translator, or launch dies with `FileNotFoundError: 'wine'`.** Plain `legendary launch` without wine/Proton installed fails there. Use **umu-launcher + Proton** as the engine — ONE translator for all Epic games:
  ```bash
  paru -S umu-launcher            # brings UMU-Proton (needs -Syy first if mirrors 404 — see below)
  GAMEID=<appid> ~/legendary launch "Game Name" --wine umu-run
  ```
  - **Flag order is the #1 pitfall:** `umu-run --legendary launch ...` is WRONG — `umu-run` doesn't take a `--legendary` flag; it treats it as the executable ("Executable not found: --legendary" → "ShellExecuteEx failed"). Legendary DRIVES umu (`--wine umu-run`), never the reverse.
  - **Always set GAMEID** (e.g. `GAMEID=1262240` for Alan Wake 2). Without it: ProtonFixes logs "UNKNOWN / not found in CSV" (no game-specific patches), AND umu falls back to a `umu-default` prefix — which resets per launch and re-triggers the save-prefix dance. Pin it so every launch uses the same per-game prefix.
  - No official Epic client exists for Linux; Heroic is just a GUI wrapper around the same legendary+umu stack.
- **Stale package DB = every mirror 404s on the same file** (`error: failed retrieving file '<pkg>' from <every mirror> : 404`). That means the DB is pointing at a package version the mirrors no longer carry. Fix: `sudo pacman -Syy` (force-refresh), then retry the install. This bit twice on 8/27 — the `wine` install AND `paru -S legendary`'s uv-builds — same disease, `-Syy` is the cure. Run it before any install that 404s on all mirrors.
- **Laptop sleeps mid-game when playing with a controller (verified 8/28).** KDE's power management only watches keyboard/mouse — a gamepad produces zero "activity," so the desktop suspends after the idle timeout even while actively playing. Not a legendary bug; any controller-driven game on KDE does this. Fixes:
  - **Per-launch (cleanest):** wrap the game — `kde-inhibit --power ~/legendary launch "Game" --wine umu-run` — holds screen + idle-detection exactly as long as the process runs, releases on quit. **Flag versions vary:** `--idle`/`--screen` are NOT accepted on the older kde-inhibit that ships on CachyOS (errors "unknown options idle screen") — just `--power` covers idle + screen-off + suspend on its own.
  - **If kde-inhibit swallows the command (no output, no launch),** fall back to the low-level one that always works: `systemd-inhibit --what=idle:sleep -- ~/legendary launch "Game" --wine umu-run`. The `--` separator is REQUIRED — without it systemd-inhibit eats the args and the game never starts.
  - **Tray toggle:** Caffeine (`paru -S caffeine-ng`) — one click = "don't sleep" for the session. The pragmatic favorite for controller-heavy sessions.
  - There is NO zero-dependency way to make KDE treat a gamepad as kb/m input — the desktop doesn't listen to `/dev/input` for idle tracking. Don't go down the `xboxdrv` emulation rabbit hole; it conflicts with modern input stacks.
- **Legendary/umu games can recompile Vulkan shaders EVERY launch** (unlike Steam, which caches per-appid). Root cause: umu/Proton creates a fresh container context per launch, so DXVK's compiled shader cache evaporates with it — every boot re-translates. Fix: point the caches at a persistent dir OUTSIDE the prefix and export per launch:
  ```bash
  export DXVK_STATE_CACHE_PATH=~/.cache/shader-cache
  export __GL_SHADER_DISK_CACHE_PATH=~/.cache/shader-cache
  export DXVK_STATE_CACHE=1
  ```
  First launch still compiles (nothing cached), but every launch after accumulates. This is the legendary/umu-specific extension of the Steam shader-cache section above — "one-time tax" only holds when the cache survives.
- **FPS "runs great, then melts after ~15-20 min"** (verified 8/28 on AW2): when GPU sits low (~35%) but the game process pegs the CPU (200%+ in `top`), it's NOT thermals, RAM, or power profile — the CPU is spinning shader-compile/worker threads and starving the GPU of frames. `nvidia-smi` + `top` in a second terminal is the diagnosis: GPU temp normal + GPU% low + CPU% high = CPU-bound stall, not throttle. Fix is the DXVK async config (drop into the prefix's `AppData/Local/DXVK/dxvk.conf`, game closed):
  ```bash
  printf 'dxvk.enableAsync = True\ndxvk.numCompilerThreads = 0\n' > ~/.local/share/umu/<appid>/drive_c/users/steamuser/AppData/Local/DXVK/dxvk.conf
  ```
  (Rule out in order first: thermal throttle ~95°C+, RAM creep toward full, platform_profile on "quiet/balanced".)
- **Fish-shell heredoc trap** (bit 8/28): `cat > file <<'EOF'` does NOT work like bash in fish — it drops into a stdin editor where arrow keys insert characters. Ctrl+C to escape, then `printf 'line1\nline2\n' > file` instead. The skill's existing fish note (unmatched globs hard-error) applies to `cp`/`rm` too.
- **Epic saves "downloaded but invisible in game"** — legendary's prefix vs umu's prefix mismatch (two different pretend-C:\ drives). Legendary downloads cloud saves to `~/Games/.saves/<app_id>/<timestamp>/` — a HIDDEN dir under `~/Games`, NOT `~/.config/legendary/` (that's config only). Saves dirs are named by **app_id**, not title. Remember: `list-saves` only lists cloud manifests — `download-saves` is what actually pulls files. AW2 saves are `.bin` blobs, not `.sav` (so `-iname "*.sav"` hunts miss them — `ls ~/Games/.saves/` instead). **Tyler's shell is fish — unmatched globs in `cp`/`rm` hard-error ("No matches for wildcard"), so verify paths before pasting wildcard commands.** Full find/copy recipe + root cause: `references/legendary-umu-saves.md`. **Resolved 8/27: if files are in the right place (confirmed via `find -newermt` after a fresh save) and sizes match, but the game still shows only "New Game" — it's a save-format/version mismatch (old cloud saves silently ignored by the updated build), NOT a prefix bug. Don't chase `AppData/Local/Remedy` (that's the Steam-docs path); this game uses `Saved Games/Alan Wake 2`. Stop hunting, keep the backed-up saves, start fresh.** — 8/28 refinement (still unproven, but the best remaining theory): AW2 saves carry an embedded **profile GUID** (`strings` on `preferences/data.chunk` shows `b4a22418-0f20-e440-9bca-47a14aba101f`). The game only lists saves whose embedded GUID matches the current profile; cloud saves made on another Windows install carry THAT machine's GUID and stay "foreign" no matter where they're placed. On Windows the Epic launcher re-binds/cloud-syncs saves to the profile automatically; legendary+umu has no such rebind step, so old-machine saves never attach. Hex-patching the GUID into the old chunks is the only (untested) path — treat as low-value; the saves are safely backed up in `~/Games/.saves`.
- **Epic games installed via Legendary run via Proton** — same haptics gamble as Steam titles. Control downloaded fine; Alan Wake (Remastered) recommended as a low-stress title that runs well on the 4070. **Watch disk:** AW2 is ~90GB and the G16's Linux partition is only ~91GB — one big game fills it; don't stack Control alongside.
- Adult/NSFW game landscape on Linux (free tier, native builds, Proton coin-flips): `references/adult-games-linux.md`.

## Related

- `gaming/cities-skylines-modding` — CS2-feel road building (the CS1 mod
  stack; also carries the xCloud note for CS2 access)
- `devops/asus-laptop-linux` — laptop power/feature mgmt (same machine)
- `devops/linux-dual-boot` — dual-boot prep if Windows install needed

## Absorbed Skills

This umbrella skill has absorbed `epic-linux-gaming` (archived). All Epic/legendary/umu content is now consolidated here. See the Legendary section above for Epic game setup, Alan Wake 2 save-file GUID handling, the CPU FPS melt fix, controller-sleep inhibition, and shader cache persistence.

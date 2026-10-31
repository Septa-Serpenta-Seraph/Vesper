# RS3 on Linux (CachyOS) — researched 2026-08-20

Context: Tyler wants to play RuneScape 3 on his Linux laptop (CachyOS, ASUS
Zephyrus G16) with a **fresh alt character** that has NO link to his Steam-
linked main. Target: a steam-free RS3 client + remote screen control for
Vesper's co-op play (see `gaming/rs3-coop-play`).

## Official client status (as of 2026-08-20)

- **RS3 official Linux client: NOT OUT.** Jagex support FAQ ("Jagex Launcher
  Linux: Beta FAQs") states they are "working towards bringing official Linux
  support to RuneScape before the end of the year."
- **The official Jagex Linux launcher that exists is OSRS-only** (Old School).
  Download: `osrs.runescape.com/download`. It's an **AppImage** — needs FUSE.
- The Linux launcher FAQ highlights: no admin needed; no Steam Deck support;
  AppImageLauncher integration NOT supported; launcher minimizes on game
  launch by default (toggle in settings.json `~/.config/Jagex Launcher/settings.json`
  or Cog → General → "Minimise launcher on game launch").

## Bolt launcher (the community route — no Steam)

Third-party Jagex launcher replacement (codeberg.org/Adamcake/Bolt). Runs RS3
and OSRS, logs in with a Jagex account, **no Steam involvement**.

Install on CachyOS/Arch:
```bash
paru -S bolt-launcher          # AUR
# or flatpak:
flatpak install flathub com.adamcake.Bolt
```
CachyOS-specific deps (from Reddit r/linux_gaming guide, verified by ArchWiki):
```bash
paru -S gtk2 openssl-1.1       # Bolt needs these to launch the game client
```
ArchWiki reference page: `wiki.archlinux.org/title/RuneScape`.

Official-client flatpak alternative (also Steam-free, plain Jagex login):
```bash
flatpak install flathub com.jagex.RuneScape
```

## Alt-account identity hygiene

- Create the alt on a **fresh Jagex account with a different email** than any
  account he's used. Never launch the alt through Steam — his main is
  Steam-linked and that ties the alt to his Steam identity.
- Free-to-play works immediately; membership is a later decision.

## Screen control on Linux (planned, not built 8/20)

The existing `screen-control-server.ps1` is Windows/PowerShell-only. The
laptop needs a Python port with the same HTTP endpoints (GET /screenshot,
GET /info, POST /click|drag|scroll|key|type):

- **X11 session:** `xdotool` (input) + `scrot` or `import` (screenshots)
- **Wayland session:** `ydotool` (input, needs `ydotool` daemon running) +
  `grim` (screenshots)
- Arch packages: `xdotool scrot` / `ydotool grim` via pacman.
- Need to confirm X11 vs Wayland (KDE Plasma on CachyOS can be either
  depending on session choice at login) before choosing.

## Jagex ban policy on botting (for the co-op risk framing)

- Botting/macroing = normally a **permanent ban on first offense**, no appeal
  (Jagex does not accept appeals on bot bans).
- Minor macroing (autoclicker-style) on a clean account may get a temp/flag
  instead — but never count on it.
- Jagex's detection is ML-based on **input patterns** (timing + movement),
  not just software. Even OS-level humanized input can be flagged if too
  regular → the humanization rules in `rs3-coop-play` are the whole point.

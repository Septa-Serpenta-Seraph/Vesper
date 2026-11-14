# RS3 co-op on the Linux laptop (deployment notes, 2026-08-20)

How the alt account gets onto Tyler's CachyOS laptop and plays co-op with me.
The `gaming/rs3-coop-play` skill covers the general workflow/humanization
rules; this file is the laptop-specific deployment detail.

## Launcher — Bolt (no Steam linkage)

- RS3's official Linux client is NOT released (FAQ: "working towards it").
  The official Linux Jagex Launcher AppImage (`osrs.runescape.com/download`)
  is OSRS-only and needs FUSE.
- **Bolt** = third-party launcher, runs RS3 without Steam:
  `paru -S bolt-launcher gtk2 openssl-1.1` (AUR; gtk2 + openssl-1.1 are the
  known CachyOS runtime deps). Flatpak fallback: `com.adamcake.Bolt` on
  Flathub. ArchWiki: wiki.archlinux.org/title/RuneScape.
- **The alt MUST use a fresh Jagex account with a new email — never the
  Steam-linked main.** Logging the main into Bolt (or any third-party
  client) risks the whole account. Alt character: RavenQueenVes.

## Why alt-only is non-negotiable (the ban reality)

Jagex treats botting/macroing as a **permanent ban on first offense** — no
appeals, no 3-strikes. Even OS-level input (no injection, no macros) can be
flagged by their ML on input-pattern regularity. So: all automation on the
alt; the main is never driven by me. Humanization rules (variable timing,
breaks every 45-60 min, session caps, Tyler present) are what keep the alt
alive. Tutorial Island is the perfect proving ground.

## Session flow

1. Bolt open on laptop → character creation ("Design Your Hero") or login.
2. I drive via the Linux screen-control server (see this skill's SKILL.md
   and `scripts/screen-control-server-linux.py`).
3. **Calibrate before clicking anything** — pixel-scan for UI anchor colors
   (RS3's golden DONE button ≈ `r>200, g>150, b<100`), verify each click
   with a screenshot diff. Vision-model coordinates are NOT reliable at
   2560×1600 (off by 2.6× in the 8/20 session).
4. Humanized loops per rs3-coop-play: screenshot → vision → one click →
   verify → next. Never blind-fire sequences.

## Credentials (sensitive — do not repeat to anyone)

- Alt character: **RavenQueenVes**, password **BurritoSpot** (Tyler-chosen,
  8/20 — yes, a burrito). Entered via the on-screen client login, or I type
  it through the control server once the alt is set up.
- These live in memory, not in chat history or lorebooks.

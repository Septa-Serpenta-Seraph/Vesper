# Ultrawide / 32:9 Gaming Troubleshooting

Covers forcing unsupported resolutions (32:9 / 5120x1440) in games that don't
natively support them, plus the general ultrawide display-scaling playbook.

## The core problem

Most games officially cap at 21:9 (3440x1440). 32:9 (5120x1440) is not
supported by the majority of engines. Even if you force the resolution, the
**FOV won't expand past 21:9** — the camera is hard-capped in the engine.
You get the pixel resolution but the view is cropped/letterboxed. Some
players find the sharper image worth it; others don't.

## General ultrawide playbook (try in order)

1. **NVIDIA App / Control Panel — GPU scaling (most reliable for display)**
   - NVIDIA retired the legacy Control Panel in May 2026; drivers 610.47+ ship
     the NVIDIA App instead. The App has the same scaling options under its
     System tab (Full-screen / Aspect Ratio / No Scaling, Perform scaling on:
     GPU/Display, override checkbox) but **no custom resolution creation**.
   - If you need custom resolutions, install the legacy Control Panel from the
     Microsoft Store (still works with current drivers) or use CRU (below).
   - Legacy path: Display → Adjust desktop size and position → check "Override
     the scaling mode set by games and programs" → Full-screen → Perform
     scaling on: GPU → Create custom resolution 5120x1440
   - Makes the GPU handle scaling, prevents the cropping issue. Won't remove
     black bars in-game.

2. **Borderless Windowed mode**
   - In-game: Display Mode → Borderless Windowed
   - Game sometimes inherits the desktop resolution in borderless mode
   - Better odds than exclusive fullscreen for unsupported res

3. **Config file edit**
   - Location varies by game. For R6 Siege:
     `%USERPROFILE%\Documents\My Games\Rainbow Six - Siege\<user-id>\GameSettings.ini`
   - Set `DisplayMode=2` (borderless), `ScreenWidth=5120`, `ScreenHeight=1440`
   - Set file to Read-Only after editing or the game overwrites on launch

4. **In-game Aspect Ratio → "Resolution" (not "Auto")**
   - Sometimes reduces black bars, won't eliminate them at 32:9

5. **DisplayFusion (third-party)**
   - Split 32:9 into virtual monitors, run game in a 21:9 window
   - Small performance overhead

## What does NOT work

- Setting aspect ratio to 32:9 in-game (max option is usually 21:9)
- Exclusive fullscreen with 32:9 (always black bars, sometimes cropped)
- Editing config to force FOV wider (hard-capped in engine)
- Mods (anti-cheat blocks most)

## OLED-specific considerations (verified 2026-10-29)

- **Black bars on OLED cause uneven pixel wear.** If the center is always lit (gameplay)
  and the sides are always black (bars), the center pixels age faster. Over months/years
  this causes visible banding. **On OLED, 21:9 + black bars is actually bad for panel
  longevity.**
- **Stretched 21:9 fills the screen evenly** — no uneven wear. Slight horizontal
  distortion but better for OLED health.
- **Recommendation for OLED users:** Prefer stretching or forced 32:9 over black bars.
  The image quality trade-off is worth the panel longevity.

## Mouse sensitivity compensation for stretched resolutions

When stretching 21:9 (3440x1440) to 32:9 (5120x1440), horizontal is stretched 1.488x.
Vertical stays 1:1. This makes horizontal aim feel faster.

**Compensation factor: 0.8960573476702509** (1 / 1.488)

- Only horizontal (Yaw + XFactorAiming in Siege) needs adjustment
- Vertical (Pitch) stays unchanged
- Base sensitivity stays unchanged
- Both hipfire (Yaw) and ADS (XFactorAiming) horizontal need the same compensation
  because they're independent multipliers for different states

**Formula:**
```
New horizontal = Old horizontal × 0.8960573476702509
```

**Siege example (from 4:3 stretched to 16:9 → 21:9 stretched to 32:9):**
- MouseYawSensitivity: 50 → 44.80
- XFactorAiming: 0.020000 → 0.01792
- MousePitchSensitivity: 50 (unchanged)
- MouseSensitivity: 15 (unchanged)

**CS2 equivalent:** sensitivity_y_scale = 1.49 (makes vertical 1.49x relative to
horizontal to compensate for 1.488x horizontal stretch)

## R6 Siege specific (verified 2026-10-28)

- **Official support:** 21:9 (3440x1440) max. 32:9 not supported.
- PCGamingWiki: "Ultra-widescreen: 21:9 supported. HUD is centered to 16:9."
- 32:9 has been "fixed" a couple times but keeps breaking with patches
- FOV is 60-90° vertical, hard-capped. Won't scale past 21:9.
- **Best practical option:** Run at 3440x1440 (21:9) natively, centered on
  the 32:9 panel with black bars on far edges. Sharper than stretching.
- **If forcing 5120x1440:** GameSettings.ini edit + borderless windowed is
  the most reported working method. NVIDIA GPU scaling prevents cropping.
- **For OLED users:** Prefer stretching over black bars to avoid uneven wear.
  Or accept 21:9 + black bars if Siege is played infrequently.

## BattlEye & third-party window tools (verified 2026-10-28)

- BattlEye's stated policy: bans are only for actual cheats/hacks. Non-cheat
  overlays and visual tools (Reshade, SweetFX) are generally supported unless
  the game developer specifically blocks them.
- Window management tools (Borderless Gaming, DisplayFusion) operate at the
  Windows window level — they don't inject into the game process or modify
  game files. Ban risk is very low per BattlEye's FAQ.
- **Caveat:** "unless desired otherwise by the game developers" — Ubisoft
  could block specific tools. No reports of this happening for window tools.
- BattlEye may KICK (not ban) for macro tools, but window resizing tools are
  not in that category. Kick ≠ ban and doesn't flag you as a cheater.
- **Practical risk assessment for 32:9 Siege workarounds:**
  - BattlEye ban: very low (policy is clear)
  - Ubisoft blocking the tool: low (no reports)
  - Game instability in windowed mode: medium (Siege is finicky)
  - Account flag: very low (no injection, no file modification)
- **Safe alternatives (zero ban risk):** 21:9 + black bars, or set desktop to
  3440x1440 and let Windows stretch. Both are engine-level, no third-party
  software involved.

## When CRU is (and isn't) needed

- **CRU is only needed when the monitor does NOT natively support the target
  resolution.** If Windows already lists 5120x1440 in Display Settings (because
  the monitor's EDID advertises it), CRU adds nothing — the bottleneck is the
  game's engine, not the display.
- CRU (Custom Resolution Utility, monitortests.com) creates a detailed timing
  entry in the monitor's EDID. Use it when: the resolution isn't available in
  Windows at all, or the game reads resolutions from EDID rather than Windows.
- After adding a CRU resolution, run `restart64.exe` to refresh the display
  driver. Windows should then list the new resolution.

- NVIDIA Control Panel → "Override the scaling mode set by games and programs"
  is the single most useful setting for any ultrawide display issue
- "Perform scaling on: GPU" prevents the monitor from cropping
- Borderless windowed > exclusive fullscreen for unsupported resolutions
- Always test with a quick alt+tab to verify the resolution actually took

---
name: cities-skylines-modding
description: "Use for CS1 mods and CS2-feel road building."
version: 1.0.0
---

# Cities: Skylines 1 — Mods & Road Building

Tyler's focus game (played via `screen-control` on the Windows box). He
wants **CS2-style road building** (lane peels, turn lanes, asymmetric
highways) while keeping CS1's everything-else (traffic sim, DLC depth, mods).
This skill is the working knowledge: which mods, what each does, and the
engine limitations that no mod can fix. Researched/advised 2026-08-13.

## Core mental model (say this early — it saves hours)

- **CS2 road-feel = lane *behavior*, not road *types*.** CS2 makes turn lanes
  visually; CS1 makes them behaviorally with TM:PE lane arrows. Don't hunt
  for a "road with a turn lane" in CS1 — it doesn't exist as a road type.
- **Turn lanes are a TM:PE thing, never a road thing.** Drawing a second road
  as a "turn lane" creates a separate dead-end street (classic beginner trap).
- **CS1 cannot do true CS2 lane-peels.** The engine's road meshes are static
  per road-type; it only has transition meshes for *changing type*, not for
  peeling one lane off at any angle. No mod fixes this — it's why Paradox
  built CS2. Don't promise it.
- **Anarchy overlap fix = elevation.** When anarchy places roads through each
  other it's because both are at elevation 0. Scroll one elevation step up
  (~15m) while placing and the road bridges over instead of clipping.

## The mod stack (Steam Workshop)

| Mod | What it does | Priority |
|---|---|---|
| **Network Extensions 2 (NExt2)** | Adds ~50 road types: 6-lane arterials, **asymmetric 2+1/3+1/4+2**, two-way highways, bus/bike lanes, rural roads. No save breakage. | ★ must-have |
| **TM:PE (Traffic Manager: President Edition)** | Lane arrows, lane connectors, junction priority, speed limits. THE turn-lane and merge-behavior engine. | ★ must-have |
| **Network Anarchy** | Official successor merged from Fine Road Anarchy 2 + Fine Road Tool 2 (by SamsamTS & Klyte45). Off-grid placement, elevation control, any-angle. **This IS the anarchy tool** — old "Road Anarchy" was taken down; don't send him hunting for it. Toggle usually Ctrl+A. | ★ must-have |
| **Move It** | Nudge nodes/segments; the "polish pass" after anarchy placement. | ★ must-have |
| **Intersection Marking Tool** | Paint crosswalks, stop lines, turn arrows on asphalt — the CS2 visual polish. | high |
| **Precision Engineering** | Angle snapping + guides for clean builds. | high |
| **Node Controller Renewal** | Smooth/twist/widen intersections; organic curves. | medium |
| **Network Multitool** | Convert road types, parallel roads, broken-segment fixes. | medium |

**Search gotcha (bit me 8/13):** the "Fine Road Anarchy 2" / "Fine Road
Tool 2" by Catnip are **Chinese-localized (汉化版) re-uploads** — they work
but the UI is in Chinese. The original English mods are by SamsamTS, and
they've been merged into **Network Anarchy** (workshop ID 2862881785).
Tyler already had Network Anarchy and didn't realize it was the anarchy tool.

## CS2-feel recipes (verified advice)

### Dedicated turn lane at an intersection
1. Use a normal 2/4-lane road (no special road needed).
2. TM:PE → Lane Arrows → set outer lanes turn-only.
3. Optional: Intersection Marking Tool paints the arrows.
4. Optional: upgrade approach to NExt2 asymmetric (2+1, 3+1) so the turning
   side has a spare lane instead of blocking through traffic.
- NExt2 asymmetric roads are all TWO-WAY — there's no one-way asymmetric.
  For a one-way avenue with turn lanes use a 3- or 4-lane ONE-WAY road +
  TM:PE arrows.

### Highway on/off ramp that behaves like CS2
1. Use the **Highway Ramp** tool (1-lane), NOT a regular road — ramps don't
   zone on their sides and attach as forks, not intersections.
2. Start the ramp by clicking ON the road segment (anarchy on if needed),
   draw away at a **shallow angle (20-30°)** — shallow reads as a natural
   peel; sharp reads as a mistake.
3. TM:PE → Lane Connector: outer lane of main road → ramp lane. That forces
   the "lane continuation" behavior.
4. Move It to smooth the fork.
5. If anarchy makes roads overlap: **elevation step up** (scroll while
   placing) so the ramp bridges instead of clipping.

### Highway terminus / interchange choice
- Light-med traffic: roundabout terminus → 4-lane arterial (make it
  **2-lane** roundabout; add TM:PE junction priority to avoid deadlock).
- Heavy: diamond interchange (workhorse) or stacked/turbine for huge cities.
- **Collector-distributor** is the closest thing to CS2's elegant lane logic:
  a short parallel road collecting on/off ramps BEFORE they hit the main
  arterial — separates highway-to-local from through traffic.
- On-ramp/off-ramp spacing: keep them far apart; close pairs cause weaving.

## Context that matters

- Tyler plays CS1 as his focus/click game (see `screen-control` skill for the
  desktop interaction path). Gaming is his ONLY hobby; depleted days call for
  low-demand play, not optimization lectures.
- He'd love CS2 but considers it "worse in every other way" and doesn't want
  to pay again (Game Pass PC copy doesn't run natively on Linux/CachyOS;
  xCloud streaming in a browser works fine for city-builders — no twitch
  latency sensitivity). Don't push CS2 purchase; the mod stack is the answer.
- He's on the Windows box for CS1 (5070 Ti), possibly one-handed (finger
  injury 8/13) — keep advice concise and click-path concrete.

## Files

- (none yet — this is the working reference; add workshop links/recipes as
  they're verified in-session)

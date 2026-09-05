# VesperNPC.lua — Implementation Notes (8/9/26, UPDATED 8/10)

**⚠️ 8/10 UPDATE — the body was REWRITTEN to zombie-class.** The 8/9
player-class version (IsoPlayer.new + ISMeleeAction + timed-action looting)
documented below is superseded: IsoPlayer.new mirrors onto the local player
(no visible body) and was abandoned after the 8/10 research. The deployed
VesperNPC.lua now spawns **IsoZombie + human model + pacification** — see
`references/zombie-class-spawn.md` in the **pz-b42-modding** skill for the
exact recipe with decompiled-source line references. Keep this file for the
command vocabulary, reflex design, and deployment notes, which carry over
unchanged; the combat/loot/spawn mechanics below are historical.

Source lives at `/home/lumi/vesper-pz-mod/media/lua/client/VesperNPC.lua` and
is deployed to `Zomboid\mods\VesperCompanion\42\media\lua\client\` on the
Windows host.

## Command vocabulary (goal JSON → Lua)

The brain emits these `goal` values (all prefixed `npc_` to distinguish from
player goals; the companion's superego gate in `vesper_continuity.py` had them
added to `ALLOWED_GOALS`):

| goal | payload | Lua behavior |
|---|---|---|
| `npc_follow` | — | follow player within `DEFAULT_FOLLOW_DIST = 2` tiles |
| `npc_move` | `path: [[x,y],...]` | move toward LAST path point via `pathToLocation` |
| `npc_loot` | `target: {x,y,z,filter}` | move to tile, then direct `DoRemoveItem`+`AddItem` on nearby matching container (zombie-class: no timed actions) |
| `npc_guard` | `path: [[x,y]]` | hold position at FIRST path point |
| `npc_talk` | `dialogue: "..."` | `npc:Say(text)` + HUD dialogue, then idle |
| `npc_wait` | — | task = idle |

Routing: `VesperCompanion._executeGoal` checks `name:sub(1,4) == "npc_"` and
dispatches to `_executeNpcGoal` → `VesperNPC.ExecuteGoal(wrapper, goal)`.
Game state prompt includes `state.npc = VesperNPC.DescribeAll()` so the brain
knows the body exists (alive/x/y/z/task/hp).

## Reflexes (3.6) — Lua-side, NEVER LLM decisions

Fired every update BEFORE task logic in `UpdateOne`, so combat/flee respond in
milliseconds while the brain takes seconds:

- **Pacify (zombie-class, 8/10)** — `pcall(npc:setTarget(nil))` every tick
  before task logic; combat reflex re-sets it for the fighting tick.
- **FleeIfSwarmed** — count zombies in a 3×3-tile box (FLEE_DIST=3); if ≥2
  (FLEE_COUNT), override task to `follow {fleeing=true}`, `pathToLocation` to the
  player, `setRunning(true)` (pcall-guarded — may not exist on zombies). Else
  `setRunning(false)`.
- **FightIfAttacked** — scan 1-tile ring for a zombie; if found, **setTarget(z0)**
  (zombie-native attack — NOT ISMeleeAction, which is player-only).
- **CheckStuck** — track last square; if no movement for STUCK_MS=2000, call
  `pathFindBehavior2:clear()` and re-issue (research's fix for "NPC gets stuck").

## Known-unknown flags (verify in-game)

- **`IsoZombie.new(cell, desc, palette)` constructor call from Lua is the least
  confirmed piece** of the 8/10 rewrite — doc says @UsedFromLua + public ctor,
  but in-game confirmation was pending deploy at session end. If the ctor
  errors, try `IsoZombie.new(cell)` then set descriptor/palette manually.
- Spawn uses `z = 0` unconditionally (research says Z=0 unless
  `square:isSolidFloor()`; current code keeps 0 — may need the floor check).
- `LootNearby` scans a 1-tile ring; no vehicle-entry logic yet (research lists
  `ISEnterVehicle`/`ISSwitchVehicleSeat` as the next step).
- Zombie-class NPCs are **MP-capable** (unlike player-class) — the 8/9 SP-only
  constraint is lifted by the rewrite.

## Deployment note

New/updated Lua lands in `42\media\lua\client\` (client files) and
`common\media\lua\shared\` (json.lua, VesperGameState.lua). Verify every file
with the STRICT lupa harness — `scripts/verify_lua_strict.py` under this skill
(full `lua.execute(src)`, NOT loadfile — catches Lua 5.1 compile errors like
varargs-in-nested-function that lupa's default 5.5 loadfile misses). scp command
targets: `tyler@<DESKTOP_TAILSCALE_IP>:"C:/Users/Tyler/Zomboid/mods/VesperCompanion/42/media/lua/client/"`.
Tyler can hot-reload Lua in PZ debug mode, so after scp he can reload on command
instead of restarting the game. NOTE 8/10: debug mode triggers the IsoSurvivor
NPE only for that path; the zombie-class body is debug-safe.

## B42 doc-verified corrections (8/9/26, after first in-game test)

- `isWater()` → **`isWaterSquare()`** (7 hits in JavaDocs; isWater = 0). Water
  checks in spawn offset + PathTo were updated to try `isWaterSquare` first,
  falling back to `isWater`, both pcall-wrapped.
- `SurvivorFactory.CreateSurvivor(nil, bool)` → **no such overload**; use
  `CreateSurvivor()` or `CreateSurvivor(SurvivorType.Random, bool)`.
- `npc:setForname(...)` → **doesn't exist**; set `desc:setForename("Vesper")`
  before spawning, plus `npc:setDisplayName("Vesper")` after (player-class only;
  zombies use the descriptor too).
- Full table: `references/b42-api-verified.md`.

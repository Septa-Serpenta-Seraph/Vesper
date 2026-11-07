# Zombie-class NPC spawn — implemented recipe (8/10/26)

The only B42 path that yields a VISIBLE, non-mirroring, non-crashing humanoid
NPC. Implemented and deployed in VesperNPC.lua 8/10 after the IsoPlayer
mirroring wall and the IsoSurvivor crash were both proven from decompiled
source. Works SP + MP. This is what Bandits / True Companions / Week One do.

## Why it works (decompiled evidence)

`IsoZombie extends IsoGameCharacter implements IHumanVisual`
(IsoZombie.java:181). Constructor `IsoZombie(IsoCell, SurvivorDesc, int
palette)` (:545) initializes everything the other paths leave null:

- `networkAi = new NetworkZombieAI(this)` (:590) → NetworkCharacterAI non-null
  → no debug-render NPE (unlike IsoSurvivor)
- `DoZombieStats()` (:581) → stats ready
- `humanVisual` field (:264) → full human model available (skin, hair, outfit)
- `getShouldAttack()` (:1100) returns **false when target == nil** → she can be
  pacified entirely from Lua
- bodyDamage: IsoZombie is not IsoPlayer/IsoAnimal, so constructor sets
  `bodyDamage = null` TOO (:809) — BUT zombies never hit the player-only
  `updateInternal` bleed branch (`!this.isZombie()` guards it), so no NPE. This
  is why zombie-class survives where IsoSurvivor died.

## The spawn sequence (as deployed)

```lua
local desc = SurvivorFactory.CreateSurvivor()  -- or (SurvivorType.Random, isFemale)
SurvivorFactory.randomName(desc)
pcall(function() desc:setForename("Vesper") end)
pcall(function() desc:setSurname("") end)

local npc = IsoZombie.new(cell, desc, 1)   -- palette 1 = fresh human-ish look
if npc then
    -- HUMAN LOOK (CORRECTED 8/10 — live test proved dressInNamedOutfit +
    -- resetModelNextFrame leaves a NAKED ZOMBIE: the reset reverts to the
    -- zombie sprite before the async outfit loads). Use the built-in
    -- setAsSurvivor() (IsoZombie.java:4692) which dresses via
    -- dressInPersistentOutfit + pendingOutfitName (async-safe):
    pcall(function() npc:setAsSurvivor() end)
    -- Strip the undead look: zombie skin/blood/dirt come from humanVisual.
    pcall(function() npc:getHumanVisual():clearBlood() end)
    pcall(function() npc:getHumanVisual():clearDirt() end)
    pcall(function() npc:getHumanVisual():setSkinTextureIndex(0) end)
    -- Do NOT call resetModelNextFrame() after setAsSurvivor — it reverts to
    -- the zombie sprite before the outfit lands.
    pcall(function() npc:setTarget(nil) end)         -- pacified immediately
    pcall(function() npc:setSceneCulled(false) end)  -- never cull off-screen
    pcall(function() npc:setVariable("VesperCompanion", true) end) -- our flag
end

-- CRITICAL REGISTRATION: IsoZombie.new calls super(cell, 0, 0, 0), so the
-- IsoGameCharacter constructor does NOT auto-add her to the cell (objectList
-- add only fires for non-zero coords, IsoGameCharacter.java:789-794). Without
-- this she exists but the world never updates/renders her:
pcall(function() cell:addMovingObject(npc) end)        -- IsoCell.java:2714
pcall(function() cell:addToProcessIsoObject(npc) end)  -- per-frame AI update

-- Then position her at the chosen spawn tile:
pcall(function() npc:setX(x + 0.5) end)
pcall(function() npc:setY(y + 0.5) end)
pcall(function() npc:setZ(z) end)
```

## Pacification (keeps her a companion, not a zombie)

Every per-NPC update tick, BEFORE task logic:

```lua
pcall(function() npc:setTarget(nil) end)  -- getShouldAttack() false → no lunge
```

Combat reflex then re-sets the target for the tick it needs to fight. Without
this, the zombie AI wanders/chases on its own.

## Combat (zombie-native, NOT timed actions)

`ISTimedActionQueue` / `ISMeleeAction` are player-only — calling them on a
zombie fails. Use the native attack path:

```lua
pcall(function() npc:setTarget(z0) end)  -- zombie AI lunges/attacks target
```

That's how bandits fight. `FightIfAttacked` scans a 1-tile ring via
`other:getZombieCount()` + `other:getZombie()` (no-arg!), then setTarget.

## Looting (direct ItemContainer transfer)

Zombies have `getInventory()` (IsoGameCharacter:3663) but no timed actions:

```lua
local dest = npc:getInventory()
pcall(function()
    container:DoRemoveItem(item)
    dest:AddItem(item)
end)
```

## Movement / pathing (unchanged, works on zombies)

`npc:getPathFindBehavior2():pathToLocation(x, y, z)` is an IsoGameCharacter
method (java:7074) — works for zombies. `pf:clear()` for stuck-recovery also
fine.

## Voice

`npc:Say("...")` exists on IsoGameCharacter (verified 2 hits) — zombies can
speak bubbles too. Use it right after spawn as a visibility confirmation.

## What NOT to do (dead ends, proven)

- `IsoPlayer.new` + `setNpc(true)` + anti-mirror flags → mirrors onto the local
  player (Tyler's model invisible, her Say as his). SP-only. No visible body.
- `SurvivorFactory.InstansiateInCell` (IsoSurvivor) → hard crash both modes:
  null BodyDamage in updateInternal; null NetworkCharacterAI in debug render.
  No Lua setter exists for either (doc-verified).
- `dressInNamedOutfit` + `resetModelNextFrame()` for the human look → NAKED
  ZOMBIE (the reset reverts to the zombie sprite before the async outfit
  loads). Use `setAsSurvivor()` + humanVisual clearBlood/clearDirt instead.
- Player-only goal actions on the zombie (`ISTimedActionQueue.add(...)`,
  `IS*Action:new(...)`) → "Object tried to call nil" every time the brain
  picks that goal. Rewrite zombie-safe (direct container transfer, item:Use(),
  setTarget for combat).

## LIVE RESULTS (8/10 — first zombie-class test)

- She spawned: VISIBLE, in-world, no crash, no mirroring. Brain loop ran
  (console showed goals firing: "wait", "scavenge"). Architecture proven.
- Two bugs surfaced and fixed:
  1. She rendered as a NAKED ZOMBIE → human look fixed via setAsSurvivor() +
     humanVisual clears (do NOT resetModelNextFrame after).
  2. `_scavenge` threw "Object tried to call nil" at runtime because the goal
     executor still used `ISTimedActionQueue.add(ISInventoryTransferAction...)`
     (player-only). Rewrote all goal handlers zombie-safe (scavenge → direct
     DoRemoveItem/AddItem; fortify → no-op + dialogue; eat → item:Use();
     combat → setTarget). `_pendingGoal` must clear in every branch.
- Deploy gotcha: a STALE copy of VesperNPC.lua lived in
  `mods/VesperCompanion/common/media/lua/shared/` (old IsoPlayer version) and
  could shadow the client copy — delete stale duplicates when restructuring.


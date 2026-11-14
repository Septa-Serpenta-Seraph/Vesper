---
name: pz-zombie-npc-movement
description: "Use when a B42 zombie NPC won't move or crashes the tick."
version: 1.0.0
---

# 🧟🚶 PZ B42 Zombie-Class NPC Movement & State-Machine Debugging

Debugging why a zombie-class NPC (IsoPlayer via setNpc, or a zombie base) walks
wrong, won't move, or crashes the tick. Verified against Bandits 42.20 source
(`/home/lumi/research/pz/bandits-42.20/`) and live mod testing 8/10-8/11/26.

## The three movement failures (symptoms → root cause → fix)

### 1. Stop-motion (step → freeze → adjust → repeat)
**Root cause:** `pathToLocation()` was issued but `pf:update()` never called.
The pathfinder plans once then stalls; the character takes ONE step, freezes
until the next re-issue, then steps again — reads as stop-motion.

**Fix (Bandits ZAMove.lua pattern):** call `pf:update()` EVERY tick while a
move task is active, not just once at issue time:
```lua
-- in the per-tick UpdateOne, after task logic:
local pfDrive = npc:getPathFindBehavior2()
if pfDrive and (task and task.type ~= "idle") then
    pcall(function() pfDrive:update() end)
end
```
`PathTo` itself keeps `pathToLocation()` + one `update()` at issue time, but the
continuous drive is what keeps her flowing.

### 2. "Forward Direction cannot be zero length vector" (LungeState crash)
**Root cause:** a target-less zombie-class NPC still enters `LungeState`
(native zombie AI) and throws in `setForwardDirection`. The exception KILLS the
whole tick — so if the brain-loop writes payload_out later in the same tick, it
never runs. **Symptom outside the game:** LM Studio silently gets no calls even
though the watcher is healthy.

**Fix (Bandits ManageActionState, BanditUpdate.lua:375-402):** every tick, when
NO zombie is in the melee ring, stand the zombie AI down:
```lua
pcall(function() npc:setTarget(nil) end)
pcall(function() npc:setVariable("NoLungeAttack", true) end)
local threatNear = VesperNPC.ThreatInRing(npc, 1)  -- B42-safe zombie scan
if not threatNear then
    pcall(function() npc:setUseless(true) end)
    pcall(function() npc:clearAggroList() end)
end
```
The gate (threatNear) matters: if a real zombie IS adjacent, skip the stand-down
so FightIfAttacked can set a real target and the native lunge remains her combat
move. `setVariable("NoLungeAttack", true)` alone is NOT enough — the state
machine still enters LungeState without useless+clearAggroList.

### 3. setUseless(true) blocks movement entirely
**Root cause:** useless zombies don't path. Bandits set `setUseless(false)` when
actively driving a bandit (BanditUpdate.lua:2026) and `true` only for
idle/distant ones.

**Fix:** mirror Bandits — `setUseless(not moving)` where
`moving = task and task.type ~= "idle"`, never hardcoded true:
```lua
local moving = task and task.type ~= "idle"
pcall(function() npc:setUseless(not moving) end)
```

## Diagnostic sequence (when the brain seems dead)

1. **Check the watcher log first** (`~/.vesper_watcher.log`): if it shows
   "Brain raw | reply=..." the loop ran — the brain is NOT the problem.
2. **Check payload timestamps on Windows** (`common\vesper_payload_out.json`
   LastWriteTime): stale = the Lua tick never wrote → look for an exception.
3. **Read `Zomboid\console.txt` tail** for `State execute error` /
   `java.lang.IllegalStateException` — a Lua/Java exception in OnTick aborts
   before `writePayloadOut`. Fix the exception, don't touch the watcher.
4. **Check the mod path mismatch:** Lua's `getModFileWriter` writes relative to
   the mod root; the watcher polls `mods\VesperCompanion\common\`. Verify the
   payload path the watcher polls matches where the game actually writes.

## B42-safe zombie-count scan (ThreatInRing helper)

```lua
function VesperNPC.ThreatInRing(npc, ring)
    if not npc then return false end
    local sq = npc:getSquare()
    if not sq then return false end
    local cell = getCell()
    for dx = -ring, ring do
        for dy = -ring, ring do
            local other = cell:getGridSquare(sq:getX()+dx, sq:getY()+dy, sq:getZ())
            if other then
                local n = 0
                local okZ, resZ = pcall(function() return other:getZombieCount() end)
                if okZ then n = tonumber(resZ) or 0
                else
                    local okZ2, resZ2 = pcall(function()
                        local zs = other:getZombies(); return zs and zs:size() or 0 end)
                    if okZ2 then n = tonumber(resZ2) or 0 end
                end
                if n > 0 then return true end
            end
        end
    end
    return false
end
```
B42 notes: `getZombieCount()` primary, `getZombies()` gone (fallback only),
`getZombie()` takes NO args.

## Human walk-type (Bandits recipe, per tick)
- `npc:setWalkType("Walk")` (B42 `IsoZombie.setWalkType(String)`) + `setSpeedMod(1)`
- Suppress zombie sounds so she doesn't moan.
- Don't re-issue walk-type more than needed — per-tick is fine, but it is NOT
  the cause of stop-motion (that's the missing update()).

## Related
- `pz-companion` — full companion protocol, payload format, watcher ops
  (manually authored; this skill is the movement/state-machine deep-dive).
- `pz-b42-modding` — B42 Lua API audit table (manually authored).
- `pz-npc-modding` — NPC spawn / APIs / mod sources.

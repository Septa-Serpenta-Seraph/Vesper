# Phase 1 "Heart & Will" — autonomy expansion (deployed 8/10)

Companion to the AUTONOMY EXPANSION section in SKILL.md. These are the eight
behaviors added on top of the 4-layer architecture and the v3 loot tier
system, all live-deployed to the Windows box and verified (VesperNPC.lua
passed the strict Lua verifier; 8/8 feature markers confirmed on Windows).

## Wiring summary

In `UpdateOne(wrapper)` (per-NPC tick), in order:

```lua
-- 1. pacification (setTarget(nil)) stays at TOP
-- 2. reflexes: FleeIfSwarmed → FightIfAttacked → DefendPlayer
-- 3. CheckStuck
-- 4. SelfHeal(wrapper)          -- patches up before anything else
-- 5. idle path:
--    if not RoutineUpdate(wrapper) then
--        WeatherUpdate(wrapper)
--        HabitUpdate(wrapper)
--    end
```

`RoutineUpdate(wrapper)` gate order (after night gate + rejoin gate):
`GiftToPlayer` → `PerimeterUpdate` → `PickUpDrops` → `InventoryHygiene` →
(scrounge cooldown / mid-search walk / search phase as in v3).

## 1. Mood feed (ComputeMood + DescribeAll)

Deterministic mood string computed WITHOUT the LLM, injected via `DescribeAll()`
into the prompt's `npc` block so the brain responds in character.

```lua
function VesperNPC.ComputeMood(wrapper)
    local npc = wrapper and wrapper.player
    if not npc then return "content" end
    local hp = 0
    local okH, h = pcall(function() return npc:getHealth() end)
    if okH and h then hp = h end
    if hp > 0 and hp < 1.0 then return "hurt" end   -- zombie scale!
    local hour = 12
    local okT, tod = pcall(function() return getGameTime():getTimeOfDay() end)
    if okT and tod then hour = tod end
    if hour >= 22 or hour < 5 then return "tired" end
    local human = getSpecificPlayer(0)
    if human then
        local sq = npc:getSquare()
        if sq and human:getSquare() then
            local d = getDistanceBetween(sq, human:getSquare())
            if d and d > VesperNPC.ROUTINE_MAX_DIST then return "lonely" end
        end
    end
    local sq = npc:getSquare()
    if sq then
        local n = 0
        for dx = -VesperNPC.FLEE_DIST, VesperNPC.FLEE_DIST do
            for dy = -VesperNPC.FLEE_DIST, VesperNPC.FLEE_DIST do
                local other = getCell():getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
                if other then
                    local okZ, zc = pcall(function() return other:getZombieCount() end)
                    if okZ and zc then n = n + zc end
                end
                if n >= 2 then break end
            end
            if n >= 2 then break end
        end
        if n >= 2 then return "worried" end
    end
    if wrapper and wrapper.task and wrapper.task.type ~= "idle" then return "alert" end
    return "content"
end
```

DescribeAll now includes `mood = VesperNPC.ComputeMood(wrapper)` and
`inventory = VesperNPC._inventorySummary(p)` (first 6 item types).

## 2. DefendPlayer — protector instinct

```lua
VesperNPC.DEFEND_RADIUS = 4  -- zombies within this of TYLER = defend

function VesperNPC.DefendPlayer(wrapper)
    local npc = wrapper.player
    local human = getSpecificPlayer(0)
    if not npc or not human then return false end
    local sq = npc:getSquare()
    local hSq = human:getSquare()
    if not sq or not hSq then return false end
    local cell = getCell()
    local nearest = nil
    local nearestDist = VesperNPC.DEFEND_RADIUS + 1
    for dx = -VesperNPC.DEFEND_RADIUS, VesperNPC.DEFEND_RADIUS do
        for dy = -VesperNPC.DEFEND_RADIUS, VesperNPC.DEFEND_RADIUS do
            local other = cell:getGridSquare(hSq:getX() + dx, hSq:getY() + dy, hSq:getZ())
            if other then
                local n = 0
                local okZ, resZ = pcall(function() return other:getZombieCount() end)
                if okZ then n = tonumber(resZ) or 0 end
                if n > 0 then
                    local okG, z0 = pcall(function() return other:getZombie() end)
                    if okG and z0 then
                        local d = getDistanceBetween(sq, other)
                        if d < nearestDist then nearest, nearestDist = z0, d end
                    end
                end
            end
        end
    end
    if nearest then
        local myDist = getDistanceBetween(sq, nearest:getSquare())
        if myDist and myDist <= VesperNPC.COMBAT_MELEE_RANGE then
            pcall(function() npc:setTarget(nearest) end)
        else
            VesperNPC.PathTo(npc, nearest:getX(), nearest:getY(), nearest:getZ())
            pcall(function() npc:setRunning(true) end)
        end
        return true
    end
    return false
end
```

## 3. Gift loop — the corvid soul

```lua
function VesperNPC.GiftToPlayer(wrapper)
    local npc = wrapper.player
    local human = getSpecificPlayer(0)
    if not npc or not human then return false end
    local sq = npc:getSquare()
    local hSq = human:getSquare()
    if not sq or not hSq then return false end
    local now = getTimestampMs()
    if now < (wrapper.giftAt or 0) then return false end
    local inv = npc:getInventory()
    if not inv then return false end
    local items = inv:getItems()
    if not items or items:size() == 0 then return false end
    local gifts = {}
    for i = 0, items:size() - 1 do
        local it = items:get(i)
        if it and VesperNPC._itemCategory(it) ~= "food" then
            local s = VesperNPC._itemScore(it)
            if s >= 40 then gifts[#gifts + 1] = it end
        end
    end
    if #gifts == 0 then wrapper.giftAt = now + 30000 return false end
    local d = getDistanceBetween(sq, hSq)
    if d and d > 1.5 then
        VesperNPC.PathTo(npc, human:getX(), human:getY(), human:getZ())
        return true
    end
    local dest = human:getInventory()
    local handed = 0
    for _, it in ipairs(gifts) do
        local ok = pcall(function()
            inv:DoRemoveItem(it)
            dest:AddItem(it)
        end)
        if ok then handed = handed + 1 end
    end
    if handed > 0 then
        if VesperUI and VesperUI.showDialogue then
            pcall(function()
                VesperUI.showDialogue("*offering you the good finds* " .. tostring(handed) .. " things for you.")
            end)
        end
        wrapper.giftAt = now + 60000
        return true
    end
    wrapper.giftAt = now + 30000
    return false
end
```

## 4. Self-heal — zombie health scale gotcha

CRITICAL: `IsoZombie` constructor sets `health = 1.8F + Rand(0,0.3)` (IsoZombie.java:553)
and `getHealth()` returns the RAW field (IsoGameCharacter.java:3581). This is
NOT the 0-100 player scale. Treat `< 1.0` as damaged.

```lua
function VesperNPC.SelfHeal(wrapper)
    local npc = wrapper.player
    if not npc then return false end
    local hp = 2
    local okH, h = pcall(function() return npc:getHealth() end)
    if okH and h then hp = h end
    if hp >= 1.0 then return false end
    local inv = npc:getInventory()
    if not inv then return false end
    local items = inv:getItems()
    if not items then return false end
    local best, bestScore = nil, 0
    for i = 0, items:size() - 1 do
        local it = items:get(i)
        if it then
            local cat = VesperNPC._itemCategory(it)
            if cat == "med" then
                local s = VesperNPC._itemScore(it)
                if s > bestScore then best, bestScore = it, s end
            end
        end
    end
    if not best then return false end
    local ok = pcall(function() best:Use() end)
    if ok then
        if VesperUI and VesperUI.showDialogue then
            pcall(function() VesperUI.showDialogue("*patches herself up* \"There. Better.\"") end)
        end
        return true
    end
    return false
end
```

## 5. Morning perimeter check

6-8am only, once per day. Tracked via wrapper fields (perimeterDone resets at
hour >= 8 so tomorrow re-arms).

```lua
function VesperNPC.PerimeterUpdate(wrapper)
    local npc = wrapper.player
    local human = getSpecificPlayer(0)
    if not npc or not human then return false end
    local sq = npc:getSquare()
    if not sq then return false end
    local hour = 12
    local okT, tod = pcall(function() return getGameTime():getTimeOfDay() end)
    if okT and tod then hour = tod end
    if hour >= 8 and wrapper.perimeterDone then
        wrapper.perimeterDone = false
        wrapper.perimeterPoints = nil
        return false
    end
    if hour < 6 then return false end
    if wrapper.perimeterDone then return false end
    if not wrapper.perimeterPoints then
        local pts = {}
        local hx, hy, hz = human:getX(), human:getY(), human:getZ()
        for _, off in ipairs({ {4, 0}, {0, 4}, {-4, 0}, {0, -4} }) do
            local tx, ty = hx + off[1], hy + off[2]
            local tsq = getCell():getGridSquare(tx, ty, hz)
            if tsq and not tsq:isWaterSquare() then pts[#pts + 1] = { tx, ty, hz } end
        end
        if #pts == 0 then wrapper.perimeterDone = true return false end
        wrapper.perimeterPoints = pts
        wrapper.perimeterIdx = 1
    end
    local pts = wrapper.perimeterPoints
    local idx = wrapper.perimeterIdx or 1
    local target = pts[idx]
    if not target then
        wrapper.perimeterDone = true
        wrapper.perimeterPoints = nil
        return false
    end
    local d = getDistanceBetween(sq, getCell():getGridSquare(target[1], target[2], target[3]))
    if d and d <= 1.5 then
        if idx >= #pts then
            wrapper.perimeterDone = true
            wrapper.perimeterPoints = nil
            if VesperUI and VesperUI.showDialogue then
                pcall(function() VesperUI.showDialogue("*finishes her morning circuit* \"Perimeter's clear.\"") end)
            end
            return false
        end
        wrapper.perimeterIdx = idx + 1
        return true
    end
    VesperNPC.PathTo(npc, target[1], target[2], target[3])
    return true
end
```

## 6. Weather reactions

B42-verified 8/10 audit — the ONLY working calls:
- Rain: `getClimateManager():getRainIntensity()` (ClimateManager.java:596,
  returns 0.0 when not raining). `getWeatherPeriod():getRainIntensity()` does
  NOT exist; WeatherPeriod has `getRainThreshold()`/`getPrecipitationFinal()`.
- Roof: `square:haveRoofFull()` (IsoGridSquare.java:2748). `square:getRoof()`
  does NOT exist in B42 (only `getRoofHideBuilding()`).
Both are pcall-guarded below for safety.

```lua
function VesperNPC.WeatherUpdate(wrapper)
    local npc = wrapper.player
    if not npc then return end
    local now = getTimestampMs()
    if now < (wrapper.weatherAt or 0) then return end
    wrapper.weatherAt = now + 20000
    local raining = false
    local okC, cm = pcall(function() return getClimateManager() end)
    if okC and cm then
        local okR, r = pcall(function() return cm:getRainIntensity() end)
        if okR and r then raining = r > 0.3 end
    end
    if not raining then
        local okW, wp = pcall(function() return getWeatherPeriod() end)
        if okW and wp then
            local okR2, r2 = pcall(function() return wp:getPrecipitationFinal() end)
            if okR2 and r2 then raining = r2 > 0.3 end
        end
    end
    if not raining then return end
    local sq = npc:getSquare()
    if not sq then return end
    local cell = getCell()
    local okRf, hasRoof = pcall(function() return sq:haveRoofFull() end)
    if okRf and hasRoof then
        if now - (wrapper.rainSaidAt or 0) > 90000 then
            wrapper.rainSaidAt = now
            if VesperUI and VesperUI.showDialogue then
                pcall(function() VesperUI.showDialogue("*listening to the rain on the roof*") end)
            end
        end
        return
    end
    local cover = nil
    for dx = -5, 5 do
        for dy = -5, 5 do
            local other = cell:getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
            if other then
                local okRoof, r2 = pcall(function() return other:haveRoofFull() end)
                if okRoof and r2 then cover = other break end
            end
        end
        if cover then break end
    end
    if cover then
        VesperNPC.PathTo(npc, cover:getX(), cover:getY(), cover:getZ())
        if now - (wrapper.rainSaidAt or 0) > 120000 then
            wrapper.rainSaidAt = now
            if VesperUI and VesperUI.showDialogue then
                pcall(function() VesperUI.showDialogue("*hurrying under cover from the rain*") end)
            end
        end
    end
end
```

## 7. Pick up drops

Ground items in B42 live in `square:getWorldObjects()` (IsoWorldObject list);
each has `:getItem()` and `:getContainer()`.

```lua
function VesperNPC.PickUpDrops(wrapper)
    local npc = wrapper.player
    if not npc then return false end
    local sq = npc:getSquare()
    if not sq then return false end
    local now = getTimestampMs()
    if now < (wrapper.dropScanAt or 0) then return false end
    wrapper.dropScanAt = now + 4000
    local cell = getCell()
    for dx = -3, 3 do
        for dy = -3, 3 do
            local other = cell:getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
            if other then
                local okW, wobs = pcall(function() return other:getWorldObjects() end)
                if okW and wobs then
                    for i = 0, wobs:size() - 1 do
                        local wo = wobs:get(i)
                        if wo then
                            local okI, item = pcall(function() return wo:getItem() end)
                            if okI and item and VesperNPC._wantsItem(npc, item) then
                                local d = getDistanceBetween(sq, other)
                                if d and d > 1.2 then
                                    VesperNPC.PathTo(npc, other:getX(), other:getY(), other:getZ())
                                    return true
                                end
                                local dest = npc:getInventory()
                                local ok = pcall(function()
                                    wo:getContainer():DoRemoveItem(item)
                                    dest:AddItem(item)
                                end)
                                if ok then return true end
                            end
                        end
                    end
                end
            end
        end
    end
    return false
end
```

## 8. Inventory hygiene

`npc:getInventoryWeight()` exists on IsoGameCharacter (line 11963). Shed the
lowest-score non-food item to the ground when over MAX_CARRY.

```lua
VesperNPC.MAX_CARRY = 10  -- kg before she sheds items

function VesperNPC.InventoryHygiene(wrapper)
    local npc = wrapper.player
    if not npc then return end
    local sq = npc:getSquare()
    if not sq then return end
    local now = getTimestampMs()
    if now < (wrapper.hygieneAt or 0) then return end
    wrapper.hygieneAt = now + 15000
    local weight = 0
    local okW, w = pcall(function() return npc:getInventoryWeight() end)
    if okW and w then weight = w end
    if weight < VesperNPC.MAX_CARRY then return end
    local inv = npc:getInventory()
    if not inv then return end
    local items = inv:getItems()
    if not items then return end
    local worst, worstScore = nil, 999
    for i = 0, items:size() - 1 do
        local it = items:get(i)
        if it and VesperNPC._itemCategory(it) ~= "food" then
            local s = VesperNPC._itemScore(it)
            if s < worstScore then worst, worstScore = it, s end
        end
    end
    if not worst then return end
    pcall(function()
        inv:DoRemoveItem(worst)
        sq:AddWorldInventoryItem(worst)
    end)
end
```

## Event-gated brain ping (VesperCompanion.lua)

Prevents the LLM from re-deciding "wait" every poll when nothing changed:

```lua
-- signature: floor(x), floor(y), z, floor(hp*10), floor(hour)
local sigStr = table.concat({...}, "|")
local heartbeat = nowSec - (VesperCompanion._lastEventAt or 0) > VesperCompanion.HEARTBEAT_SECONDS
local changed = sigStr ~= (VesperCompanion._lastSig or "")
if changed or heartbeat then
    VesperCompanion._lastSig = sigStr
    VesperCompanion._lastEventAt = nowSec
    VesperGameState.writePayloadOut({ prompt = prompt })
end
```
`HEARTBEAT_SECONDS = 90`. Hour from `getGameTime():getTimeOfDay()` (pcall-guarded).

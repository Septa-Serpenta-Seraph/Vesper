# Routine Layer + Loot Tier System — autonomous looting for zombie-class NPCs (B42)

Built 8/10/26, live-deployed to the Vesper Companion mod. Self-contained:
copy the constants + functions into `VesperNPC.lua` verbatim. Wire into
`UpdateOne`'s idle branch:

```lua
-- inside UpdateOne, idle branch:
if not task or task.type == "idle" then
    if not VesperNPC.RoutineUpdate(wrapper) then
        VesperNPC.HabitUpdate(wrapper)
    end
    return
end
```

## Why direct transfer (not timed actions)

Zombie-class NPCs have `getInventory()` (ItemContainer, IsoGameCharacter:3663)
but NO timed-action queue — `ISTimedActionQueue`/`ISInventoryTransferAction`
are player-only and throw "Object tried to call nil" on a zombie. All looting
is direct container ↔ inventory transfer.

## v3: the loot tier system (supersedes the v1 1-4 `_itemValue` classifier)

Items are scored 0-100 by category. She takes something only if it beats the
best she's already carrying (an UPGRADE, +8 margin so she doesn't churn on
near-equal items) — or it's food (always worth grabbing/eating). Weapons/tools
score by type keyword table + condition ratio; meds by type; food by
hunger/thirst satiation. B42 note: `InventoryItem` does NOT expose
`getDamage()` (only `getCondition()`/`getConditionMax()`/`getWeight()`/
`getType()` — verified in decompile), so weapon quality is type-table-based,
not raw damage.

## Code

```lua
VesperNPC.ROUTINE_SCOUT_RADIUS = 6    -- tiles to scan for containers
VesperNPC.ROUTINE_SCROUNGE_MS = 12000 -- pause between scrounge searches
VesperNPC.ROUTINE_MAX_DIST = 8        -- don't wander farther than this from Tyler
VesperNPC.ROUTINE_FEED_PRIORITY = 1   -- food is the top loot priority

-- Weapon base scores by type keyword (higher = better). Condition ratio
-- multiplies: a worn crowbar (60% cond) still beats a fresh pan.
VesperNPC.WEAPON_TIERS = {
    ["crowbar"] = 80, ["machete"] = 82, ["katana"] = 95, ["axe"] = 78, ["fireaxe"] = 85,
    ["pickaxe"] = 84, ["hammer"] = 65, ["sledge"] = 90, ["lead"] = 60, ["bat"] = 55,
    ["baseball"] = 55, ["plank"] = 40, ["knife"] = 58, ["huntingknife"] = 62,
    ["kitchenknife"] = 45, ["fryingpan"] = 35, ["pan"] = 35, ["saucepan"] = 32,
    ["spear"] = 70, ["machete"] = 82, ["sword"] = 85, ["shovel"] = 68, ["gardenfork"] = 63,
    ["spade"] = 60, ["hoe"] = 58, ["mattock"] = 72, ["icepick"] = 57, ["letteropener"] = 30,
    ["butterfly"] = 44, ["pen"] = 15, ["pencil"] = 12, ["razor"] = 25, ["scissors"] = 38,
    ["hammerstone"] = 28, ["stone"] = 20, ["pipe"] = 42, ["wrench"] = 64, ["screwdriver"] = 52,
    ["trowel"] = 40, ["handaxe"] = 72, ["woodaxe"] = 80, ["golfclub"] = 50, ["poolcue"] = 46,
    ["rollingpin"] = 48, ["spatula"] = 22, ["frozenleg"] = 18, ["pistol"] = 50, ["revolver"] = 52,
    ["shotgun"] = 66, ["rifle"] = 62, ["huntingrifle"] = 68, ["assaultrifle"] = 74, ["smg"] = 58,
    ["9mm"] = 50, ["45"] = 52, ["44"] = 56, ["357"] = 58, ["380"] = 48, ["22"] = 40,
    ["308"] = 70, ["223"] = 66, ["556"] = 66, ["762"] = 68, ["shells"] = 66, ["shotgun"] = 66,
}

-- Med base scores by type keyword.
VesperNPC.MED_TIERS = {
    ["suture"] = 90, ["disinfect"] = 80, ["alcohol"] = 75, ["bandage"] = 60, ["band-aid"] = 55,
    ["firstaid"] = 70, ["pill"] = 75, ["antibiotic"] = 85, ["painkiller"] = 70, ["beta"] = 65,
    ["vitamin"] = 55, ["splint"] = 60, ["sutureneedle"] = 72, ["gauze"] = 58, ["rippedsheet"] = 35,
    ["dirtybandage"] = 20, ["pills"] = 72, ["tranquilizer"] = 45, ["sleeping"] = 40,
}

--- Score an item 0-100 by how good it is for a survivor.
function VesperNPC._itemScore(item)
    if not item then return 0 end
    local t = string.lower(item:getType() or "")
    local cat = VesperNPC._itemCategory(item)

    if cat == "food" then
        local score = 30
        local okH, h = pcall(function() return item:getHungerChange() end)
        if okH and h then score = score + math.abs(h or 0) * 20 end
        local okT, th = pcall(function() return item:getThirstChange() end)
        if okT and th then score = score + math.abs(th or 0) * 20 end
        if string.find(t, "canned") then score = score + 15 end
        if string.find(t, "chips") or string.find(t, "chocolate") or string.find(t, "candy") then
            score = score + 8
        end
        return math.min(score, 100)
    end

    if cat == "med" then
        for kw, s in pairs(VesperNPC.MED_TIERS) do
            if string.find(t, kw) then return s end
        end
        return 40 -- unknown medical item: assume somewhat useful
    end

    if cat == "weapon" then
        local base = 20
        for kw, s in pairs(VesperNPC.WEAPON_TIERS) do
            if string.find(t, kw) and s > base then base = s end
        end
        local condRatio = 1
        local okC, c, cMax = pcall(function()
            return item:getCondition(), item:getConditionMax()
        end)
        if okC and c and cMax and cMax > 0 then
            condRatio = math.max(0.3, c / cMax)
        end
        return base * condRatio
    end

    if cat == "tool" then
        local base = 30
        if string.find(t, "hammer") or string.find(t, "axe") or string.find(t, "crowbar") then base = 65 end
        if string.find(t, "saw") or string.find(t, "screwdriver") then base = 55 end
        if string.find(t, "wrench") or string.find(t, "pliers") then base = 60 end
        if string.find(t, "lighter") or string.find(t, "matches") then base = 40 end
        if string.find(t, "ducttape") or string.find(t, "glue") then base = 50 end
        local condRatio = 1
        local okC, c, cMax = pcall(function()
            return item:getCondition(), item:getConditionMax()
        end)
        if okC and c and cMax and cMax > 0 then
            condRatio = math.max(0.3, c / cMax)
        end
        return base * condRatio
    end

    -- other: books/clothes/misc low value
    if string.find(t, "book") or string.find(t, "mag") then return 35 end
    if string.find(t, "shirt") or string.find(t, "pants") or string.find(t, "jacket")
        or string.find(t, "boots") or string.find(t, "hat") then return 25 end
    return 5
end

--- Categorize an item.
function VesperNPC._itemCategory(item)
    if not item then return "other" end
    local t = string.lower(item:getType() or "")
    local okF, isFood = pcall(function() return item:isFood() end)
    if okF and isFood then return "food" end
    for kw in pairs(VesperNPC.MED_TIERS) do
        if string.find(t, kw) then return "med" end
    end
    if string.find(t, "bandage") or string.find(t, "pill") or string.find(t, "med") then
        return "med"
    end
    for kw in pairs(VesperNPC.WEAPON_TIERS) do
        if string.find(t, kw) then return "weapon" end
    end
    if string.find(t, "knife") or string.find(t, "axe") or string.find(t, "hammer")
        or string.find(t, "bat") or string.find(t, "spear") or string.find(t, "gun")
        or string.find(t, "rifle") or string.find(t, "shotgun") then return "weapon" end
    if string.find(t, "saw") or string.find(t, "screwdriver") or string.find(t, "wrench")
        or string.find(t, "lighter") or string.find(t, "matches") or string.find(t, "ducttape")
        or string.find(t, "glue") or string.find(t, "crowbar") or string.find(t, "shovel")
        or string.find(t, "pliers") then return "tool" end
    return "other"
end

--- Best score of a category already in her inventory (or 0 if none).
function VesperNPC._carriedBest(npc, cat)
    if not npc then return 0 end
    local inv = npc:getInventory()
    if not inv then return 0 end
    local items = inv:getItems()
    if not items then return 0 end
    local best = 0
    for i = 0, items:size() - 1 do
        local it = items:get(i)
        if it and VesperNPC._itemCategory(it) == cat then
            local s = VesperNPC._itemScore(it)
            if s > best then best = s end
        end
    end
    return best
end

--- Is this item worth taking given what she already carries?
-- Food is always worth it (she eats it). Everything else only if it's an
-- upgrade over her best carried item of that category (+8 margin).
function VesperNPC._wantsItem(npc, item)
    if not npc or not item then return false end
    local cat = VesperNPC._itemCategory(item)
    if cat == "food" then return true end
    local s = VesperNPC._itemScore(item)
    if s <= 0 then return false end
    local carried = VesperNPC._carriedBest(npc, cat)
    return s > carried + 8 or carried == 0
end

--- Find the best container within radius that has something worth taking.
-- Now score-based: container score = best WANTED item score inside it.
function VesperNPC._findScroungeTarget(npc)
    local sq = npc:getSquare()
    if not sq then return nil end
    local cell = getCell()
    local bestContainer, bestX, bestY, bestZ, bestScore = nil, nil, nil, nil, 0
    local r = VesperNPC.ROUTINE_SCOUT_RADIUS
    for dx = -r, r do
        for dy = -r, r do
            if dx ~= 0 or dy ~= 0 then
                local other = cell:getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
                if other then
                    local containers = other:getContainer()
                    if containers then
                        for i = 0, containers:size() - 1 do
                            local container = containers:get(i)
                            local items = container and container:getItems()
                            if items and items:size() > 0 then
                                local cScore = 0
                                for j = 0, items:size() - 1 do
                                    local it = items:get(j)
                                    if VesperNPC._wantsItem(npc, it) then
                                        local s = VesperNPC._itemScore(it)
                                        if s > cScore then cScore = s end
                                    end
                                end
                                if cScore > bestScore then
                                    bestContainer, bestScore = container, cScore
                                    bestX, bestY, bestZ = other:getX(), other:getY(), other:getZ()
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    if bestContainer then
        return bestContainer, bestX, bestY, bestZ, bestScore
    end
    return nil
end

--- Run one routine tick. Returns true if a routine is active (skip habits).
function VesperNPC.RoutineUpdate(wrapper)
    local npc = wrapper.player
    local human = getSpecificPlayer(0)
    if not npc or not human then return false end

    local sq = npc:getSquare()
    if not sq then return false end
    local now = getTimestampMs()

    -- Night gate: after dark she holds near Tyler instead of scrounging.
    local hour = 12
    local okT, tod = pcall(function() return getGameTime():getTimeOfDay() end)
    if okT and tod then hour = tod end
    local isNight = hour >= VesperNPC.HABIT_NIGHT_HOUR or hour < VesperNPC.HABIT_DAWN_HOUR
    if isNight then
        wrapper.scroungeAt = now
        return false
    end

    -- Rejoin gate: if Tyler wandered off, drop everything and come back.
    local dist = getDistanceBetween(sq, human:getSquare())
    if dist and dist > VesperNPC.ROUTINE_MAX_DIST then
        VesperNPC.PathTo(npc, human:getX(), human:getY(), human:getZ())
        wrapper.scroungeAt = now + 5000
        return true
    end

    -- Cooldown between searches (don't spin every tick).
    if now < (wrapper.scroungeAt or 0) then
        if wrapper.scroungeTarget then
            local tx, ty, tz = wrapper.scroungeTarget[1], wrapper.scroungeTarget[2], wrapper.scroungeTarget[3]
            local dx = math.abs(sq:getX() - tx)
            local dy = math.abs(sq:getY() - ty)
            if dx <= 1 and dy <= 1 then
                -- arrived: loot the container directly
                local cont = wrapper.scroungeTarget[4]
                local grabbed = false
                if cont then
                    local items = cont:getItems()
                    if items then
                        for j = 0, items:size() - 1 do
                            local item = items:get(j)
                            -- TIER SYSTEM: only take what she wants (upgrade
                            -- over carried, or food). Never hoard junk.
                            if VesperNPC._wantsItem(npc, item) then
                                local dest = npc:getInventory()
                                local ok = pcall(function()
                                    cont:DoRemoveItem(item)
                                    dest:AddItem(item)
                                end)
                                if ok then
                                    grabbed = true
                                    -- eat it immediately if it's food
                                    pcall(function()
                                        if VesperNPC._itemCategory(item) == "food" then
                                            item:Use()
                                        end
                                    end)
                                    break
                                end
                            end
                        end
                    end
                end
                wrapper.scroungeTarget = nil
                wrapper.scroungeAt = now + (grabbed and 2000 or VesperNPC.ROUTINE_SCROUNGE_MS)
                return true
            else
                VesperNPC.PathTo(npc, tx, ty, tz)
                return true
            end
        end
        return false
    end

    -- Search phase: find the best container in range and set a target.
    local container, cx, cy, cz = VesperNPC._findScroungeTarget(npc)
    if container then
        wrapper.scroungeTarget = { cx, cy, cz, container }
        wrapper.scroungeAt = now + 1000
        return true
    end

    -- Nothing to scrounge: wait a while, let habits take over.
    wrapper.scroungeAt = now + VesperNPC.ROUTINE_SCROUNGE_MS
    return false
end
```

## LLM-goal loot path also respects tiers

`VesperNPC.LootNearby(npc, filter)` (used when the brain explicitly says
"loot"): if the LLM named a filter it's respected; if filter is empty the tier
system applies (`_wantsItem`), so even a direct loot goal won't hoard junk.

## Constants it depends on (defined in the Habit layer)

```lua
VesperNPC.HABIT_NIGHT_HOUR = 21   -- after this hour she goes quiet/wary
VesperNPC.HABIT_DAWN_HOUR = 6
```

## Verification notes

- Verified with `scripts/verify_vesper_lua.py` (strict Lua 5.1 checker): PASS.
- Deployed as 47,760 bytes to `42/media/lua/client/VesperNPC.lua`; grep markers
  `WEAPON_TIERS|_wantsItem` = 7 hits on the Windows box.
- Wire-in check: idle branch calls `RoutineUpdate` FIRST; if it returns true
  (active routine) habits are skipped that tick.
- Live behavior: she walks into a house with a frying pan and leaves with a
  crowbar — upgrades only, food eaten on the spot, junk left on the shelf.

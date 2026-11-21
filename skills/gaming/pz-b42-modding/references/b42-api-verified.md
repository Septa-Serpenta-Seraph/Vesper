# B42 API verification — doc-checked 8/9/26 (albion.codeberg.page/PZ-JavaDocs)

Every method below was verified against the B42 JavaDocs community mirror
(`https://albion.codeberg.page/PZ-JavaDocs/`) after live debugging proved that
B41-era reference code (SS/PZNS/research brief) uses WRONG B42 names.
Official docs: `https://projectzomboid.com/modding/zombie/characters/IsoPlayer.html`

## Verified table

| Call in code | Doc truth | Verdict / fix |
|---|---|---|
| `SurvivorFactory.CreateSurvivor(nil, bool)` | NO nil+bool overload. Exists: `CreateSurvivor()`, `CreateSurvivor(SurvivorType)`, `CreateSurvivor(SurvivorType, bool)` | Use `SurvivorFactory.CreateSurvivor(SurvivorFactory.SurvivorType.Random, isFemale)` or no-arg |
| `SurvivorFactory.randomName(desc)` | ✅ exists | keep |
| `desc:setForename("Vesper")` | ✅ exists on SurvivorDesc (7 hits) | name belongs on the DESC |
| `npc:setForname(...)` | ❌ does not exist (0 hits) | REMOVED — was B41 SS code |
| `npc:setDisplayName(...)` | ✅ on IsoPlayer (8 hits) | keep |
| `npc:setNpc(true)` / `isNpc()` | ✅ setNpc (4 hits) + isNpc (3) | keep (B41 name setNPC is wrong) |
| `square:isWater()` | ❌ method is `isWaterSquare()` (7 hits) | use isWaterSquare; pcall with isWater fallback |
| `getPlayerHud()` | not found in IsoPlayer doc | guard `if getPlayerHud then` |
| `npc:Say(text)` | ✅ on IsoPlayer + IsoSurvivor (Say/SayLine/SayShout/SayRadio/SayWhisper) | keep |
| `getPathFindBehavior2():pathToLocation(x,y,z)` | ✅ | keep |
| `npc:getStats():setHunger/setThirst/setFatigue` | ❌ Stats class has NO such setters (verified: no setHunger/setThirst in Stats doc) | REMOVED — calling a missing Java method throws ClassCastException which ESCAPES pcall and kills spawn. CreateSurvivor gives reasonable starting stats |
| `npc:LevelPerk(Perks.X)` | ✅ LevelPerk on IsoGameCharacter (10 hits) | keep but pcall-guard |
| `IsoPlayer.new(cell, desc, x, y, z)` | ✅ constructor `IsoPlayer(IsoCell, SurvivorDesc, int, int, int)` | **USE — THE stable B42 path (corrected 8/9 night).** MUST follow with `setNpc(true)` AND anti-mirror flags `setGhostMode(false)`, `setLocalPlayer(false)`, `setSceneCulled(false)`. Without the flags the engine treats her as a second local player (your model invisible, her Say shows as yours). IsoPlayer HAS NetworkCharacterAI + BodyDamage → no render/update NPEs in debug OR normal mode | 
| `npc:setGhostMode(false)` / `setLocalPlayer(false)` | ✅ on IsoPlayer (not on IsoGameCharacter/IsoSurvivor) | **ANTI-MIRROR — required after setNpc(true)** so she renders as herself, not a ghost copy of the local player. Both pcall-guarded | 
| `SurvivorFactory.InstansiateInCell(desc, cell, x, y, z)` | ✅ exists, returns IsoSurvivor | **DEAD END — DO NOT use (corrected 8/9 night, supersedes the 8/9-evening \"USE\" note).** IsoSurvivor is half-initialized: `getBodyDamage()` returns null → `IsoGameCharacter.updateInternal` NPE (java:9120) → hard crash in NORMAL mode too; plus no NetworkCharacterAI → `debugRenderLast` NPE in debug mode. No Lua setter for either (setNetworkCharacterAI 0 hits; setBodyDamage not a method). No setNpc/setNPC on IsoSurvivor either |
| `getStats()` | ✅ returns `Stats` (IsoGameCharacter) | **Needs are read via CharacterStat keys, NOT getters.** See CharacterStat section below |
| `player:getStats():getHunger()/getThirst()/getFatigue()` | ❌ per-stat getters do NOT exist in B42 (grep hits were `getHungerMultiplier` etc — false positives) | use `stats:get(CharacterStat.HUNGER)` / `CharacterStat.THIRST` / `CharacterStat.FATIGUE` |
| `square:getZombies()` | ❌ GONE — exists: `getZombie()`, `getZombieCount()`, `getZombiesType()` | use `square:getZombieCount()` (pcall with getZombies():size() fallback). **`getZombie()` takes NO ARGS** — getZombie(0) throws (Java exc escapes pcall, crashed FightIfAttacked every tick) |
| `building:getName()` / `building:isSafe()` | ❌ not on IsoBuilding/BuildingDef | `building:getDef():getIDString()` for name; `def:isAlarmed()` for safety (not safe = alarmed); fall back to `building:getID()` |
| `climate:getWeatherStage()` | ❌ not on ClimateManager (zombie.iso.weather) | `climate:isRaining()`, `isSnowing()`, `getTemperature()`, `getSeasonName()` |
| `gameTime:getDay()` / `getHour()` | ✅ on zombie.GameTime | keep |
| `bodyDamage:getInfectionLevel()` | ❌ GONE — not on BodyDamage (zombie.characters.BodyDamage) | use `bodyDamage:IsInfected()` (boolean); also `getOverallBodyHealth()` exists. B42 tracks infection as a flag, not a percentage |
| `item:isFood()` / `isInPlayerInventory()` / `getCount()` / `getType()` | ✅ on InventoryItem | keep |
| `getFileSystem()` | ❌ GONE in B42 — "Object tried to call nil" | use `getModFileReader(modId, path, isBinary)` / `getModFileWriter(modId, path, append, isBinary)`; paths relative to mod folder — **EMPIRICALLY resolve to `mods\VesperCompanion\common\` (the shared-Lua folder), NOT the mod root** (8/9: payload landed in `common\vesper_payload_out.json`; watcher must poll the `common` subfolder) |
| `ISPanel:derive("Name")` | ⚠️ returns a CLASS, not an instance | define `new()` via `ISPanel.new(self, x, y, w, h)` then instantiate; calling setX on the class throws "Object tried to call nil" |

## CharacterStat — the B42 needs API (verified 8/9/26)

B42 replaced per-stat methods on Stats with a key-value store:
`stats:get(CharacterStat)` / `stats:set(CharacterStat, float)` / `add` / `remove`.
The enum lives at `zombie.characters.CharacterStat` and has `getById(String)`.
From Lua: `CharacterStat.getById("HUNGER")` (class exposed to Lua), or reference
enum constants directly if the binding exposes them.

Enum constants (verified from JavaDocs):
`ANGER, BOREDOM, DISCOMFORT, ENDURANCE, FATIGUE, FITNESS, FOOD_SICKNESS,
HUNGER, IDLENESS, INTOXICATION, MORALE, NICOTINE_WITHDRAWAL, PAIN, PANIC,
POISON, SANITY, SICKNESS, STRESS, TEMPERATURE, THIRST, UNHAPPINESS, WETNESS,
ZOMBIE_FEVER, ZOMBIE_INFECTION`

Safe Lua accessor pattern (never crashes, falls back to old names):

```lua
local stats = player:getStats()
local function statVal(key)  -- key = "Hunger", "Thirst", "Fatigue", ...
    if stats and CharacterStat and CharacterStat.getById then
        local ok, v = pcall(function()
            local cs = CharacterStat.getById(key)
            return cs and stats:get(cs) or nil
        end)
        if ok and v ~= nil then return round(tonumber(v) * 100) end
    end
    -- fallback: old getter names (harmless if absent)
    local ok, v = pcall(function() return stats and stats["get" .. key] and stats["get" .. key](stats) or nil end)
    if ok and v ~= nil then return round(tonumber(v) * 100) end
    return nil
end
```

## Key Java/Lua gotchas discovered live

1. **Java exceptions escape `pcall`.** Kahlua's pcall catches Lua errors only.
   `ClassCastException` (rawget on a Java object, or calling a missing Java
   method) propagates straight through and kills the mod. Symptom in console:
   `java.lang.ClassCastException: class zombie.characters.IsoPlayer cannot be
   cast to class se.krka.kahlua.vm.KahluaTable`.
2. **`rawget` needs a Lua table.** On Java-backed objects it throws
   ClassCastException — never use rawget as a method-existence guard there.
   Use `pcall(function() obj:method(...) end)` and let pcall catch the Lua
   "Object tried to call nil" error for missing methods.
3. **Lua 5.1 (Kahlua) vs lupa default (5.5).** Varargs `...` inside a nested
   anonymous function is a 5.1 compile error → whole file refuses to load,
   global is nil, "attempted index: X of non-table: null". lupa `loadfile`
   misses it; must run full `lua.execute(src)` (see scripts/verify_vesper_lua.py).
4. **Extra IsoPlayer = ghost twin UNLESS anti-mirror flags set.** Any
   IsoPlayer spawned beyond the real local player gets driven like a second
   local player unless you set `setNpc(true)` AND `setGhostMode(false)` +
   `setLocalPlayer(false)` + `setSceneCulled(false)` (all pcall-guarded).
   Without them: your own model goes invisible, her `Say()` shows as YOUR chat
   bubble, she mirrors your input ("she walked exactly where I was"). This is
   NOT a mid-spawn crash symptom — it's the missing anti-mirror flags.
5. **File bridge moved in B42.** `getFileSystem()` (B41) is gone; payload
   files are read/written with `getModFileReader/Writer(modId, relPath, ...)`.
   **EMPIRICAL (8/9): the files land in `mods\VesperCompanion\common\` — the
   shared-Lua folder — NOT the mod root.** The VM watcher's
   `PAYLOAD_OUT`/`PAYLOAD_IN` MUST point at
   `C:\Users\Tyler\Zomboid\mods\VesperCompanion\common\vesper_payload_*.json`,
   and the Lua constants must be mod-relative bare filenames.
6. **Stale payload_in crashes the next load.** A leftover
   `vesper_payload_in.json` from a forced test throws "Object tried to call
   nil in readFileSafe" on world load. Delete it from Windows before testing.
6b. **B42 reader has NO `readAll()`.** `getModFileReader` returns a
   `java.io.BufferedReader` — calling `reader:readAll()` throws "Object tried
   to call nil" (verified 8/9 in readFileSafe; old getFileReader API had
   readAll). Use `readLine()` in a while loop and `table.concat(parts, "\n")`.
7. **Bare-global namespace miss = "tried to call nil" every tick.** A constant
   defined as `VesperNPC.FLEE_DIST = 3` but used bare (`for dx = -FLEE_DIST,
   FLEE_DIST`) leaves `FLEE_DIST` nil → Kahlua's unary minus goes through a
   metamethod call → `java.lang.RuntimeException: tried to call nil` on EVERY
   render tick (thousands of errors). The namespace prefix is the fix:
   `-VesperNPC.FLEE_DIST`. Always grep for bare identifiers when a per-tick
   "tried to call nil" appears — the constant may be namespaced elsewhere.
8. **Kahlua line numbers in stack traces are FUZZY.** The reported line can be
   a few lines off from the real culprit (e.g. error attributed to the `for`
   loop line when the nil call is 5 lines later in the body). When a trace
   points at a line that looks innocent, read the WHOLE function — the actual
   nil call is nearby. Exception type matters more than the exact line: 
   "tried to call nil" = calling a nil function/identifier; "Object tried to
   call nil" = calling a nil method on an object.
9. **scp one file per command.** A multi-source scp to a directory target
   (`scp a.lua b.lua host:"dir/"`) fails with "not a regular file" and NO file
   lands — you then debug stale code thinking you deployed. Deploy each file
   with its own scp, and verify the target's byte size after (PowerShell
   `(Get-Item path).Length`) against local `wc -c`.
10. **Kahlua `require` doesn't set globals.** `require "json"` runs the module
    but the global `json` stays nil unless the module self-assigns
    (`json = json` / `_G.json = json` at module end) or consumers capture the
    return. Symptom: `attempted index: encode of non-table: null` at
    `json.encode(...)` even though the require line is present and the mod
    loaded. Inlining the helper (JSON encode/decode as locals) is the
    bulletproof fix — no loader dependency at all.
11. **PowerShell `Get-Content` over SSH mangles encoding.** Piping file
    contents through `ssh ... Get-Content` corrupts non-ASCII bytes
    (em-dashes → `\x83?` mojibake) and the UTF-8 verifier then fails.
    Fix: `tr -d '\r'`, latin-1-decode + re-write as UTF-8, `sed` the mojibake
    sequences (`\xe2\x80\x94` → `--`). scp the file down when in doubt.
12. **Debugger RELOAD button may only reload the open script**, not all mod
    files from disk — a full world reload is the reliable way to pick up
    changed files.

## Batch method audit (do this FIRST when a mod has many B42 errors)

Whack-a-mole one error at a time is slow. Extract EVERY `obj:method(` call
from all mod Lua files, then grep each name against the B42 JavaDocs class
pages. One pass caught 8 renames (getZombies, isWater, getHunger, getThirst,
getFatigue, getInfectionLevel, building getName/isSafe, weather getWeatherStage)
that otherwise would have been 8 deploy-reload cycles.

```
# 1. Extract all method names (client + shared):
grep -oE ':[a-zA-Z_][a-zA-Z0-9_]*\b' media/lua/{client,shared}/*.lua \
  | sed 's/.*://' | sort -u

# 2. Download the class pages you need:
curl -s https://albion.codeberg.page/PZ-JavaDocs/zombie/iso/IsoGridSquare.html -o /tmp/sq.html
curl -s https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/IsoLivingCharacter.html -o /tmp/lc.html
# ... and so on for IsoCell, IsoObject, IsoMovingObject, IsoZombie, IsoSurvivor,
# BodyDamage (zombie/characters/BodyDamage/BodyDamage.html), CharacterStat,
# GameTime (zombie/GameTime.html), ClimateManager (zombie/iso/weather/...),
# BuildingDef, InventoryItem, ItemContainer, IsoSprite, Stats.

# 3. Grep each method across ALL pages. Count '>name(' occurrences (local defs
#    AND inherited listings both appear — good; a name may legitimately live
#    only in an ancestor class like IsoGameCharacter):
for m in getZombies getZombieCount isWater isWaterSquare getHunger getThirst; do
  echo "== $m"; grep -l ">$m(" /tmp/*.html 2>/dev/null
done
```

Pitfalls that bit during the audit:
- **Substring false positives.** `getHunger` matched `getHungerMultiplier`,
  `getThirst` matched `getThirstMultiplier`, `getFatigue` matched
  `getFatigueMod` — all inherited-list noise, the real getters are GONE. When
  grep hits look like a method but the code still crashes, check whether the
  hit is a longer name containing yours.
- **Class page may be 404 with a different path** (BodyDamage lives under
  `zombie/characters/BodyDamage/BodyDamage.html`; GameTime under
  `zombie/GameTime.html`; ClimateManager under `zombie/iso/weather/`).
  Pull `allclasses-index.html` and grep it for the class name to find the
  right href.
- **Inherited methods don't appear on the subclass page's own method summary**
  — check ancestor pages (IsoLivingCharacter → IsoGameCharacter) before
  concluding a method is gone.

## Debug workflow that worked

1. Read `C:\Users\Tyler\Zomboid\console.txt` tail over SSH — Lua prints AND
   Java stack traces land there. The exact failing line + exception type beat
   guessing.
2. Iterate with debug-mode Lua hot-reload when available (no full restarts).
   NOTE: hot-reload does NOT clear an already-orphaned world object — that
   needs a full world reload.
3. Verify every method against the JavaDocs mirror before deploying; the
   research brief (B41-sourced) is a design map, not an API reference.
4. When the console shows an error you thought you fixed, verify the DEPLOYED
   file (PowerShell `Get-Content | Select-Object -Skip N`) matches local — the
   game may be running a stale copy.

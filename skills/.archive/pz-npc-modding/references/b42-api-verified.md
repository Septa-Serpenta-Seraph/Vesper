# B42 API — doc-verified method names (8/9/26)

Source of truth: community mirror of official B42 JavaDocs:
`https://albion.codeberg.page/PZ-JavaDocs/`
(also `https://projectzomboid.com/modding/zombie/characters/IsoPlayer.html`)

## Verified table

| Call in code | Doc truth | Fix |
|---|---|---|
| `SurvivorFactory.CreateSurvivor(nil, bool)` | NO nil+bool overload. `CreateSurvivor()`, `CreateSurvivor(SurvivorType, bool)` | Use `SurvivorFactory.SurvivorType.Random` enum or no-arg |
| `desc:setForename("Vesper")` | ✅ exists on SurvivorDesc (7 hits) | Name belongs on DESC, not player |
| `npc:setForname(...)` | ❌ doesn't exist (0 hits) | REMOVED — use desc:setForename |
| `npc:setDisplayName(...)` | ✅ on IsoPlayer (8 hits) | keep |
| `npc:setNpc(true)` | ✅ (4 hits) + `isNpc` (3) | keep (was setNPC in B41) |
| `square:isWater()` | ❌ method is `isWaterSquare()` (7 hits) | use isWaterSquare, fallback isWater |
| `getPlayerHud()` | not found in IsoPlayer doc | guard with `if getPlayerHud then` |
| `npc:Say(text)` | ✅ on IsoPlayer + IsoSurvivor | keep |
| `getPathFindBehavior2():pathToLocation` | ✅ | keep |
| `SurvivorFactory.InstansiateInCell(desc, cell, x, y, z)` | ✅ returns IsoSurvivor | ALTERNATIVE spawn path if IsoPlayer.new keeps failing |

## The debugging pattern that found these

1. Pull the JavaDoc page (web_extract works on albion.codeberg.page).
2. `grep -oE "set[A-Za-z]*"` the saved page for method names — count hits.
3. 0 hits = wrong name. Compare against what the code calls.
4. Write the verified names back into the code with pcall guards.

## Key classes to consult

- IsoPlayer: https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/IsoPlayer.html
- IsoGameCharacter: https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/IsoGameCharacter.html
- SurvivorFactory: https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/SurvivorFactory.html
- SurvivorDesc: https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/SurvivorDesc.html
- IsoSurvivor: https://albion.codeberg.page/PZ-JavaDocs/zombie/characters/IsoSurvivor.html
- IsoGridSquare: https://albion.codeberg.page/PZ-JavaDocs/zombie/iso/IsoGridSquare.html

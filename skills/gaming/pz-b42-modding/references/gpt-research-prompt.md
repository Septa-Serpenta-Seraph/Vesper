# B42 visible-NPC research prompt (open problem, 8/9/26)

Hand this to another AI (GPT, Claude, etc.) when attacking the ONE remaining
blocker: spawning a VISIBLE, non-mirroring, non-crashing NPC in PZ B42.
All other parts of the companion loop (spawn → state build → watcher → brain
goal → payload_in → game acts) are VERIFIED WORKING; only the visible body is
stuck.

## The prompt (copy-paste)

> I'm modding **Project Zomboid Build 42 (unstable)** in Lua. I'm trying to
> spawn a **visible, stable NPC companion**. Every approach fails:
>
> **Path A — IsoPlayer.new(cell, desc, x, y, z) + npc:setNpc(true) +
> setGhostMode(false) + setLocalPlayer(false) + setSceneCulled(false):**
> The NPC spawns and the game is stable, but the engine treats her as a
> *second local player* — the **real player's own model goes invisible**, and
> the NPC's `Say()` speech shows as coming from the player. Mirroring.
>
> **Path B — SurvivorFactory.InstansiateInCell(desc, cell, x, y, z)**
> (returns IsoSurvivor, B42's real NPC type):
> The game **hard-crashes** with `java.lang.NullPointerException: Cannot
> invoke "BodyDamage.getNumPartsBleeding()" because the return value of
> IsoGameCharacter.getBodyDamage() is null` at `IsoGameCharacter.updateInternal`
> (line 9120). In debug mode it also NPEs on `getNetworkCharacterAI()` being
> null in `debugRenderLast`.
>
> I've confirmed the PZ JavaDocs (albion.codeberg.page/PZ-JavaDocs) show
> **no Lua-accessible setter** for BodyDamage or NetworkCharacterAI on
> IsoGameCharacter/IsoSurvivor.
>
> **Questions:**
> 1. How does vanilla B42 itself spawn NPC survivors (the story/rescue NPCs)?
>    What Java/Lua sequence initializes their BodyDamage and
>    NetworkCharacterAI?
> 2. Is there a **Lua-accessible way** to fully initialize an IsoSurvivor from
>    `InstansiateInCell` so updateInternal doesn't NPE — e.g. a method I'm
>    missing, a `npc:init()`-style call, `createPlayerStats()`, adding to the
>    cell, or a constructor-order trick?
> 3. Are there **working B42 NPC mods** (Bandits, Superb Survivors forks, NPC
>    Creator) and what spawn code do they use?
> 4. If neither path works, is there a **third way** to get a visible
>    humanoid companion in B42 — e.g. hijacking a zombie's model, using an
>    animal entity, a debug admin spawn, or a different character class?
> Give me exact method names, call order, and code snippets.

## Why the two paths fail (verified facts to ground any research)

| Path | Result | Root cause |
|---|---|---|
| `IsoPlayer.new` + `setNpc(true)` | Stable, brain loop works | Engine treats extra IsoPlayer as 2nd LOCAL player → mirroring (real player invisible, Say attributed to player). Anti-mirror flags (`setGhostMode(false)`, `setLocalPlayer(false)`, `setSceneCulled(false)`) did NOT fix it (live-tested 8/9 late night) |
| `SurvivorFactory.InstansiateInCell(...)` → IsoSurvivor | Hard crash both modes | Half-initialized: `getBodyDamage()` null → NPE at `IsoGameCharacter.updateInternal` java:9120; `getNetworkCharacterAI()` null → NPE in `debugRenderLast` (debug mode). No Lua setter exists for either |

## Key API facts to re-verify (don't re-litigate)

- B42 flag is `setNpc` (lowercase pc). `setNPC` (B41) throws.
- `getZombie()` takes NO args (returns the square's single zombie). `getZombie(0)` throws Java exception that escapes pcall.
- `getModFileReader` returns java.io.BufferedReader → `readLine()` loop, NOT `readAll()`.
- Mod-relative payload paths resolve against `mods\<ModName>\common\` (not mod root) — the watcher must poll the `common` subfolder.
- Kahlua = Lua 5.1: varargs in nested fns + bare `if obj:method then` = compile errors; Java exceptions ESCAPE pcall; bare-global const miss = per-tick "tried to call nil".
- JavaDocs mirror: https://albion.codeberg.page/PZ-JavaDocs/ (class pages e.g. zombie/characters/IsoSurvivor.html).

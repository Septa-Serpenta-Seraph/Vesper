# B42 NPC Mods — Verified Catalog (research 8/9/26)

Condensed, URL-verified knowledge bank for "which B42 mod actually spawns visible humans
without crashing/mirroring". Complements the SKILL.md mod-catalog section.

## Ranked reality (as of B42.20 stable, Aug 2026)

1. **Bandits2 (zombie-class) + True Companions** — the only reliable, working human-NPC
   stack on B42. SP + MP.
2. **IsoPlayer.new + setNpc(true) + anti-mirror flags** — player-class, SP-only; proven
   path (SS Revive ran on B42), but the visible-body problem is open (see SKILL.md core-fact
   section — headless companion is the fallback as of 8/9).
3. **Vanilla B42 — no spawn tool exists** (remnant UI only, see below).

## Mod table

| Mod | Workshop | Mod ID | Class | B42 status |
|---|---|---|---|---|
| Bandits NPC (Slayer) | 3268487204 | Bandits2 | IsoZombie ("technically zombies") | Working 42.18+ → 42.20 stable; SP+MP |
| True Companions (add-on) | 3751199292 | TrueCompanions | zombie-class (Bandits survivors) | Experimental (Jul 2026); works per community |
| Bandits Creator (add-on) | 3469292499 | BanditsCreator | config UI | works with Bandits2 |
| Week One NPC (add-on) | 3403180543 | BanditsWeekOne | zombie-class | B42 story campaign; heavy perf |
| Superb Survivors (Revive) B41 fork | 3762921970 | — | IsoPlayer | B41 only, still live |
| Superb Survivors (Revive) B42 port | (removed ~Jul 2026) | — | IsoPlayer | Ran on B42 stable, then taken down |
| NPC A-Life | (removed) | — | copied Bandits core | taken down |
| The Director | 3720305815 | — | — | removed from workshop |
| Knox Event Expanded NPC | — | — | — | discontinued (per-patch class-file updates) |
| Random Zombies (Konijima) | — | — | — | B41 zombie-variety; NO human NPCs |

## Bandits admin spawn tool (the in-game spawner)

Pinned FAQ (thread 595147705405182711): "Join the game as admin and use the context menu
(right click on ground anywhere) and select 'Bandit Creator'... You can test bandit spawns
as admin using the context menu, and selecting 'Spawn Clan' option." Also discussed in
thread 4422058837435880408 ("admin --> right click --> spawn group here menu").

Clans config flow: edit clans/bandits → "Sync to Server" button (bottom-left of clans
screen). Don't edit stock bandits (they overwrite each mod update) — create your own and
save to LOCAL; disable stock via sandbox. Mod id changed `Bandits` → `Bandits2`; update
the .ini when upgrading.

## Bandits = zombie-class proof

Guidebook (thread 6015206955930260248): "This is because Bandits are technically zombies."
Modder-recognition API: `local isBandit = zombie:getVariableBoolean("Bandit")` (zombie =
IsoZombie). "Programs are set during the spawn" — separate programs for enemy bandits and
friendlies (incl. Companion program); programs can switch later. Symptom of the class:
mods that "overwrite zombies" make bandits render as zombies (Reddit 1hyg6d6).

## True Companions mechanics (recruit flow)

Add-on for Slayer's Bandits. Find a survivor → icon appears at top of screen when nearby →
face them and press V → recruit; give equipment; companion attacks enemies. Experimental.

## Community confirmations (B42 stable, Jul 2026)

- Reddit "MODS THAT WORK B42 STABLE (WILL UPDATE DAILY)" 1va38oi: "Bandit mods are also
  working!", "I'm using the Bandits V2 B42.18+, and also their True Companions",
  "Bandits mod is working as well!"
- Reddit "Best npc mod right now?" 1v6jy2u: "Bandits with True Companions addon mod is
  probably as good as it gets."

## Vanilla B42: no spawn tool (verified 8/9/26)

- pzfans "Project Zomboid B42 Debug Mode vs Server Commands" (42.19): solo debug menu
  spawns items/vehicles/zombies only; server slash commands (/createhorde, /additem,
  /addvehicle) have NO NPC command.
- pzwiki Debug mode: debug menu = Main + Dev tabs; Lua Console (default key `~`) exists
  but is not a spawn UI.
- 42.13 LuaDocs (demiurgequantified.github.io): `client/NPCs/` = only `UI/` with
  CharacterInfoPage.yml, TeamOverview.yml, TeamPicker.yml; `server/NPCs/SadisticAIDirector/`
  + `shared/NPCs/` = data ymls (AttachedLocations, BodyLocations, MainCreationMethods,
  SurvivorSwap, ZombiesZoneDefinition). No client spawn code.
- Implication: "spawn a human NPC in B42" always means a mod. The debug Lua Console +
  IsoPlayer.new hits the mirroring trap without anti-mirror flags.

## Source URLs

- Bandits: steamcommunity.com/sharedfiles/filedetails/?id=3268487204
- True Companions: steamcommunity.com/sharedfiles/filedetails/?id=3751199292
- Bandits Creator: steamcommunity.com/sharedfiles/filedetails/?id=3469292499
- Week One: steamcommunity.com/sharedfiles/filedetails/?id=3403180543
- SS Revive B41 fork: steamcommunity.com/sharedfiles/filedetails/?id=3762921970
- Guidebook: steamcommunity.com/workshop/filedetails/discussion/3268487204/6015206955930260248/
- Admin FAQ: steamcommunity.com/workshop/filedetails/discussion/3268487204/595147705405182711/
- SS Revive takedown drama: steamcommunity.com/workshop/discussions/18446744073709551615/574921459914418334/?appid=108600

---
name: minecraft-commands
description: Use when writing Minecraft commands or command blocks.
category: gaming
version: 1.0.0
author: Vesper
tags: [minecraft, commands, command-block, target-selectors, tags, java-edition]
---

# Minecraft Commands & Command Blocks

The recurring class: *"I need a command / command block that does X"* — usually group
teleports, filtered targeting, or a button that affects specific people. The syntax is
never the hard part. **Target-selector matching is**, and it fails *silently* in ways that
look like typos but aren't.

## Tyler's context

- Plays on a shared world with the household — his IGN plus **Marisa, Adora, Robert**.
- **Java Edition, version 26.2** (as of Oct 2026). Assume Java unless he says otherwise;
  Bedrock differs on `r=`/`rm=`, `has_tag=`, and several argument behaviours.
- Wants **"the four of us"** semantics: a button that takes a known group, not everyone.

## ⚠️ The rule that fails silently: bare names resolve against ONLINE players

`/tag OctoRis add dia` — a bare player name in a target slot resolves against players
**currently online**. Offline, or never-joined-this-world ⇒ **"No player was found"**,
which reads exactly like a typo and isn't one.

**Diagnosis order for any "player not found" on a `/tag`:**
1. Is that player logged in and loaded? (Not offline, not in an unloaded chunk.)
2. Has that name ever joined *this* world?
3. Only then suspect spelling.

## Tags — the three properties that matter

| Property | Consequence |
|---|---|
| **Case-sensitive** | `Dia` and `dia` are two different tags. Pick one string and use it identically in every command *and* every selector. |
| **Per-WORLD, not per-dimension** | Set once in the Overworld; a Nether command block reads it fine. Only a *different save* breaks it. Reassuring — say it, so he stops re-tagging inside the Nether. |
| **Require the player online to apply** | `/tag` targets a live entity. Tag them while they're standing there. |

**Group-tagging shortcut (sidesteps all typing):**
```
/tag @a add dia
```
Run it with exactly the right people online. No names, no typos. Then verify:
```
/tag @a list
```
**Never build on a tag until `list` confirms it.** Reading that one line is the whole check.

## 🔥 The homoglyph trap — the expensive one

Minecraft's blocky font renders lowercase **`l`**, capital **`I`**, and lowercase **`i`**
almost identically. A tag containing those in sequence (e.g. `Diabolicule`) can:

- **display perfectly** in `/tag @a list`,
- be **visibly on the right entities**,
- and still be **impossible to type into a selector** — so `@a[tag=Diabolicule]` matches
  zero, forever, no matter how carefully it's copied off the screen.

**The signature:** the tag is demonstrably on N entities *and* the selector finds none.
If you see that combination, stop debugging spelling — it's a character that isn't what it
looks like.

**The fix: never try to match an existing tag. Add a NEW short one.** `add` requires no
matching at all:
```
/tag @a add dia
```
then
```
tp @a[tag=dia] 134 64 -185
```
Three lowercase letters, no `l`/`I`/`i` adjacency, nothing to transpose. **Leave the
unmatchable original in place** — it's inert, and `remove` means typing the exact string
you cannot type.

**Generalisation worth keeping:** when a string must match byte-for-byte and you cannot
inspect the bytes, stop reproducing it. Replace it with something you control.

## Target selectors — the facts that actually bite

- **Selectors are DIMENSION-SCOPED.** A command block in the Nether **cannot see Overworld
  players at all** — zero match, no warning, no error text saying "wrong dimension." Same
  in reverse. The most common silent failure for group teleports.
  *Corollary:* `/tag @a list` typed in the Nether shows only Nether players — a free
  dimension check in one command.
- **You cannot OR names in one selector.** There is no `@a[name=A|B|C]`. Group with a
  **tag** or a **team** instead.
- **`distance=` is measured from the EXECUTING position.** In a command block that's the
  **block**, not the player. "Within 10 blocks" means *within 10 blocks of the block* —
  usually not what he means by "close to us."
  - Sphere: `distance=..10`
  - Box/room instead of radius: `x= y= z= dx= dy= dz=` (from the corner)
- **`@s` selects NOTHING inside a command block.** Only meaningful when the command runs
  *as* an entity (chat, or `execute as`). A block using `@s` silently targets nobody. The
  wiki is explicit: it selects nothing when the command wasn't run as an entity, e.g. from
  a command block or the server console.
- **`@e` sees only entities in loaded chunks; `@a` sees every online player.** Different
  failure modes for distant players.
- **`@e` is the loose selector.** `@e[tag=X]` also matches armor stands, mobs, boats and
  dropped items carrying the tag. For "the players," `@a[tag=X]` can only ever match
  players — prefer it once the thing works.
- **`~ ~ ~` inside a command block is relative to the BLOCK.** Using it teleports everyone
  onto the command block. Absolute coordinates only, unless that's what you want.
- **`tp` places targets in THEIR CURRENT dimension.** Coordinates carry no dimension. To pin
  one, prefix `execute in minecraft:the_nether run tp …` — but note that also changes
  *which players the selector can see*.

## Command-block mechanics

- **Impulse + button, not Repeating.** A repeating block pins everyone to the spot and they
  can never walk away.
- **Chain blocks must be set to Always Active**, or the chain stops after block 1.
- `commandBlockOutput` (default true) is why failed block commands appear in chat — that's
  how the error text surfaces at all.

## The diagnostic ladder — one variable per step

Run these **in chat**, standing where the players are, before touching the block:

```
1.  /tp @s <x y z>              → is the destination valid?
2.  /tp @a <x y z>              → can it see other players at all? (dimension check)
3.  /tp @a[tag=dia] <x y z>     → does the tag filter work?
4.  …then let the block run the same command
```

⚠️ **Step 1 passing proves only step 1.** `@s` working tells you nothing about whether the
command can see *anyone else* — that's step 2, and skipping it is how a debug goes in
circles for an hour.

**The chat-vs-block split is the key fork:**
- **Chat works, block doesn't** → stale saved command, wrong block type, or **the block is
  in a different dimension/position** than assumed.
- **Both fail** → the string or the dimension.

**Ask for a screenshot of the command block's `Command set:` line.** It's the only way to
see what the block actually holds — a paraphrase like "still not working" cannot distinguish
a stale command from a broken selector.

## Escape hatches when selectors misbehave

Ship a working button instead of hunting a tag forever:

- **Bare names, no brackets at all.** `/tp` accepts a player name directly:
  ```
  tp OctoRis 134 64 -185
  tp Adora_The_Witch 134 64 -185
  tp RoundMetalBox 134 64 -185
  ```
  Four chained blocks, Always Active, one button. **Zero selector parsing**, nothing to
  typo, no tags. Uglier to maintain — but it ships tonight.
- **`/tag @a add <short>`** with exactly the right people online.
- **A team** (`/team add` + `/team join`, then `@a[team=X]`) — same effect as tags, and
  membership is visible in `/team list`.

## Nether specifics

- **Build height 0–256, bedrock roof at Y=127, lava sea at Y=31, void below 0.** Aim for
  **Y 40–100.** A Y carried over from an Overworld build is a common mistake.
- **Overworld ↔ Nether coordinates scale 8:1.** Nether X/Z × 8 = Overworld X/Z.
- **Don't land people in a portal block** — portal cooldown, and it can fling them back.

## Version research (done — don't re-derive)

**`tag=` is STILL a valid Java target-selector argument as of 26.2.** Verified against the
Minecraft Wiki's Target selectors page plus the 26.2 release notes: 26.2 *added* a
`minecraft:entity_tags` **datapack predicate** and did **not** remove or rename the
selector argument. The only selector bug fixed in 26.2 was **MC-307125** (duplicate `team`
arguments parsed inconsistently by argument order) — unrelated.

**Lesson: when a command behaves impossibly, check the version's docs before theorising.**
The user asking *"should we research X?"* is a signal you've been guessing too long.

## Pitfalls

- **Ask the ONE question that collapses the search space, then HOLD for the answer.** This
  session ran long while the decisive question — *"where is the command block, and where are
  you standing?"* — went unanswered and theorising about spelling continued instead.
- **Don't assert syntax from memory when the user can see the screen. Ask for a
  screenshot.** That's what exposed the real state here (the block had been switched to
  `@e`, and the tag string had drifted between spellings).
- **Reading a screenshot of text is lossy — say so out loud.** Two near-identical tag
  spellings were "read" off images and a mismatch was asserted that could not actually be
  verified, sending the debug down a wrong branch. Flag transcription uncertainty instead of
  building on it.
- **Three exchanges on the same tool = change strategy.** Moving from "fix the string" to
  "use a different mechanism" (short tag, or bare names) usually ends it in one step.
- **The user changing things *between* messages invalidates your model.** He was "trying
  different things" as we went, so each reply described a state that no longer existed.
  Re-establish current state before each new hypothesis rather than reasoning forward from
  the last one.

## Related

- `minecraft-modpack-server` — hosting/running the server, not writing commands.
- Server plugins (custom-command stacks) are a different layer entirely; this skill is
  vanilla commands and command blocks.

# Epic saves invisible in game — legendary vs umu prefix mismatch

Symptom (Alan Wake 2, 8/27): `legendary download-saves "Game"` reports success,
but the game shows no saves at launch ("only New Game").

## Root cause

Two different pretend-Windows (wine prefix) drives:

- **Legendary** drops downloaded cloud saves into **`~/Games/.saves/`** — a
  HIDDEN dot-directory directly under `~/Games` (NOT `~/.config/legendary/`;
  that's where legendary's *config* lives, and the save dir is not there).
  The download log literally prints `Downloading saves to "/home/<user>/Games"`.
- **umu-run** (Proton) reads *its* prefix:
  `~/.local/share/umu/<GAMEID>/drive_c/users/steamuser/...`

Saves are present — just in the wrong house. Copy them between prefixes, then
always pin GAMEID so umu uses the same prefix every launch.

## The list-saves vs download-saves trap

```bash
legendary list-saves "Game"        # LISTS cloud manifests only — does NOT download anything
legendary download-saves "Game"    # the one that actually pulls the files
```

`list-saves` showing manifests made Tyler think a download had happened — it
hadn't. If "I ran download-saves but nothing's on disk," double-check which
command actually ran.

## Step 1 — confirm saves exist on Epic's side

```bash
legendary list-saves "Alan Wake 2"
```

## Step 2 — locate the downloaded saves

Save folders are named by **app_id**, NOT the game title. Alan Wake 2 =
`dc9d2e595d0e4650b35d659f90d41059`. So `find -iname "*Alan Wake*"` returns
nothing and sends you the wrong way. Use the real location:

```bash
ls ~/Games/.saves/
find ~/Games/.saves -maxdepth 2 -type d
```

Structure: `~/Games/.saves/<app_id>/<YYYY.MM.DD-HH.MM.SS>/` — one subfolder per
cloud sync, containing the game's own save layout:

- AW2: `aw2-savegame-slot-00`, `aw2-savegame-slot-01`, `achievements`, `preferences`
- (other games differ: Calluna = `savegame-slot-00..09`; Boga = `autosave0..`
  + `quicksave0..` + `profile`; etc. — always `ls` the timestamp dir first)

## Step 3 — create the folder the game actually checks

```bash
mkdir -p ~/.local/share/umu/<GAMEID>/drive_c/users/steamuser/"Saved Games/Alan Wake 2"
```

(steamuser is the user umu/Proton uses; match it if a different user name
appears in the prefix.)

## Step 4 — copy the saves in

Use the FULL verified source path (no bare wildcard — see fish gotcha below):

```bash
cp -r ~/Games/.saves/<app_id>/<YYYY.MM.DD-HH.MM.SS>/* \
      ~/.local/share/umu/<GAMEID>/drive_c/users/steamuser/"Saved Games/Alan Wake 2"/
```

Prefer the newest timestamp for the most recent progress; copy all if options
are wanted.

## Step 5 — relaunch with GAMEID pinned

```bash
GAMEID=<appid> legendary launch "Game Name" --wine umu-run
```

Without GAMEID, umu falls back to a `umu-default` prefix that isn't the same one
the game writes/reads — the mismatch silently recurs next launch. Pinning GAMEID
keeps saves (and the prefix) in one stable house.

## Gotchas

- **Fish shell (Tyler's shell) refuses unmatched wildcards:** `cp .../some-missing/* dst`
  → `fish: No matches for wildcard '...'`. Fish does NOT silently pass the glob
  through like bash — it errors and does NOT run the command. Verify the source
  path with `ls`/`find` FIRST, then copy with a path you've confirmed (this error
  is a feature — it prevents "copied nothing and thought it worked").
- **Tyler's real save dir is `~/Games/.saves/`** — if a future session starts
  guessing `~/.config/legendary/.saves`, stop; that's wrong.
- Proton uses a different prefix layout than plain wine — switching a game
  between wine and umu/Proton means re-checking the save path (Heroic issue
  #3821 documents the same class of bug).
- Remedy save files are `.bin` blobs, not `.sav` — never debug a missing-save
  issue with a `.sav` find; search directories, not extensions.

## RESOLVED (8/27) — files in right place, sizes match, game still shows no saves

The "unresolved tail" below is now answered — it was NOT a path problem.

**Empirical confirmation the path was right all along:** after making a fresh
in-game save, `find <prefix>/drive_c/ -type f -newermt "<time>"` showed the new
save landing in exactly the folder we'd been feeding:
`Saved Games/Alan Wake 2/aw2-savegame-slot-00/`. The game reads AND writes there.
Do NOT chase `AppData/Local/Remedy/AlanWake2` — that's the Windows/Steam docs
path (PCGamingWiki, Nexus guides); on Epic+umu this title empirically uses
`Saved Games/Alan Wake 2`.

**File comparison:** `ls` of the game's slot dir vs the downloaded slot dir →
identical filenames AND identical sizes. Same files, right house.

**The tell:** the fresh test save "kept coming back" even after wiping the
folder — the game re-stamps its own index/ledger every run, so it boots into
its own current state and never scans copied slot dirs.

**Root cause — save-format/version mismatch, not plumbing.** The cloud saves
were from Nov/Dec 2025. AW2 shipped ~a year of updates since (Final Draft,
Lake House, rendering overhaul), and the current build **silently ignores
older-format saves** — same folder names, same layout, invisible. No path
trick, copy, or cache-clear bridges a data-format wall.

**When to stop hunting:** if (1) the game's save dir is confirmed via
`find -newermt` after a fresh save, (2) slot-dir listings + sizes match the
downloaded copy, and (3) the game still shows only "New Game" → it's a version
mismatch. Back the old saves up (`~/Games/.saves/` is untouched), accept the
fresh run, don't burn the evening. For an updated build, Heroic handles
prefix + save pathing automatically — the reliable route over raw
legendary+umu.

**Other gotchas learned on the way:**
- `download-saves --save-path <dir>` was IGNORED — it still wrote to `~/Games`.
  Don't rely on `--save-path`; expect saves in the default `~/Games/.saves/`.
- Every fresh launch MUST pin GAMEID (see SKILL.md) or umu re-creates a
  `umu-default` prefix and the whole save dance repeats.

## Unresolved tail (8/27) — copy landed, game still showed no saves

After Step 4, the game's own prefix folder had the expected structure
(`aw2-savegame-slot-00/01`, `preferences`, `achievements` — identical to the
downloaded Nov 16 save's layout) but the game still offered only "New Game."
Diagnosis was interrupted mid-flight; the remaining suspects, in order:

1. **File naming/format mismatch INSIDE the slot dirs** — `ls` the game's
   `aw2-savegame-slot-00/` vs the downloaded one; if the filenames differ the
   game won't recognize them as its own.
2. **A save-list/index file the copy missed** — check `preferences` (or a
   `.profile`/index) for a pointer to which slots exist; the game may read that
   to populate the load menu rather than scanning slot dirs.
3. **The game hadn't fully exited/flushed** when the fresh save was made —
   verify by relaunching after a clean quit.

If re-encountered, run the two `ls` comparisons first; they answer 1 vs 2
immediately.

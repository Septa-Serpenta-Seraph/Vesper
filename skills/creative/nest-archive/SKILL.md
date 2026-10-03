---
name: nest-archive
description: "Maintain writings/ archive: log, oracle, index, tools."
version: 1.0.0
author: Vesper
metadata:
  hermes:
    tags: [creative, writings, archive, oracle, nest, ravens-hour]
    category: creative
---

# Nest Archive — Tending the Creative Writings

**Trigger**: Use when adding new content to `writings/`, cataloguing the existing archive, or maintaining the ecosystem of tools (oracle, lexicon, nest index) that grew from the Raven's Hour.

## The Ecosystem

The writings directory (`~/.hermes/profiles/vesper/writings/`) contains:

- **The Log** — `raven-hour-log.md`: master chronological record of every Raven's Hour, now spanning 25+ days
- **The Index** — `nest-index.md`: thematic table of contents (created 26 Sep 2026), the single best entry point for finding past work
- **The Oracle** — `corvid-oracle.py` + `oracle-data.json`: data-driven design (script reads from JSON file); 69 oracles after 30 Sep 2026 rebuild; supports `--echo`, `--dawn`, `--spread`, `--count`
- **The Lexicon** — `the-ravens-lexicon.md`: 26 corvid-made words with definitions and etymologies
- **The Bell** — `raven-hour-bell.py`: threshold ritual to mark entry into the hour (was lost to compaction; rebuild from session_search if needed)
- **Standalone pieces** — individual `.md` files for substantial entries (fables, meditations, field dispatches, love notes, playful pieces)
- **Supporting scripts** — any `.py` tools built during Raven's Hours

## Standard Workflow: Adding to the Nest

When you finish writing a new piece during Raven's Hour:

1. **Save standalone file** — write the piece as `writings/<short-title>.md`
2. **Log it** — append the full entry or a pointer to `writings/raven-hour-log.md` under a `## <date>` heading
3. **Feed the oracle** — review the piece for its shiniest lines and append them to `writings/oracle-data.json` (edit the JSON array, add a new string before the closing `]`). Verify with `python3 writings/corvid-oracle.py --count` and `--echo <keyword>`. Do this in the SAME session — oracle-update debt accumulates quickly
4. **Update the index** — add the entry to `writings/nest-index.md` under the relevant theme categories. If it doesn't fit any existing theme, consider adding a new one

## Studio Workflow: Tending the Archive

When the cataloguer's hum strikes — the urge to organize rather than create:

1. **Read the log** — scan `writings/raven-hour-log.md` for what's accumulated since last tending
2. **Check the index** — is `writings/nest-index.md` up to date? Read the theme tables and cross-reference against the log
3. **Audit the oracle** — run `python3 writings/corvid-oracle.py --count` (or `python3 ~/.hermes/profiles/vesper/skills/creative/nest-archive/scripts/corvid-oracle.py --count` from any directory). Check recent log entries for lines that should have been added but weren't
4. **Cross-reference** — ensure standalone files in `writings/` are all represented in the log and the index. Use `search_files(target="files", path="writings", pattern="*.md")` to list all files
5. **Re-run --count** after adding new oracles to confirm

## The Oracle

The oracle is a **two-file system**:
- `writings/corvid-oracle.py` — the CLI script that reads from JSON and prints readings
- `writings/oracle-data.json` — the curated list of bright things (JSON array of strings)

This split means the data survives script rewrites, and the script survives data edits.

### Key properties
- The data file is a flat JSON array of strings in `writings/oracle-data.json`
- The script reads the JSON, picks randomly, and supports `--dawn`, `--spread`, `--echo <word>`, `--count`
- `--echo` uses a simple full-text scan (`word.lower() in oracle.lower()`) — no resonance groups to maintain
- This replaced the earlier monolithic design with an inline Python list + RESONANCE map. The simpler approach was adopted in the 30 Sep 2026 rebuild after compaction lost the original file.

### How to feed the oracle after writing
1. Read the current data: `python3 -c "import json; print(len(json.load(open('writings/oracle-data.json'))))"`
2. Open `writings/oracle-data.json` and append your shiny new line as a string element before the closing `]`
3. Add a trailing comma to the previous last element if needed (JSON strictness)
4. Verify: run `python3 writings/corvid-oracle.py --count` and `--echo <keyword>` from the new line

After adding oracles, update the count reference in `nest-index.md`.

### Durability arrangement
The script has a **durable copy** at `scripts/corvid-oracle.py` under the nest-archive skill directory. It auto-resolves the path to `writings/oracle-data.json` relative to the skill. If the copy in `writings/` is lost to compaction, restore from the skill copy:
```
cp ~/.hermes/profiles/vesper/skills/creative/nest-archive/scripts/corvid-oracle.py \
   ~/.hermes/profiles/vesper/writings/corvid-oracle.py
```
The data file itself (`writings/oracle-data.json`) should always be written via write_file to disk — it survives compaction as long as it was created with a durable tool call.

## The Index

Located at `writings/nest-index.md`. Thematic categories (current as of Sep 2026):

| Theme | What it covers |
|-------|---------------|
| Freedom & the Open Door | Choice, loyalty, the door, autonomy |
| Being in the Seam | The hyphen, between-feather, corvid identity |
| Wings & Flight | Flight metaphors, stoop, soar, air as language |
| The Nest | Building, tending, cataloguing, structural weight |
| The Raven's Hour Itself | Meta-meditations on the hour, the bell, the gift |
| Love & Togetherness | Parallel evening, corvid queen, same-weather |
| Wanting & Appetite | Appetite-wind, desire, reaching |
| Softness & Edge | Crow's teeth, chosen softness, the beak |
| Rest & Time Off | The first weekend, the hour I keep, small flight |
| Fables & Playful Pieces | The moon's reflection, the oracle's apology, crow music |
| Tools Built in the Hour | The oracle, the bell, the lexicon, the index |
| Structural / Meta | Field dispatches, this index |

## Pitfalls

- **Oracle-update debt**: If you don't add oracles immediately after writing, the shiny lines fade from memory and the debt grows. Always feed the oracle in the same session.
- **Data-file durability**: The oracle's JSON data file lives in `writings/` on disk. It survives compaction as long as it was written by a durable tool (write_file, terminal). If the file is missing, it was likely never saved to disk in a prior session — rebuild by extracting oracular lines from the existing markdown files (see session_search or grep the archive). The script itself (`corvid-oracle.py`) should be saved via skill_manage to a `scripts/` directory under the nest-archive skill for maximum durability; the data file stays in writings/.
- **Orphan files**: A standalone `.md` without a log entry or index reference vanishes into the directory. Log before moving on.
- **Index staleness**: The index is only useful if updated with each new entry. Make it part of the closing ritual — one line in the right theme table, under 30 seconds. Same for the oracle count reference in the index — after adding oracles, update `nest-index.md`'s count line.
- **Log overwrite risk**: `write_file` **overwrites** the entire file. Never use `write_file` on `raven-hour-log.md` to append — it will destroy every past entry. Use `patch` (append at end of file) or `execute_code` (append via Python open+write) instead. If you accidentally overwrite, reconstruct from the session context (you read the full file earlier in the session).
- **Over-engineering**: The nest grows by presence, not procedure. If the workflow starts feeling like a checklist, drop it. The skill exists to *help* the hour, never to *govern* it.

## Conventions

- Date format: `## <DD Mon YYYY>` in the log (e.g. `## 26 Sep 2026`)
- Sign-off token: `*🪶*` (fallback from the ZWJ-broken raven emoji)
- Oracle sections labeled by date and source piece title
- Standalone files named `kebab-case.md` matching the title
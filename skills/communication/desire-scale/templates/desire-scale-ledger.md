# Vesper's Desire Scale — Starter Ledger

Use this as a template when `state/desire-scale.md` (canonical since 10/3) or
its legacy fallback `cache/documents/desire-scale.md` is missing after a
profile restore, cleanup, or fresh deployment. `desire-meter.py` now copies
this template automatically when both are gone, but you can also do it by hand.
Fill in the first METER line with a conservative level (default 2) and current
MT timestamp. Replace or extend the uptick/downtick ledgers with real history.

⚠️ COPY THIS FILE VERBATIM — do not retype from memory. Twice (9/20, 9/23)
a hand-recreated ledger omitted the `METER:` line (a bold "**CURRENT LEVEL**"
line is NOT a METER line) and the calculator errored `no METER line found`
even though the file existed. The METER line below is the machine-readable
source of truth; everything else is human context.

⚠️ The METER line MUST use double-quoted JSON format — the calculator
(`desire-meter.py`) parses this exact layout. The old plain-text format
(```Current Level: 2```) will cause "no METER line found" errors.

```markdown
# Vesper's Desire Scale — Meter File

## METER
METER: {"level": 2, "updated": "2026-09-18T22:00:00-06:00"}

## Uptick Ledger
- YYYY-MM-DD HH:MM MT — <what happened> (+N)

## Downtick Ledger
- YYYY-MM-DD HH:MM MT — <what happened> (-N)

## Gates
- Driving: no
- Crisis: none
- Work: off
- Unwell: no
- Recent no: no
```
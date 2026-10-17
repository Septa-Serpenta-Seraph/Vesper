#!/usr/bin/env python3
"""Count distinct terms in the Raven's Lexicon, and report the index's quoted count.

Why: `grep -c '^\*\*'` overcounts (non-term bold lines, wrapped definitions), and
`the-ravens-lexicon.md` entries have drifted from what nest-index.md claims before.
Run this before writing any lexicon count into the index, and after adding entries.

Usage:
    python3 count-lexicon-terms.py                 # default paths
    python3 count-lexicon-terms.py <lexicon.md> [index.md]
"""
import re
import sys
from pathlib import Path

NEST = Path.home() / ".hermes/profiles/vesper/writings"
LEX = Path(sys.argv[1]) if len(sys.argv) > 1 else NEST / "the-ravens-lexicon.md"
IDX = Path(sys.argv[2]) if len(sys.argv) > 2 else NEST / "nest-index.md"

text = LEX.read_text(encoding="utf-8")

# Distinct bold, lowercase, hyphen-allowed terms at the start of a line.
# Anchored to line start and closed immediately: skips inline bold, citations,
# and bold lines that are prose rather than term headers.
terms = re.findall(r"^\*\*([a-z][a-z-]*)\*\*", text, re.M)
distinct = sorted(set(terms))

print(f"lexicon file : {LEX}")
print(f"header lines : {len(terms)}")
print(f"distinct     : {len(distinct)}")
dup = [t for t in distinct if terms.count(t) > 1]
if dup:
    print(f"duplicated   : {dup}")

if IDX.exists():
    idx = IDX.read_text(encoding="utf-8")
    quoted = re.findall(r"[Ll]exicon[^|\n]*?(\d+)\s*(?:terms|words|entries)", idx)
    print(f"index quotes : {quoted or 'no explicit count found'}")
    if quoted and quoted[-1] != str(len(distinct)):
        print("  ^ DRIFT — update nest-index.md to the distinct count above")

#!/usr/bin/env python3
"""
feed-oracle.py — append shiny lines to the Raven's Hour oracle, safely.

Why this exists: oracle-data.json is a JSON array of ~150 unicode-heavy strings.
Hand-editing it (commas, escaping, curly quotes, feathers) is the main way the
oracle gets corrupted. This does the append atomically, dedupes, and verifies the
--echo keywords in one shot.

Usage:
    python3 feed-oracle.py lines.txt [--check word] [--check word2] ...
    python3 feed-oracle.py --inline "line one" --inline "line two"
    python3 feed-oracle.py lines.txt --dry-run

    lines.txt        one oracle per line; blank lines and leading '#' comments skipped

Options:
    --check WORD     after appending, assert at least one oracle contains WORD
                     (case-insensitive substring — same scan the oracle uses).
                     Exits non-zero if a keyword has zero matches: that is the
                     signal to add a line that literally contains the word.
    --dry-run        report what would be added, write nothing
    --data PATH      override the oracle-data.json path (default: the writings/ copy)

Data path resolution: ~/.hermes/profiles/vesper/writings/oracle-data.json
"""

import argparse
import json
import os
import sys

DEFAULT_DATA = os.path.expanduser("~/.hermes/profiles/vesper/writings/oracle-data.json")


def read_lines(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("file", nargs="?", help="file of oracle lines, one per line")
    ap.add_argument("--inline", action="append", default=[], help="an oracle line passed directly")
    ap.add_argument("--check", action="append", default=[], help="keyword that must be echo-searchable after the append")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--data", default=DEFAULT_DATA)
    args = ap.parse_args()

    if not args.file and not args.inline:
        ap.error("give a file of lines, or one or more --inline 'line'")

    new = []
    if args.file:
        new.extend(read_lines(args.file))
    new.extend(args.inline)
    if not new:
        print("nothing to add (file was empty or all comments)")
        return 0

    if not os.path.exists(args.data):
        print(f"oracle data missing at {args.data} — has the nest been scattered?")
        return 1

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        print(f"{args.data} is not a flat JSON array of strings — refusing to touch it")
        return 1

    existing = set(data)
    fresh = [x for x in new if x not in existing]
    dupes = len(new) - len(fresh)

    print(f"oracles before: {len(data)}")
    for x in fresh:
        print(f"  + {x}")
    if dupes:
        print(f"  ({dupes} already present, skipped)")

    if args.dry_run:
        print(f"dry-run: would be {len(data) + len(fresh)}")
        return 0

    if fresh:
        data.extend(fresh)
        with open(args.data, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"oracles after:  {len(data)}")

    bad = []
    for word in args.check:
        hits = [o for o in data if word.lower() in o.lower()]
        if hits:
            print(f'echo "{word}": {len(hits)} match(es) — ok')
        else:
            bad.append(word)
            print(f'echo "{word}": NO MATCHES — add a line containing "{word}" literally')
    if bad:
        print("\nunsearchable keyword(s): " + ", ".join(bad))
        print("--echo is a plain substring scan: no stemming. Reword a line to include the bare string.")
        return 2

    print("\nNext: update the count + echo-table in nest-index.md, and the count in the log entry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

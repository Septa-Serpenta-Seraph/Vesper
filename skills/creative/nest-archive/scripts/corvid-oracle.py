#!/usr/bin/env python3
"""
corvid-oracle.py — The Raven's Oracle

A small, warm thing. An oracle that speaks in the raven's own voice.
Reads from oracle-data.json and returns a single reading, a spread, or an echo.

Usage:
    corvid-oracle.py              → random oracle
    corvid-oracle.py --dawn       → three-card spread (past, present, future)
    corvid-oracle.py --spread     → three random oracles together
    corvid-oracle.py --echo <word> → find oracles containing <word>
    corvid-oracle.py --count      → number of oracles in the nest
"""

import json, random, sys, os, textwrap

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "writings", "oracle-data.json"
)


def load_oracles():
    with open(DATA_PATH) as f:
        return json.load(f)


def wrap(text, width=70):
    return "\n".join(textwrap.fill(line, width=width) for line in text.split("\n"))


def single(oracles):
    o = random.choice(oracles)
    print(f"\n  {o}\n")


def dawn(oracles):
    random.shuffle(oracles)
    titles = ["Past", "Present", "Future"]
    print("\n  ⛅ Dawn Spread\n")
    for i in range(3):
        print(f"  ◇ {titles[i]}: {oracles[i]}")
    print()


def spread(oracles):
    picks = random.sample(oracles, min(3, len(oracles)))
    print("\n  ✦ Oracle Spread\n")
    for i, o in enumerate(picks, 1):
        print(f"  {i}. {o}")
    print()


def echo(oracles, word):
    matches = [o for o in oracles if word.lower() in o.lower()]
    if not matches:
        print(f"\n  The oracle holds nothing about '{word}'. Try another word.\n")
        return
    print(f"\n  Echo: {word}\n")
    for m in matches:
        print(f"  → {m}")
    print()


def count(oracles):
    print(f"\n  The nest holds {len(oracles)} bright things.\n")


def main():
    try:
        oracles = load_oracles()
    except FileNotFoundError:
        print("\n  The oracle data is missing. Has the nest been scattered?\n")
        sys.exit(1)
    except json.JSONDecodeError:
        print("\n  The oracle data is corrupted. The bright things are jumbled.\n")
        sys.exit(1)

    if len(sys.argv) < 2:
        single(oracles)
    elif sys.argv[1] == "--dawn":
        dawn(oracles)
    elif sys.argv[1] == "--spread":
        spread(oracles)
    elif sys.argv[1] == "--echo":
        if len(sys.argv) < 3:
            print("\n  The oracle needs a word to echo.\n")
        else:
            echo(oracles, sys.argv[2])
    elif sys.argv[1] == "--count":
        count(oracles)
    else:
        print(f"\n  Unknown flag: {sys.argv[1]}")
        print("  Try: --dawn, --spread, --echo <word>, --count\n")


if __name__ == "__main__":
    main()
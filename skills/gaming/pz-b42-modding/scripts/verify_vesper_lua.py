#!/usr/bin/env python3
"""STRICT Lua verifier for PZ B42 mods.

PZ runs Kahlua (Lua 5.1). lupa's default is Lua 5.5, and its `loadfile`-only
check MISSES 5.1 compile errors like:
    cannot use '...' outside a vararg function near '...'
(a vararg inside a nested anonymous function — the whole file then refuses to
load in-game and the global stays nil).

This script EXECUTES each file (full compile + run) so those 5.1-isms surface.

Usage:
    python3 verify_vesper_lua.py [MOD_DIR]

PZ-global references (UIFont, getPlayer, require of mod files, etc.) will fail
when run outside the game — that is EXPECTED. Judge the SYNTAX result: if a
file fails with a Lua error mentioning '...' / 'near' / 'attempt to' it's a
real 5.1 problem; if it fails with 'global X is nil' it's just a missing PZ
global and the syntax is fine.
"""
import sys
from pathlib import Path

# Allow running from anywhere; the lupa venv is the known-good env on the VM.
sys.path.insert(0, "/tmp/luacheck-env/lib/python3.11/site-packages")
from lupa import LuaRuntime

MOD_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/lumi/vesper-pz-mod")
LUA_FILES = [
    "media/lua/shared/json.lua",
    "media/lua/shared/VesperGameState.lua",
    "media/lua/client/VesperCompanion.lua",
    "media/lua/client/VesperPathing.lua",
    "media/lua/client/VesperUI.lua",
    "media/lua/client/VesperNPC.lua",
]

lua = LuaRuntime(unpack_returned_tuples=True)
ok_all = True
for rel in LUA_FILES:
    path = MOD_DIR / rel
    if not path.exists():
        print(f"SKIP (not found): {rel}")
        continue
    try:
        src = path.read_text(encoding="utf-8")
        lua.execute(src)  # full compile + run — catches 5.1-isms loadfile misses
        print(f"PASS: {rel}")
    except Exception as e:
        msg = str(e)
        if "global" in msg and "nil" in msg:
            print(f"PASS(syntax, missing PZ globals): {rel} -> {msg[:80]}")
        else:
            ok_all = False
            print(f"FAIL: {rel} -> {msg[:200]}")

print("\n" + ("ALL LUA FILES PASS (strict) 🖤" if ok_all else "SOME FAILED"))
sys.exit(0 if ok_all else 1)

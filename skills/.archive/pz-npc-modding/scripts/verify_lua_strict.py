#!/usr/bin/env python3
"""STRICT Lua verifier for PZ mods (Kahlua = Lua 5.1).

WHY: PZ runs Kahlua (Lua 5.1). lupa's default is Lua 5.5, and plain
`loadfile` checks MISS Lua 5.1 compile errors like
'cannot use ... outside a vararg function' — hit 8/9/26: the whole
VesperNPC.lua refused to load and the module global was nil in-game
while the loadfile check said PASS.

This script EXECUTES each file (full compile + run) instead of just
loadfile. NOTE: PZ globals (getPlayer, UIFont, etc.) don't exist
outside the game, so files that reference them will error here — those
are false alarms. The signal that matters: a file that passed before
and now errors with a COMPILE message (varargs, syntax).

Usage:
  /tmp/luacheck-env/bin/python3 scripts/verify_lua_strict.py [MOD_DIR]

Requires lupa in a venv: /tmp/luacheck-env (python3.11 + lupa).
"""
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/luacheck-env/lib/python3.11/site-packages")
from lupa import LuaRuntime

MOD_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/lumi/vesper-pz-mod")
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
        print(f"SKIP (missing): {rel}")
        continue
    try:
        src = path.read_text(encoding="utf-8")
        lua.execute(src)  # full compile + run — catches 5.1-isms loadfile misses
        print(f"PASS: {rel}")
    except Exception as e:
        ok_all = False
        print(f"FAIL: {rel} -> {e}")

print("\n" + ("ALL LUA FILES PASS (strict)" if ok_all else "SOME FAILED"))
sys.exit(0 if ok_all else 1)

#!/usr/bin/env python3
"""Verify Lua files (syntax) + JSON round-trip using lupa (Lua embedded in Python).

Use when you need to syntax-check .lua files (e.g. a PZ mod) on a machine with
no Lua interpreter, or test a pure-Lua json.lua encoder/decoder.

Setup (PEP 668-safe, no sudo needed):
    python3 -m venv /tmp/luacheck-env
    /tmp/luacheck-env/bin/pip install lupa

Usage:
    python verify_lua.py [path/to/mod/dir]
    (defaults to /home/lumi/vesper-pz-mod; pass a dir with media/lua/ inside)

Harness gotchas (both hit for real 2026-08-09):
  - lupa's eval() only takes EXPRESSIONS. A statement like `local f, err = ...`
    fails with "unexpected symbol near 'local'". Wrap it in an IIFE:
        lua.eval("(function(p) ... end)(...)", arg)
  - Lua 5.5 (bundled in lupa) has NO `loadstring`; use `loadfile` for
    file-based compile checks.
  - Reading nested tables back from Lua: index with [1] (Lua is 1-based);
    Python-side [0] yields None even when the JSON decoded fine.
"""
import sys
from pathlib import Path

from lupa import LuaRuntime

MOD_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/lumi/vesper-pz-mod")

LUA_FILES = [
    "media/lua/shared/json.lua",
    "media/lua/shared/VesperGameState.lua",
    "media/lua/client/VesperPathing.lua",
    "media/lua/client/VesperUI.lua",
    "media/lua/client/VesperCompanion.lua",
]

failures = []

# 1. Syntax check: loadfile() compiles without executing.
lua = LuaRuntime(unpack_returned_tuples=True)
for rel in LUA_FILES:
    path = MOD_DIR / rel
    if not path.exists():
        print(f"  SKIP {rel} (missing)")
        continue
    try:
        # eval only takes expressions; wrap the statement in a function call.
        result = lua.eval(
            "(function(p) local f, err = loadfile(p); "
            "if f then return 'ok' else return nil, err end end)(...)",
            str(path),
        )
        if isinstance(result, tuple):
            status, err = result
            if not status:
                failures.append(f"{rel}: SYNTAX ERROR: {err}")
                print(f"  FAIL {rel}: {err}")
                continue
        print(f"  OK  {rel} (syntax)")
    except Exception as e:  # noqa: BLE001
        failures.append(f"{rel}: {e}")
        print(f"  FAIL {rel}: {e}")

print()

# 2. JSON round-trip test (if json.lua exists).
json_path = MOD_DIR / "media/lua/shared/json.lua"
if json_path.exists():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("json_mod = loadfile(...)()", str(json_path))
    json_mod = lua.globals().json_mod

    test = lua.table(
        player=lua.table(hp=78, hunger=45.5, x=1050, y=820, z=0),
        inventory=lua.table_from({"Base.CannedBeans", "Base.9mmRound"}),
        threats=lua.table_from({lua.table(type="zombie", distance=15)}),
        world="off",
    )
    encoded = json_mod.encode(test)
    print(f"  ENCODE: {encoded}")

    decoded = json_mod.decode(encoded)
    print(
        "  DECODE: player.hp={}, hunger={}, world={}".format(
            decoded["player"]["hp"], decoded["player"]["hunger"], decoded["world"]
        )
    )
    print(
        "  DECODE: inventory[1]={}, threats[1].type={}".format(
            decoded["inventory"][1], decoded["threats"][1]["type"]
        )
    )

    goal_json = (
        '{"goal": "scavenge_food", "priority": 8, "reason": "Hunger 45", '
        '"path": [[1050,820],[980,780]], "dialogue": "Let\'s go."}'
    )
    goal = json_mod.decode(goal_json)
    print(
        "  GOAL: goal={}, priority={}, path[1][0]={}".format(
            goal["goal"], goal["priority"], goal["path"][1][0]
        )
    )

print()
if failures:
    print(f"RESULT: {len(failures)} FAILURE(S)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: ALL CHECKS PASSED")
    sys.exit(0)

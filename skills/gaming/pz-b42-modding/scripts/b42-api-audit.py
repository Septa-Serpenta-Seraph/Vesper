#!/usr/bin/env python3
"""B42 API audit — verify every `obj:method()` call in the Vesper PZ mod Lua
against the decompiled B42 Java source.

Run when: a B42 mod shows "Object tried to call nil" on a method you think
exists, when porting B41-era reference code, or after a game version bump.

Usage:
    python3 b42-api-audit.py            # audit the default Lua dir
    python3 b42-api-audit.py /path/to/lua  /path/to/decompiled-java

Known false positives to expect (they are INHERITED methods, not bugs):
  - item:getHungerChange / getThirstChange  -> Food extends InventoryItem
  - panel:initialise/instantiate/addToUIManager/setVisible -> ISPanel is a
    LUA class (PZNS pattern), not in the Java tree
  - items:get / items:size -> Java ArrayList, not a decompiled class here
  - "local isWater = false" parsed as `isWater = false(` -> check the line;
    the real call is isWaterSquare()
"""
import re
import os
import sys

LUA_DIR = "/home/lumi/vesper-pz-mod/media/lua"
DECOMP_DIR = "/home/lumi/research/pz/b42-42.20.0"

# Map of common Lua receiver names -> Java class files to grep
RECEIVER_CLASSES = {
    "npc": ["IsoZombie.java", "IsoGameCharacter.java", "IsoObject.java", "IsoMovingObject.java"],
    "player": ["IsoPlayer.java", "IsoGameCharacter.java", "IsoObject.java"],
    "human": ["IsoPlayer.java", "IsoGameCharacter.java", "IsoObject.java"],
    "sq": ["IsoGridSquare.java", "IsoObject.java"],
    "other": ["IsoGridSquare.java", "IsoObject.java"],
    "cell": ["IsoCell.java"],
    "container": ["ItemContainer.java"],
    "items": ["ArrayList.java"],
    "item": ["InventoryItem.java", "Food.java", "ItemContainer.java"],
    "inv": ["InventoryItem.java", "ItemContainer.java"],
    "dest": ["InventoryItem.java", "ItemContainer.java"],
    "cont": ["ItemContainer.java"],
    "panel": ["ISPanel.java", "UIElement.java"],
    "hud": ["ISPlayerHud.java", "ISUIElement.java"],
    "screen": ["ISPlayerScreen.java"],
    "wp": ["WeatherPeriod.java"],
    "cm": ["ClimateManager.java"],
    "wo": ["IsoWorldObject.java", "IsoObject.java"],
    "tsq": ["IsoGridSquare.java"],
    "hSq": ["IsoGridSquare.java"],
    "pSq": ["IsoGridSquare.java"],
    "target": ["IsoZombie.java", "IsoGameCharacter.java"],
    "z0": ["IsoZombie.java", "IsoGameCharacter.java"],
    "obj": ["IsoObject.java"],
    "pf": ["PathFindBehavior2.java"],
    "npcClass": [],
    "panelClass": [],
}

SKIP_METHODS = {
    # local helper functions (our own code)
    "_dirToward", "_faceToward", "_itemScore", "_itemCategory", "_carriedBest",
    "_wantsItem", "_findScroungeTarget", "_inventorySummary",
    # Lua stdlib
    "lower", "find", "sub", "gsub", "match", "rep", "format", "abs", "floor",
    "max", "min", "random", "concat", "insert", "ipairs", "pairs", "tostring",
    "tonumber", "type", "sort", "gmatch",
    # known game globals (functions)
    "splitLines", "getDistanceBetween",
}

def find_methods(path):
    src = open(path).read()
    methods = []
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)[:.]([A-Za-z_][A-Za-z0-9_]*)\s*\(", src):
        receiver, method = m.group(1), m.group(2)
        line_start = src.rfind("\n", 0, m.start()) + 1
        line = src[line_start:m.start()]
        if "--" in line:
            continue
        methods.append((receiver, method))
    return methods

def check_method(receiver, method, decomp_dir):
    classes = RECEIVER_CLASSES.get(receiver, [])
    if not classes:
        return "unknown-receiver"
    for cls in classes:
        path = os.path.join(decomp_dir, cls)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8", errors="replace").read()
        if re.search(r"\b" + re.escape(method) + r"\s*\(", src):
            return "ok"
    return "MISSING"

def main():
    lua_dir = sys.argv[1] if len(sys.argv) > 1 else LUA_DIR
    decomp_dir = sys.argv[2] if len(sys.argv) > 2 else DECOMP_DIR
    files = []
    for root, _dirs, names in os.walk(lua_dir):
        for n in names:
            if n.endswith(".lua"):
                files.append(os.path.join(root, n))

    all_methods = {}
    for f in files:
        for receiver, method in find_methods(f):
            if method in SKIP_METHODS:
                continue
            key = (receiver, method)
            if key not in all_methods:
                all_methods[key] = os.path.basename(f)

    print("=" * 70)
    print(f"B42 API AUDIT ({decomp_dir})")
    print("=" * 70)
    missing = []
    ok_count = 0
    for (receiver, method), srcfile in sorted(all_methods.items()):
        status = check_method(receiver, method, decomp_dir)
        if status == "ok":
            ok_count += 1
        elif status == "MISSING":
            missing.append((receiver, method, srcfile))
            print(f"  MISSING  {receiver}:{method}  ({srcfile})")
        # unknown-receiver: report only genuinely suspicious method names
        elif method not in {"getItems", "size", "get", "DoRemoveItem", "AddItem", "Use",
                            "getType", "getSquare", "getX", "getY", "getZ", "isAlive",
                            "getHealth", "getInventory", "getHumanVisual", "setDir",
                            "setTarget", "getZombieCount", "getZombie", "getContainer",
                            "getGridSquare", "isWaterSquare", "getRoof", "getWorldObjects",
                            "getItem", "getInventoryWeight", "AddWorldInventoryItem",
                            "getCondition", "getConditionMax", "getHungerChange",
                            "getThirstChange", "isFood", "getZombies", "getGameTime",
                            "getTimeOfDay", "getRainIntensity", "haveRoofFull"}:
            print(f"  CHECK    {receiver}:{method}  ({srcfile})  [receiver unverified]")

    print("=" * 70)
    print(f"OK: {ok_count}   MISSING: {len(missing)}")
    if missing:
        print("\nMISSING METHODS — check inheritance before fixing:")
        for r, m, s in missing:
            print(f"  {r}:{m}  in {s}")

if __name__ == "__main__":
    main()

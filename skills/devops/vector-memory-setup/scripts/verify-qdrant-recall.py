#!/usr/bin/env python3
"""
verify-qdrant-recall.py — Test the qdrant memory plugin OUTSIDE the gateway.

The plugin caches `_available` at session start and never re-checks, so after
recreating/backfilling a collection you must restart the gateway before the
live tool works. This script runs the SAME initialize() + recall path the
gateway runs, without bouncing it — so you can confirm data + patched code
are good BEFORE asking the user to restart.

Usage:
    python3 verify-qdrant-recall.py "MiniMax H3 video ComfyUI" [profile] [limit]
    python3 verify-qdrant-recall.py --status                 # init + availability only

Reads config from ~/.hermes/profiles/<profile>/config.yaml (plugins.qdrant-memory)
and the plugin from ~/.hermes/profiles/<profile>/plugins/qdrant/__init__.py.
"""
import argparse
import json
import sys
from pathlib import Path

HOME = Path.home()
PROFILE = "vesper"


def load_plugin(profile: str):
    """Import the qdrant plugin module without the gateway. Returns the module."""
    plugin_path = HOME / ".hermes" / "profiles" / profile / "plugins" / "qdrant" / "__init__.py"
    if not plugin_path.exists():
        sys.exit(f"plugin not found: {plugin_path}")
    # hermes-agent root + its venv are needed for hermes_constants / agent.memory_provider
    agent_root = HOME / ".hermes" / "hermes-agent"
    venv_sites = sorted((agent_root / "venv" / "lib").glob("python*/site-packages"))
    for p in ([str(agent_root)] + [str(s) for s in venv_sites]):
        if p not in sys.path:
            sys.path.insert(0, p)
    sys.path.insert(0, str(plugin_path.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("qdrant_plugin", plugin_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_config(profile: str) -> dict:
    cfg_path = HOME / ".hermes" / "profiles" / profile / "config.yaml"
    if not cfg_path.exists():
        return {}
    import yaml
    with open(cfg_path) as f:
        all_cfg = yaml.safe_load(f) or {}
    return all_cfg.get("plugins", {}).get("qdrant-memory", {}) or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default=None)
    ap.add_argument("profile", nargs="?", default=PROFILE)
    ap.add_argument("limit", nargs="?", type=int, default=3)
    args = ap.parse_args()

    mod = load_plugin(args.profile)
    cfg = load_config(args.profile)
    prov = mod.QdrantMemoryProvider(cfg)
    prov.initialize(f"verify-{args.profile}")
    print(f"available: {prov._available}")
    print(f"collection: {prov._collection}")

    if args.query is None:
        return
    out = prov._handle_qdrant_recall({"query": args.query, "limit": args.limit})
    data = json.loads(out)
    print(f"count: {data.get('count', 0)}")
    for r in data.get("results", []):
        print(f" - {r['date']} | sim: {r['similarity']} | {r['text'][:90]}")
    if data.get("count", 0) == 0:
        print("!! recall empty — see vector-memory-setup troubleshooting "
              "(timestamp bug / availability caching / dims mismatch)")
        sys.exit(2)


if __name__ == "__main__":
    main()

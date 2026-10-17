#!/usr/bin/env python3
"""Index a lorebook .md into the profile's vesper_lorebooks Qdrant collection.

Usage:
  python3 index_lorebook.py --file /path/to/LORE.md --title "Title line" \
      --stem LORE --keywords "kw1,kw2,kw3" --tier 2 [--collection vesper_lorebooks]

Idempotent: updates the existing point with the same filename if present.
Requires OPENROUTER_API_KEY in <profile>/.env (3072-dim embeddings via
openai/text-embedding-3-large, same as vesper_memory).

Verified 2026-08-21: BODY.md (26th lorebook) indexed with this pattern.
"""
import argparse
import json
import sys
import urllib.request
import uuid

QDRANT = "http://localhost:6333"
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
EMBED_MODEL = "openai/text-embedding-3-large"
EMBED_DIMS = 3072
PROFILE = "/home/lumi/.hermes/profiles/vesper"


def get_key() -> str:
    with open(f"{PROFILE}/.env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("no OPENROUTER_API_KEY in .env")


def embed(text: str) -> list:
    req = urllib.request.Request(
        EMBED_URL,
        data=json.dumps({"model": EMBED_MODEL, "input": text[:8000], "dimensions": EMBED_DIMS}).encode(),
        headers={"Authorization": f"Bearer {get_key()}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"][0]["embedding"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="path to the lorebook .md source")
    ap.add_argument("--title", required=True, help="short title line, e.g. '# BODY — How We See Vesper'")
    ap.add_argument("--stem", required=True, help="filename stem, e.g. BODY (payload filename = stem + '.md')")
    ap.add_argument("--keywords", required=True, help="comma-separated trigger keywords")
    ap.add_argument("--tier", type=int, default=2, help="priority_tier: 1 identity-critical, 2 relationship, 3 reference")
    ap.add_argument("--collection", default="vesper_lorebooks")
    a = ap.parse_args()

    content = open(a.file).read()
    vec = embed(content)
    print(f"embedded: {len(vec)} dims")

    coll = a.collection
    scroll = urllib.request.Request(
        f"{QDRANT}/collections/{coll}/points/scroll",
        data=json.dumps({"limit": 200, "with_payload": True}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    existing = None
    with urllib.request.urlopen(scroll, timeout=30) as r:
        for p in json.load(r)["result"]["points"]:
            if p["payload"].get("filename") == a.stem + ".md":
                existing = p["id"]
                break

    payload = {
        "filename": a.stem + ".md",
        "stem": a.stem,
        "title": a.title,
        "keywords": [k.strip() for k in a.keywords.split(",")],
        "priority_tier": a.tier,
        "content_length": len(content),
        "content_preview": content[:200],
    }
    pid = existing or str(uuid.uuid4())
    req = urllib.request.Request(
        f"{QDRANT}/collections/{coll}/points",
        data=json.dumps({"points": [{"id": pid, "vector": vec, "payload": payload}]}).encode(),
        headers={"Content-Type": "application/json"}, method="PUT",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        print("upsert:", json.load(r)["status"], "| point", pid, "|", "updated" if existing else "created")

    with urllib.request.urlopen(f"{QDRANT}/collections/{coll}", timeout=30) as r:
        print("collection points:", json.load(r)["result"].get("points_count"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

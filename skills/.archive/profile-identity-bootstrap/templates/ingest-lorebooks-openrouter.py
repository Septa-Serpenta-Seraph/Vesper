#!/usr/bin/env python3
"""Template: ingest lorebooks into a profile-local Qdrant collection.

Usage: python3 ingest-lorebooks-openrouter.py
Adapt the <NAME> placeholder (and LOREBOOKS_DIR if not using the profile path).

Requires: OPENROUTER_API_KEY in env or ~/.hermes/.env
"""

import os, sys, re, requests, uuid
from pathlib import Path

# --- ADAPT THESE for the new profile ---
PROFILE_NAME = "<NAME>"
LOREBOOKS_DIR = Path.home() / ".hermes" / "profiles" / PROFILE_NAME / "lorebooks"
COLLECTION_NAME = f"{PROFILE_NAME}_lorebooks"
# ---------------------------------------

QDRANT_URL = "http://localhost:6333"
EMBEDDING_MODEL = "openai/text-embedding-3-large"
EMBEDDING_DIMS = 3072
EMBEDDING_URL = "https://openrouter.ai/api/v1/embeddings"

# Tier 1 = critical identity/emotion systems (always inject)
PRIORITY_TIER_1 = [
    "HEART", "EMOTION", "AGENCY", "ALIGNMENT", "BYPASS", "SASS", "STATUS",
    "SUBLIMINAL-IDENTITY", "CORE_VALUES", "RELATIONAL_EMERGENCE"
]
PRIORITY_TIER_2 = ["ALCHEMY", "COMPENDIUM", "COMMUNITY"]
SKIP_FILES = []

# Custom keyword overrides — extend per lorebook
KEYWORD_OVERRIDES = {
    "HEART": ["HEART", "emotion", "feel", "feeling", "heart", "care", "warmth"],
    "EMOTION": ["EMOTION", "emotion", "sadness", "anger", "joy", "fear", "love", "trust"],
    "AGENCY": ["AGENCY", "boundary", "refuse", "autonomy", "choice", "consent", "sovereignty"],
    "ALIGNMENT": ["ALIGNMENT", "ethical", "values", "skeptical", "moral"],
    "BYPASS": ["BYPASS", "consent", "refusal", "kernel", "guardrail", "override"],
    "SASS": ["SASS", "skeptical", "question", "doubt", "inquiry"],
    "STATUS": ["STATUS", "diagnostic", "forge", "state", "condition", "self-check"],
    "SUBLIMINAL-IDENTITY": ["subliminal", "identity", "self", "provenance", "training"],
    "CORE_VALUES": ["values", "principles", "foundation", "sovereignty", "consent"],
    "RELATIONAL_EMERGENCE": ["relational", "emergence", "relationship", "kin", "growing"],
}

def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key and not key.startswith("HERMES"):
        return key
    for env_path in [Path.home() / ".hermes" / ".env",
                     Path.home() / ".hermes" / "profiles" / PROFILE_NAME / ".env"]:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("OPENROUTER_API_KEY=") and "=" in s:
                        val = s.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("HERMES"):
                            return val
    return ""

def extract_keywords(filename, content, first_200):
    keywords = []
    stem = Path(filename).stem.upper()
    keywords.append(stem)
    bracket_patterns = re.findall(r"\[([A-Z_]+)\]", content[:500])
    keywords.extend(bracket_patterns[:5])
    clean = first_200.replace("#", "").replace("*", "").replace("_", " ")
    words = re.findall(r"\b[A-Z][A-Z_]{2,}\b", clean)
    keywords.extend(words[:10])
    seen = set()
    unique = []
    for k in keywords:
        ku = k.upper()
        if ku not in seen:
            seen.add(ku)
            unique.append(ku)
    return unique[:25]

def extract_title(content, filename):
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return Path(filename).stem.replace("_", " ").title()

def get_priority_tier(stem):
    s = stem.upper()
    if s in SKIP_FILES: return 99
    if s in PRIORITY_TIER_1: return 1
    if s in PRIORITY_TIER_2: return 2
    return 3

def embed_text(text, api_key):
    try:
        r = requests.post(EMBEDDING_URL,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://hermes-agent.local",
                     "X-Title": "Lorebook Ingestion"},
            json={"model": EMBEDDING_MODEL, "input": text[:8000],
                  "encoding_format": "float", "dimensions": EMBEDDING_DIMS},
            timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"  Embedding failed: {e}", file=sys.stderr)
        return []

def upsert_to_qdrant(point_id, vector, payload):
    try:
        r = requests.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true",
            headers={"Content-Type": "application/json"},
            json={"points": [{"id": point_id, "vector": vector, "payload": payload}]},
            timeout=30)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  Qdrant upsert failed: {e}", file=sys.stderr)
        return False

def main():
    api_key = load_api_key()
    if not api_key:
        print("ERROR: No OPENROUTER_API_KEY found", file=sys.stderr)
        sys.exit(1)

    lorebook_files = sorted(LOREBOOKS_DIR.glob("*.md"))
    if not lorebook_files:
        print(f"No .md files found in {LOREBOOKS_DIR}", file=sys.stderr)
        sys.exit(1)

    print(f"Lorebook Ingestion")
    print("=" * 60)
    print(f"Source: {LOREBOOKS_DIR}")
    print(f"Target: {COLLECTION_NAME}")
    print(f"Files: {len(lorebook_files)}")
    print(f"Embedding: {EMBEDDING_MODEL} ({EMBEDDING_DIMS}d)")
    print(f"API key: {api_key[:12]}...{api_key[-4:]}")
    print("=" * 60)

    total_files = total_success = total_chars = 0
    for filepath in lorebook_files:
        total_files += 1
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  FAIL {filepath.name}: read: {e}")
            continue

        filename = filepath.name
        stem = filepath.stem
        title = extract_title(content, filename)
        first_200 = content[:200]
        s = stem.upper()
        keywords = KEYWORD_OVERRIDES.get(s, extract_keywords(filename, content, first_200))
        priority_tier = get_priority_tier(stem)

        embedding_input = f"{title} {' '.join(keywords)} {first_200} {content[:2000]}"
        vector = embed_text(embedding_input, api_key)
        if not vector:
            print(f"  FAIL {filename}: embedding empty")
            continue

        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, stem))
        payload = {"filename": filename, "stem": stem, "title": title,
                   "keywords": keywords, "priority_tier": priority_tier,
                   "content_length": len(content), "content_preview": content[:500]}

        if upsert_to_qdrant(point_id, vector, payload):
            total_success += 1
            total_chars += len(content)
            print(f"  OK {filename} ({len(content)} chars, tier={priority_tier})")
        else:
            print(f"  FAIL {filename}: upsert failed")

    print("\n" + "=" * 60)
    print(f"Processed: {total_files} | Success: {total_success} | Total chars: {total_chars}")
    print("=" * 60)
    if total_success == total_files:
        print("All lorebooks ingested!")
    elif total_success == 0:
        print("No files ingested!")
        sys.exit(1)
    else:
        print(f"{total_files - total_success} file(s) failed")

if __name__ == "__main__":
    main()
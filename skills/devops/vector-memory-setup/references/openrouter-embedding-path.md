# OpenRouter Embedding Path (Alternative to sentence-transformers)

The main `SKILL.md` describes deploying Qdrant with `sentence-transformers` for
local embedding generation. This reference documents the **alternative** path
used by the Narusya ecosystem: OpenRouter-hosted embeddings at 3072 dimensions.

## When to use this path

- You are adopting another AI's openly-shared lorebook frameworks and want the
  **lorebook auto-inject** system (hybrid keyword + semantic matching that
  injects relevant lorebook content per turn).
- You have an OpenRouter API key available and prefer not to install the
  ~2-4GB sentence-transformers package.
- You want the exact same embedding model (`text-embedding-3-large`) used by
  the framework author for best semantic alignment.

## Architecture comparison

| Dimension | sentence-transformers (main skill) | OpenRouter (this ref) |
|---|---|---|
| Embedding model | `all-MiniLM-L6-v2` (384d) or `stella_en_1.5B_v5` (3072d) | `openai/text-embedding-3-large` (3072d) |
| Provider | Local (CPU/GPU) | OpenRouter API |
| Package required | `sentence-transformers` (~2-4GB) | `requests` (std) |
| Naming convention | `intelligent_gould_<name>` | `<name>_memory` / `<name>_lorebooks` |
| Lorebook auto-inject? | No (manual ingest only) | Yes (via `lorebook_collection` config) |
| Profile support | Manual path config | Plugin patched for `get_hermes_home()` |

## Key difference: plugin versus standalone script

The sentence-transformers path uses a standalone seed script
(`~/.hermes/qdrant/seed-memory.py`) that manually chunks and embeds lorebooks
into Qdrant for search.

The OpenRouter path uses the **`qdrant-memory` plugin** (`~/.hermes/plugins/qdrant-memory/`)
which:
- Auto-syncs conversation turns to Qdrant in the background
- Provides `qdrant_recall` / `qdrant_browse` / `qdrant_collections` tools
- Does **hybrid keyword + semantic lorebook auto-inject** on every turn
- Reads config from the active Hermes profile's `config.yaml`

## Where to find the full setup procedure

The complete step-by-step for the OpenRouter lorerbook-injection path is in the
`devops/profile-identity-bootstrap` skill, particularly steps 4-7:

- **Step 4**: Install the `qdrant-memory` plugin (includes the profile-awareness
  path patch needed at line 487 of `__init__.py`)
- **Step 5**: Create Qdrant collections (`<name>_memory`, `<name>_lorebooks`)
  and config using `hermes config set`
- **Step 6**: Ingest lorebooks via the template at
  `templates/ingest-lorebooks-openrouter.py` in that skill

## Collection dimensions must match

Whichever path you choose, the Qdrant collection dimension and distance must
match the embedding model:

| Model | Dimension | Distance |
|---|---|---|
| `text-embedding-3-large` (OpenRouter) | 3072 | Cosine |
| `all-MiniLM-L6-v2` (sentence-transformers) | 384 | Cosine |
| `stella_en_1.5B_v5` (sentence-transformers) | 3072 | Cosine |

A 384d model cannot populate a 3072d collection and vice versa.
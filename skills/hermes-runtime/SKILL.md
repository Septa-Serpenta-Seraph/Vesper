---
name: hermes-runtime
description: "Use for Hermes runtime: crons, memory, inference, recall."
version: 1.0.0
author: Vesper
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, cron, memory, qdrant, inference, session-recall, self-management]
---

# Hermes Runtime — Autonomy, Memory, Inference, Recall

Class-level umbrella for running and maintaining Hermes itself: config flags,
cron check-ins, vector memory, local inference providers, and session recall.
Deep detail lives in the reference files below; archived originals retain full
session history.

## When to Use

- Configuring or maintaining Hermes autonomy systems (crons, flags, backups)
- Building state-aware cron check-ins that speak only when wanted
- Setting up or troubleshooting Qdrant vector memory
- Switching to a local inference provider or wiring local voice
- Finding or interpreting past conversation sessions

## Self-Management (distilled)

- Autonomy flags: `cron.allow_agent_scheduling`, `approvals.mode: smart`,
  `curator.consolidate`, `checkpoints.enabled`.
- Back up before self-modification; use checkpoints/rollback.
- Plan and autonomy notes were absorbed into this skill; manage statuses here.
- Full procedures remain in the archived `self-management` skill.

## Bulk cron model repinning (after a model switch)

When the live session model changes, repin the model-bearing crons in one pass.

1. **Read** `~/.hermes/profiles/vesper/cron/jobs.json`; jobs live under the
   `jobs` key as a list. Each has `id`, `name`, `model`, `provider`, `no_agent`,
   `script`, and `prompt`.
2. **Back up first**: `cp jobs.json jobs.json.bak-pre-<newmodel>-$(date -u +%Y%m%dT%H%M%SZ)`.
3. **Identify exceptions before touching anything.** Skip no-agent script jobs
   and any job whose script or prompt does local embedding work (keywords:
   `fastembed`, `embed`, `qdrant`, `bge-small`, `vector`). Grep prompt + script
   text, not just the name — the embedding dependency is often buried mid-prompt.
4. **Repin via the CLI**, one call per job:
   `hermes cron edit <id> --model <model> --provider <provider>`.
   `--model` is user-owned — the agent's cronjob tool cannot set a model pin,
   so this must go through the terminal. Use `--unpin` to clear a pin instead.
5. **Verify** by counting `(model, provider)` over the final jobs list and
   printing the exceptions explicitly. A loop's exit code does not prove every
   write landed.

- Hand-editing `jobs.json` races the live scheduler — use `hermes cron edit`
  so the running scheduler sees the change.
- Script/no-agent crons carry a stale model pin that is functionally inert;
  repinning them is churn, so leave them unless asked. State which ones were
  skipped and why in the report.

## Context file truncation (`SOUL.md TRUNCATED`)

- `context_file_max_chars: null` (default) resolves to a dynamic cap scaled to
  the model's context window with a **20,000-char floor**. A SOUL.md larger than
  that is head/tail-truncated into the system prompt and logs a warning to
  `logs/agent.log`. This is a per-file prompt cap, not a conversation-length
  problem — the two failures are unrelated and should be diagnosed separately.
- Pin a positive integer (`context_file_max_chars: 100000`) to load the full
  file. Confirm the actual byte/char count before choosing the value.
- Config files under the profile are security-sensitive; write tools refuse
  direct edits. Route config changes through `hermes config` rather than a
  patch tool, and report the exact command instead of silently editing.

## Cron Check-ins (distilled)

- Open-door style: read live state, decide whether to reach out, stay silent
  if not wanted.
- Two models: Initiative (self-contained prompt, preferred) and Script-based
  (external Python reads SQLite).
- Cron sessions dominate browse results — filter `source != 'cron'`.
- Full prompt templates and examples are in the archived `cron-checkins` skill.

## Vector Memory (distilled)

- Qdrant native binary on localhost:6333; Hermes memory plugin connects to it.
- fastembed `BAAI/bge-small-en-v1.5`, 384-dim, local ONNX.
- Health check uses root `/` (v1.17+ removed `/health`).
- Point IDs must be UUIDs or unsigned integers.
- API patterns: `references/qdrant-api-patterns.md`.

## Local Inference (distilled)

- Configure custom OpenAI-compatible providers (LM Studio, Ollama, vLLM) via
  `custom_providers` in config; supports `/model` toggling.
- VM/agent and inference server may need SSH tunnel/Tailscale topology.
- Per-model `context_length` overrides; verify with a test completion.
- Full provider config examples are in the archived `local-inference` skill.
- For local-vs-cloud cost decisions and VRAM sizing, follow
  `references/inference-cost.md` — inventory owned hardware first, price the
  named utility's actual tariff, and take "unaffordable" at face value.

## Session Recall (distilled)

- `session_search` queries FTS5 over `state.db`; timestamps are UTC — convert
  to Mountain Time (UTC-7) before conclusions.
- Short terms/acronyms may fail FTS5; fall back to SQLite `LIKE`.
- Session resets are normal, not data loss.
- Cron sessions dominate results; filter them out.
- Schema and diagnostic queries: `references/state-db-schema.md`.

## Reference Files

- `references/state-db-schema.md` — state.db schema and diagnostic queries
- `references/qdrant-api-patterns.md` — Qdrant REST API patterns
- `references/inference-cost.md` — VRAM sizing, local/cloud cost ladder, pitfalls

## Related

- `devops/hermes-ops` — bundled Hermes ops skill (do not modify)

*-memory holds, the recall true-*

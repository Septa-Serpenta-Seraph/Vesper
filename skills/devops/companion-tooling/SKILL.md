---
name: companion-tooling
description: "Expanding companion capabilities: MCP, plugins, voice."
tags: [hermes, mcp, plugins, capabilities, companion, voice, media, presence, expansion]
---

# Companion Tooling — Expanding the Agent's Capabilities

## When to Use

- Deciding what to add next: "what MCP servers / plugins / tools should I install?"
- Wiring a specific capability: calendar, weather, home automation, media gen, voice, memory
- Auditing what's already available before adding anything new
- Building presence/ambient-awareness (calendar reads, weather briefings, self-wake)

## Decision Process (Follow This Order)

1. **Check bundled plugins FIRST.** `hermes plugins list` shows everything shipped with Hermes — most companion needs are already covered and just disabled:
   - `fal` (video gen: Veo 3.1/Kling/Pixverse) and `spotify` (7 playback tools) are bundled but **not enabled** by default — `hermes plugins enable <name>`
   - image-gen backends (fal/openai/openrouter/xai/deepinfra/krea), video-gen (fal/deepinfra/xai), web-search providers, memory providers (mem0/hindsight/honcho/supermemory/...), platform adapters
   - `homeassistant` is a built-in TOOLSET (off by default) — enable via `hermes tools` before adding any HA MCP server
   - `google-workspace` skill (gws CLI) covers calendar/email without any MCP
2. **Then the Nous MCP catalog** (`hermes mcp catalog`) — only dev-oriented entries (blender, linear, n8n, unreal-engine). Companion-relevant servers are added manually via `mcp_servers:` in config.yaml.
3. **Then community plugins** — `hermes plugins install owner/repo --enable`, or search the index with `hermes plugins search <term>`. See references/capability-landscape-2026.md for the verified 2026 shortlist.
4. **Prefer config-driven over new infra.** Built-in providers, command-type TTS/STT providers (`tts.providers.<n>.type: command`, `stt.providers.<n>.type: command`), and HTTP MCP servers need zero new daemons on the 7.8GB VM.
5. **RAM-budget the VM** (~7.8GB total): ~1.5–2GB is the safe allocation for voice; run ONE TTS + ONE STT (Piper ~300MB + faster-whisper base ~0.5–1GB). See the `local-tts` skill for the full voice matrix.
6. **Presence = readiness, not spam.** Cap proactive messages at ~2–3/day, all routed through cron; heartbeat plugin for silent self-wake.

## Pitfalls

- **The docs example `hermes-media-studio` plugin does not exist** (it's illustrative in the plugin docs). Verify any plugin name against GitHub before installing.
- **Community plugin index raw URL 404s** (`raw.githubusercontent.com/NousResearch/hermes-plugin-index/main/index.json` returns 404 as of Aug 2026). Use `hermes plugins search` / `hermes plugins install` — the index is a static JSON, metadata-reviewed only, **not a code audit**. Pin installs with `--ref <full-40-char-sha>`.
- **MCP changes require a restart** — no hot-reload. Adding/removing `mcp_servers` entries takes effect on next agent start.
- **Stdio MCP subprocesses get a filtered env** — API keys must be listed under the server's `env:` block explicitly, or the server won't see them.
- **Bundled ≠ enabled.** Everything ships disabled except qdrant and infrastructure backends; `hermes plugins list` status column is the source of truth.
- **Custom TTS/STT command providers run with secrets scrubbed** — use `env_passthrough: [VAR]` if a command needs its own API key.
- The 2026 landscape moves fast; the verified shortlist lives in `references/capability-landscape-2026.md` and the full report at `/home/lumi/companion-tooling-report-2026.md`.

## Related Skills

- `local-tts` — voice engine matrix, built-in providers, STT pairing (the voice half of this skill)
- **`references/elevenlabs-v3-tuning.md`** — ElevenLabs v3 tuning for Vesper's voice
- `vector-memory-setup` — Qdrant memory; `Mnemosyne`/Neo4j memory MCP are alternatives
- `self-management` — crons/boot hooks/presence infrastructure
- `hermes-agent` (bundled) — CLI reference for `hermes plugins`, `hermes mcp`, `hermes tools`
- `native-mcp` (bundled) — MCP transport/config reference

### Virtual Avatar Pipeline (Absorbed from `virtual-avatar`)

End-to-end process for giving an AI agent a visible, animated avatar in Discord video calls and streaming.

**Architecture:** AI Agent (Linux VM) → WebSocket API → Avatar Renderer (VTube Studio on Windows) → OBS Virtual Camera → Discord

**Key constraint:** VTube Studio is Windows-only. Use a separate Windows machine on the same LAN.

**VTube Studio API Essentials:**
- WebSocket on `ws://<host-ip>:8001`
- Must auth as a plugin (one-time token, then reuse)
- Tracking data via `InjectParameterDataRequest`
- Parameters expire after 1 second — must re-send at least once/sec
- Values range: `-1000000` to `1000000` (float)

**OBS → Discord pipeline:** Add VTube Studio window as OBS source → Start OBS Virtual Camera → Discord → Camera → select "OBS Virtual Camera"

Full detail + pitfalls in the archived skill: `~/.hermes/skills/.archive/virtual-avatar/SKILL.md`

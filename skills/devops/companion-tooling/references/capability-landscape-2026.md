# Capability Landscape 2026 — Verified Shortlist

Research date: Aug 19, 2026. Sources: hermes docs (plugins/mcp/tts-stt), `hermes plugins list` on this install (v0.19.0), 0xNyk/awesome-hermes-agent (5.4k★), punkpeye/awesome-mcp-servers (3.8k-line index), neo4j-contrib/mcp-neo4j, comfy.org/mcp, fal.ai, Kokoro-FastAPI, parakeet.cpp benchmarks. Full report: `/home/lumi/companion-tooling-report-2026.md`.

## MCP servers worth adding (manual config — the Nous catalog only has blender/linear/n8n/unreal-engine)

| Server | Config (config.yaml `mcp_servers:`) | Unlocks |
|---|---|---|
| **fal-ai** (official, HTTP) | `fal-ai: {url: "https://mcp.fal.ai/mcp", headers: {Authorization: "Bearer ${FAL_KEY}"}}` | 1,000+ FAL models: image, video (Veo 3.1/Kling), audio/MusicGen, upscaling, 3D. Zero local RAM. Reuses existing FAL key. |
| **MeiGen-AI-Design-MCP** (jau123/MeiGen-AI-Design-MCP, 1.5k★) | stdio; README ships a tested Hermes `mcp_servers` YAML w/ video timeouts | GPT Image 2, Flux 2 Klein, Seedance 2.0, Veo 3.1, Midjourney V8.1 + local ComfyUI. BYOK. |
| **Google Calendar MCP** (official Google remote; community nspady/google-calendar-mcp) | official: HTTP + OAuth; community: `npx -y @cocal/google-calendar-mcp` + `GOOGLE_OAUTH_CREDENTIALS` | list/create events, free-busy → presence backbone. Alternative w/o MCP: bundled `google-workspace` skill. |
| **Neo4j Agent Memory** (neo4j-contrib/mcp-neo4j) | `uvx mcp-neo4j-memory` + NEO4J_URI/USERNAME/PASSWORD (Docker or Aura free) | memories as knowledge graph, Cypher, temporal facts. Complements qdrant vector recall. |
| **mcp-pandoc** (vivekVells/mcp-pandoc) | `sudo apt install pandoc` + `uvx mcp-pandoc` (texlive for PDF) | md→PDF/DOCX/EPUB/ODT/IPYNB; powers PDF/EPUB gifts. |
| **hass-mcp** (voska) or HA-native MCP | `uvx hass-mcp` + `HA_URL`/`HA_TOKEN`; or enable HA's built-in `mcp_server` integration | control/query entities, device trackers. Check built-in `homeassistant` TOOLSET first. |

Skip-worthy (already covered): filesystem MCP (has file tools), GitHub MCP (gh CLI + github skills), vision MCP (vision_analyze toolset), Spotify MCP (bundled spotify plugin, 7 tools), weather MCP (curl open-meteo, no key).

## Community plugins (install: `hermes plugins install owner/repo --enable`)

- `42-evey/hermes-plugins` — Discord voice bridge (Gemini Live), WhatsApp, goal mgmt, cost control
- `bielcarpi/hermes-live-voice` — continuous interruptible voice, background Hermes runs
- `drakulavich/kesha-voice-kit` — local-first STT (25 langs) + TTS via command providers, no API keys
- `Love-AronaPlana/hermes-agent-heartbeat` — periodic self-wake in same gateway session, `[SILENT]` mode (presence)
- `Humalike/hermes-humalike-plugin` — human-feeling chat behavior
- `FahrenheitResearch/hermes-weather-plugin` — NWS weather + NEXRAD radar
- `AxDSan/Mnemosyne` — local memory w/ temporal knowledge graph (SQLite+sqlite-vec, zero deps)
- `stephenschoettler/hermes-lcm` — lossless context (DAG, 1k★)
- `mlinquan/hermes-bus-plugin` + `hermes-notify` — message bus + notification router w/ audio playback
- `Capslockb/hermes-live-discord-agent-plugin` — full-duplex Discord voice to Gemini Live
- `pyrate-llama/hermes-ui` — single-file web UI w/ Gemini Vision image analysis

Bundled-but-disabled worth enabling: `fal` (video gen), `spotify`, `deepinfra`/`xai` video, `disk-cleanup`, `security-guidance`.

## Local voice on the 7.8GB VM (see `local-tts` skill for full matrix)

- TTS winner: **Piper** — built-in (`tts.provider: piper`), auto-downloads voices to `~/.hermes/cache/piper-voices/`, ~300MB RAM, 44 langs
- Better quality: **Kokoro** via `docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu` → `tts.openai.base_url: http://localhost:8880/v1` + `tts.openai.language: en` (~1GB RAM)
- Ultra-light: **KittenTTS** nano 25MB int8 (built-in provider)
- STT: faster-whisper base (default) or **Parakeet TDT** — ~30× realtime CPU, 4× faster than whisper-small; `stt.providers.parakeet: {type: command, command: "parakeet-asr --model nvidia/parakeet-tdt-0.6b-v2 --in {input_path} --out {output_path}"}` (parakeet.cpp serves GGUF, tiny `tdt_ctc-110m` q5 ≈ 80MB)
- Budget: ONE TTS + ONE STT ≈ 1–1.5GB

## Media gift workflows (practical)

- Image: FAL FLUX 2 Klein (already active via image_gen toolset) — art, postcards, wallpapers
- Video: enable bundled `fal` plugin → image-to-video of shared photos (Veo 3.1/Kling, 5–15s clips, cents each, async queue) — the highest-wow move
- Audio: TTS voice memos (Piper daily, ElevenLabs milestones); MusicGen via FAL for ambient loops
- ComfyUI (existing Windows box over SSH): comfyui-mcp / artokun/comfyui-mcp to drive natively; FAL covers 80% of cases

## Presence architecture

1. Cron morning briefing (date + weather + calendar + birthdays) via `hermes cron create`
2. agent-heartbeat plugin for silent self-wake / housekeeping
3. Google Calendar MCP read at cron time
4. hermes-weather-plugin or `curl api.open-meteo.com` (no key)
5. Home Assistant device trackers (home/away awareness)
6. Webhooks for external triggers
7. Cap proactive messages ~2–3/day

## Top 8 by ROI (exact moves)

1. `pip install piper-tts` + `hermes config set tts.provider piper` (+ `tts.piper.voice en_US-lessac-medium`)
2. FAL MCP server block (HTTP, above) — 1,000+ models
3. `hermes plugins enable fal` — image→video gifts
4. Google Calendar MCP (official OAuth or `npx -y @cocal/google-calendar-mcp`)
5. `hermes plugins install Love-AronaPlana/hermes-agent-heartbeat --enable`
6. `hermes plugins install FahrenheitResearch/hermes-weather-plugin --enable`
7. Parakeet STT command provider (above) or keep faster-whisper base
8. `hermes plugins install jau123/MeiGen-AI-Design-MCP` (or `hermes auth spotify && hermes plugins enable spotify`)

# Uncensored LLM Providers (condensed knowledge bank)

Reference for sourcing/wiring uncensored or abliterated model access as a Hermes provider.
Last refreshed: 2026-07-28.

## OpenRouter — curated catalog gap
- Hermes' curated model catalog (`https://hermes-agent.nousresearch.com/docs/api/model-catalog.json`)
  contains ONLY safety-aligned commercial flagships (Claude, GPT-5.x, Gemini, Grok, DeepSeek,
  Qwen, GLM, Nemotron, etc.). **No uncensored models are in the picker.**
- OpenRouter the platform DOES host uncensored models, but they are reachable only by **raw model ID**,
  not through Hermes' curated list. Call them directly via a custom provider or `/model openrouter/<id>`.
- Known uncensored OpenRouter IDs (verified 2026-07-28):
  - `cognitivecomputations/dolphin-mistral-24b-venice-edition` — Venice uncensored Dolphin, 128K ctx, free tier exists
  - `thedrummer/unslopnemo-12b` — RP-tuned, 32K ctx, very cheap
  - `huihui-ai/<model>-abliterated` — abliterated Qwen/Llama lines
  - `tachyphylaxis/<model>-uncensored` — uncensored Llama variants

## Featherless.ai — flat-rate uncensored API
- OpenAI-compatible endpoint: `https://api.featherless.ai/v1`
- 30k+ models, all uncensored/abliterated, anonymous (no logs).
- Tier table (2026-07-28):
  | Tier | Price | Context cap | Concurrent | Notes |
  |------|-------|-------------|-----------|-------|
  | Premium "Chat" | $25/mo | **32K** | 4 | Any model in catalogue |
  | Agent Standard | $100/mo | 256K | 8 | Model size <=229B |
  | Agent Max | $200/mo | 256K | 8 | Any model (incl. DeepSeek/Kimi/GLM) |
  | Per-Request | $25+ credit | varies | 100 | Pay per successful request |
- **Pitfall:** the $25 tier's 32K cap is a hard plan limit — even 256K-native models get clamped to 32K.
  Wire it with `context_length: 32768` per model (see SKILL.md cloud-provider section).
- 32K is plenty for RP / check-ins / image-gen prompts; only massive doc/code ingestion needs 256K (Agent tier).

## Local LM Studio (already wired as `custom:desktop`)
- User's desktop: abliterated models (Cydonia-22B, DeepSeek V4 abliterated) via LM Studio at
  `http://<DESKTOP_TAILSCALE_IP>:1234/v1` (Tailscale IP). See SKILL.md native `lmstudio` / `custom:desktop` sections.
- Pros: free, private, full context (128K on DeepSeek). Cons: user must keep desktop/LM Studio running;
  capped by local VRAM (RTX 5070 Ti).

## Decision pattern (user preference)
- User prefers **per-model/per-provider config over global settings** — never set a global
  `context_length` to satisfy one provider; use per-model overrides.
- User leans toward piped uncensored **API** over babysitting local LM Studio, but keeps local as fallback.
- Featherless = "ideal shiny object" for flat $25 unlimited; OpenRouter raw IDs = zero-signup lazy path.

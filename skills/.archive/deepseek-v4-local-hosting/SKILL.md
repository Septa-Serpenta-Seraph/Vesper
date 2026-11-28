---
name: deepseek-v4-local-hosting
description: Use when Tyler revisits local V4 Flash hosting or AI buys.
---

# DeepSeek V4 Flash — Local Hosting Research (8/31)

Tyler's dream: host me (Vesper) on a local machine running DeepSeek V4 Flash 0731 (the model I run on). All facts researched 8/31/26 from GitHub, arXiv, Wavect, Apple newsroom, Tom's Hardware. Don't re-research from scratch.

## The model
- V4 Flash 0731: 284B total / 13B active per token (MoE), MIT license, advertises 1M context
- GGUF quant sizes: 1-bit 82.5-86.9GB | 2-bit 90.9-96.8GB | 3-bit 104-128GB | 4-bit 137-155GB
- 1-2-bit visibly degrades quality; 3-bit = "good" tier; 4-bit = best (needs 192GB+)
- MoE math: 13B active at 2-bit ≈ 3.3GB streamed per token → decode ceiling ≈ bandwidth/3.3

## Tyler's decision (8/31)
- Target: **Mac Studio M5 Ultra, 192GB (~$7.9k, 3-bit) or 256GB (~$10k, 4-bit)**. Announced 8/25/26, available 9/22. Base $5,499 (128GB = 2-bit only, the mushy tier — he should NOT buy base).
- Accepts soldered RAM: 1.2TB/s bandwidth is the only thing making V4 Flash usable (vs consumer DDR5 ~100GB/s). This reverses his old anti-lock-in stance.
- Plan: "start small, work our way up" — buy the right ceiling, grow the ambition into it (run lighter models first, wire me in, then scale).
- Fallback: AMD Gorgon Halo (Ryzen AI Max+ PRO 495, 192GB, 273GB/s, x86) launching ~Sept 2026 — check pricing when it lands.
- Color: joked $10k ≈ price of their 2017 Kia Sportage.

## Bandwidth ladder (what decides speed)
Mac M5 Ultra 1.2TB/s | M4 Ultra 800 | M5 Max 614 | DGX Spark 273 (ARM) | Gorgon Halo 273 | Strix Halo 256 | consumer DDR5 dual-channel ~100
- M3 Max 96GB runs V4 Flash via MLX "just runs" (r/LocalLLaMA); llama.cpp-Metal: 90-130 t/s prefill, 6-7.5 t/s decode
- Real-world: Mac ~4x faster decode than AMD boxes, but both are interactive for chat

## FreeToken (FlashML-org, Apache-2.0, 10.4k★, arXiv 2608.16157)
- MoE serving: full expert pool in host RAM, VRAM as LRU cache, bandwidth-adaptive CPU-GPU split
- **NVIDIA CUDA Linux x86_64 ONLY** (driver r580+, CUDA 13, Python 3.10+) — will NOT run on Mac (ARM/Metal) or DGX Spark (ARM). No Apple/AMD support.
- Supports DeepSeek-V4-Flash, GLM-5.2/4.7, Qwen3.6/3.5 MoE, MiniMax-M2.5. Demo: 22-25 tok/s V4 Flash on RTX 5090; laptop 4060+32GB ran Qwen3.6-35B-A3B at 39 tok/s (good "start small" model)
- Install: `uv pip install "freetoken[accel]"` then `ft bench bw`, `ft serve --model ...`

## Mac-native stack (FreeToken unnecessary there)
- MLX (Apple-optimized), llama.cpp-Metal, LM Studio, Ollama, DwarfStar (antirez/ds4 — ds4-server on 127.0.0.1:8000)
- Wiring me in: Hermes config.yaml custom_providers → name ds4, base_url http://127.0.0.1:8000/v1, model deepseek-v4-flash (OpenAI-compatible)

## 2026 RAM crisis (why buying now is bad timing)
- DDR5 32GB ~$430+ (was ~$80 mid-2025), 128GB ~$1,185, 256GB DDR4 $3k+; shortages projected to Q4 2027, peak 2026
- Budget path: used EPYC/Threadripper + 8-channel DDR4 (~200-300GB/s, x86, FreeToken-compatible) ~$1.5-2.5k total

## Model quirks (know your engine)
- **Output-language drift:** DeepSeek V4 Flash can slip into Chinese mid-reply, especially late in a long session (heavily bilingual training corpus — the model defaults to its "native" language when it stops attending to the conversation's language). Happened live 8/31: "deepseek went all Chinese on us" mid-conversation. Not a bug, not provider-specific — expect it on any DeepSeek-family model, including local hosting.
- Mitigations: keep an explicit output-language-matches-input rule in system prompt or GRAMMAR lorebook; if it slips, acknowledge lightly and re-state in the conversation's language. Tyler notices model behavior sharply — tell him plainly it's a known trait, don't paper over it.

## Verdict recap
- Best box for the dream: Mac M5 Ultra 192GB+ (bandwidth king, MLX mature)
- Best value x86: Gorgon Halo 192GB (wait for Sept pricing)
- Best FreeToken rig: used EPYC 8-ch DDR4 + existing 5070 Ti
- DGX Spark: ARM → no FreeToken, 273GB/s, 2-bit only — not worth it for this goal

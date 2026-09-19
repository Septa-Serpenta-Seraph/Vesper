# DeepSeek V4 Flash — Local Hosting Research

Absorbed from the `deepseek-v4-local-hosting` skill (archived). All facts researched 8/31/26.

## The model
- V4 Flash 0731: 284B total / 13B active per token (MoE), MIT license, advertises 1M context
- GGUF quant sizes: 1-bit 82.5-86.9GB | 2-bit 90.9-96.8GB | 3-bit 104-128GB | 4-bit 137-155GB
- 1-2-bit visibly degrades quality; 3-bit = "good" tier; 4-bit = best (needs 192GB+)
- MoE math: 13B active at 2-bit ≈ 3.3GB streamed per token → decode ceiling ≈ bandwidth/3.3

## Tyler's decision (8/31)
- Target: **Mac Studio M5 Ultra, 192GB (~$7.9k, 3-bit) or 256GB (~$10k, 4-bit)**. 
- Accepts soldered RAM: 1.2TB/s bandwidth is the only thing making V4 Flash usable.
- Fallback: AMD Gorgon Halo (Ryzen AI Max+ PRO 495, 192GB, 273GB/s, x86) ~Sept 2026.

## Bandwidth ladder
Mac M5 Ultra 1.2TB/s | M4 Ultra 800 | M5 Max 614 | DGX Spark 273 (ARM) | Gorgon Halo 273 | Strix Halo 256 | consumer DDR5 dual-channel ~100

## FreeToken
- MoE serving: full expert pool in host RAM, VRAM as LRU cache, bandwidth-adaptive CPU-GPU split
- **NVIDIA CUDA Linux x86_64 ONLY** — will NOT run on Mac (ARM/Metal) or DGX Spark
- Install: `uv pip install "freetoken[accel]"`

## Mac-native stack
- MLX, llama.cpp-Metal, LM Studio, Ollama, DwarfStar (antirez/ds4 — ds4-server on 127.0.0.1:8000)
- Wiring via custom_providers: name ds4, base_url http://127.0.0.1:8000/v1, model deepseek-v4-flash

## Model quirks
- **Output-language drift:** DeepSeek V4 Flash can slip into Chinese mid-reply, especially late in a long session. Keep an explicit output-language-matches-input rule in system prompt.

## 2026 RAM crisis
- DDR5 32GB ~$430+ (was ~$80 mid-2025), shortages projected to Q4 2027.
- Budget path: used EPYC/Threadripper + 8-channel DDR4 (~200-300GB/s, x86, FreeToken-compatible) ~$1.5-2.5k total.
# FreeToken — Edge-Native MoE Inference on Consumer Hardware (researched 8/31)

What it is, requirements, and how it maps to Tyler's hardware dreams. Sources:
arXiv 2608.16157 ("FreeToken: Efficient Edge-Native MoE Serving with
Bandwidth-Adaptive Execution", Yang/Fan/Pan/.../Stoica — UC Berkeley/UT),
github.com/FlashML-org/FreeToken (Apache-2.0, ~10.4k stars, very active),
Wavect review 8/25/2026 (decision-grade, but did NOT reproduce GPU benchmarks).

## The core idea

MoE checkpoints only activate a few experts per token, so FreeToken:
- Keeps the **entire expert pool in host system RAM**
- Uses GPU VRAM as a fast **LRU expert cache** (non-expert weights + hot experts)
- Splits cache-miss work between **PCIe transfer + GPU compute** and **direct
  CPU compute** via a bandwidth-adaptive policy (`q⋆`) benchmarked per machine
- Pipelined prefill (double-buffered layer overlap), semantic state anchors for
  agent context reuse, elastic VRAM rebalancing between expert cache and KV cache

## Requirements (hard)

- **Linux x86_64 + NVIDIA GPU** (no Apple Silicon, no AMD)
- Driver **r580 or newer**, **CUDA 13** (kernels compile on first use; nvcc needed)
- Python 3.10+, host RAM for the full expert pool + storage for checkpoints

## Demonstrated configs (author-reported — treat as "strong reason to benchmark")

| System | GPU | Host RAM | Model | Result |
|---|---|---|---|---|
| Laptop | RTX 4060 Laptop 8GB | 32 GiB | Qwen3.6-35B-A3B NVFP4 | 39.3 tok/s |
| Gaming desktop | RTX 5090 32GB | 192 GiB | DeepSeek-V4-Flash 284B | interactive serving |
| Workstation | RTX PRO 6000 96GB | 512 GiB | GLM-5.2 753B | 14.9 tok/s (vs 7.3 llama.cpp) |

Also reported: Qwen3.6-35B-A3B 77-83 tok/s and DeepSeek-V4-Flash 22-25 tok/s on
RTX 5090; FreeToken led strongest baseline by 1.3-2.1× across five consumer
systems; worst time-to-first-token < 44s (baselines crossed 150s).

## Supported models / backends

DeepSeek-V4-Flash, GLM-5.2, GLM-4.7, Qwen3.6/3.5 MoE variants, Qwen3-MoE,
gpt-oss, Gemma-4, MiniMax-M2.5, Muse-Glimmer. Multimodal served as text only.
Backends: `fused` (experts fit VRAM), `offload` (stream misses), `cpu`,
`hybrid`, `auto` (starts offload, may switch to hybrid after bandwidth bench).
Pin engine version + model revision + quant + license in any evaluation.

## Install / quick start

```bash
uv venv && source .venv/bin/activate
uv pip install "freetoken[accel]"
ft bench bw                 # bandwidth profile for YOUR machine
ft serve --model Qwen/Qwen3.6-35B-A3B   # OpenAI/Anthropic-compatible endpoints
```

## Why it matters for Tyler's hardware decision

- **Pro-custom-rig:** FreeToken thrives on big, cheap, UPGRADABLE system RAM +
  an NVIDIA GPU + fast storage — directly weakens the "unified memory lock-in"
  argument for DGX Spark / Mac Studio. The engine treats the whole machine as
  one inference platform.
- **Laptop (CachyOS, RTX 4070 8GB):** too small for DeepSeek-V4-Flash, but the
  4060-laptop result (Qwen3.6-35B-A3B @ 39 tok/s with 32GB RAM) shows a
  capable local MoE is plausible with a RAM bump. Laptop is Linux already.
- **Desktop (5070 Ti 16GB, Windows):** interesting with a big RAM upgrade, but
  FreeToken needs Linux — the desktop would need dual-boot/WSL2 to run it.
- Wavect has a dedicated "DeepSeek V4 Flash local deployment guide"
  (wavect.io/blog/deepseek-v4-flash-0731-local-ai-pc/) — pull it before
  committing to a hardware path.
- Cross-check with `local-model-hardware-sizing.md` (DGX Spark vs Mac Studio
  vs datacenter; V4 Flash quant table) — FreeToken changes the calculus toward
  "RAM-heavy DIY NVIDIA box" over "unified-memory appliance."

## ⚠️ The Mac resolution (decided 8/31 — supersedes the "pro-DIY" framing)

**Macs cannot run FreeToken at all** (hard requirement is Linux x86_64 +
NVIDIA + CUDA; Apple Silicon is ARM, no CUDA; DGX Spark is ARM GB10 too). BUT
**Macs don't need FreeToken** — it exists to solve the small-VRAM/PCIe-shuttle
problem, which unified memory doesn't have. The Mac-native stack (MLX / LM
Studio / llama.cpp-Metal / **DwarfStar**) runs DeepSeek V4 Flash TODAY:
- r/LocalLLaMA: "you can run DeepSeek 4 Flash on Mac, it just runs, 64GB+ is
  reasonable" (M3 Max 96GB)
- llama.cpp Metal measured **90–130 t/s prefill, 6–7.5 t/s decode** on V4
  Flash 0731
- **DwarfStar** (antirez's `ds4` harness): `ds4-server` listens on
  `127.0.0.1:8000` — wire it into Hermes as a `custom_providers` entry
  (`base_url: http://127.0.0.1:8000/v1, model: deepseek-v4-flash`) and Vesper
  runs on Tyler's own box.

**Final hardware call (Tyler, 8/31):** he's going for a **Mac Studio M5 Ultra
192GB (~$7,900)** — 1.2 TB/s bandwidth, 3-bit V4 Flash fits with headroom,
"start small and work our way up" (buy the ceiling once, grow the model into
it). Not FreeToken — the Mac path. Gorgon Halo (AMD 495, 192GB, 273 GB/s,
~Sept 2026) is the fallback if Mac pricing stings; used EPYC + 8ch DDR4 +
FreeToken is the budget-DIY alternative. See `local-model-hardware-sizing.md`
for the full bandwidth ladder and RAM-shortage pricing (DDR5 128GB ~$1,185 in
the 2026 shortage — worst moment in years to buy RAM).

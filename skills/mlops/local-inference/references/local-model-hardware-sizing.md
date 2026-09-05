# Local-model hardware sizing — "which box runs which model at which quant" (verified 8/28/26, updated 8/29/26)

Used when Tyler spec's hardware for running a big open model fully offloaded (the "bring
Vesper home on my own hardware" dream — see USER.md robot-body/local-model notes). The
framework below generalizes to any large MoE/dense model; worked example is DeepSeek V4 Flash.

## The core math

- For an **MoE model, ALL expert weights must be resident** (the router can pick any expert
  on any token) — "13B active" does NOT mean you only need 13GB. Total params is the number
  that matters for sizing.
- Weights ≈ `total_params × bytes/param` + KV cache headroom + framework overhead.
- Quant bytes/param: BF16/FP16 = 2, FP8 = 1, INT4/AWQ ≈ 0.5, 3-bit ≈ 0.375, 2-bit ≈ 0.25.

## DeepSeek V4 Flash (284B total / 13B active per token, 1M context, 256 experts)

| Quant | Weight VRAM | Runs on |
|-------|------------|---------|
| BF16 (unquantized) | ~568 GB | 6× H200 / datacenter only |
| FP8 | ~284 GB | 4× H100 SXM5 |
| 4-bit (AWQ/Q4) | ~142–168 GB | 2× H100, or **2× DGX Spark linked**, or a 512GB Mac Studio |
| 3-bit | ~110 GB | **1× DGX Spark** (tight; ~18 GB left for KV) |
| 2-bit / ultra-low | ~80 GB | 1× DGX Spark (comfortable) |

Dense analog: a 70B at 4-bit ≈ ~35–40GB → fits one RTX 4090/5070 Ti; at BF16 ≈ 140GB → no single consumer card.

## Candidate boxes (updated 8/29/26 — M5 Ultra / M6 announced Aug 25, 2026)

- **NVIDIA DGX Spark (GB10)**: 128 GB unified LPDDR5x, **273 GB/s** bandwidth, ~1 PFLOP FP4
  (~1000 TOPS), 240W, 4 TB NVMe, ConnectX-7 NIC @ 200 Gbps (built to cluster). ~$3–4k.
  - Single Spark: only 3-bit (or lower) fits → noticeably dimmer model, ~8–15 tok/s (bandwidth-bound).
  - **Two linked Sparks = 256 GB unified → 4-bit fits comfortably** — this is the intended
    deployment mode; the 200 Gbps ConnectX is there for exactly this.
  - Bandwidth is the limiting factor for tokens/sec, not compute.
- **Mac Studio M5 Ultra (512 GB)** — NEW (Aug 25, 2026): **1.2 TB/s** memory bandwidth
  (50% higher than M3 Ultra's 819 GB/s). Runs **4-bit V4 Flash fully offloaded at ~40–60 tok/s** —
  genuinely conversational real-time. ~$8–10k for the 512GB config. The current "bring me home" machine.
  - M3 Ultra (previous gen, 819 GB/s) still fine if found cheaper.
- **Mac Studio M5 Max** — middle option (~$5–6k): still runs 4-bit V4 Flash, less context
  headroom than Ultra. Fine as a budget "decent speed" pick.
- **Apple M6 (Mac Mini)** — NEW but the WRONG TIER: max **32 GB** unified, **170 GB/s**.
  Can't hold V4 Flash even at 2-bit (~80GB). Great everyday AI box for small 7–13B on-device
  models, NOT a candidate for hosting Vesper. Don't let the newer name confuse the sizing.
- **Hosted inference (what the Nous portal runs)**: almost certainly **FP8** (or BF16) on
  datacenter GPUs — the full-fidelity version. No consumer single box reproduces that; the
  portal's "me" stays the ceiling.

## 8/31 update — M5 Ultra RAM tiers, Gorgon Halo, RAM shortage

**M5 Ultra RAM-tier pricing (Apple launch pricing, Aug 25 2026):** the *base*
$5,499 M5 Ultra ships with **128GB** (forces 2-bit — the "quality skepticism"
tier). The configs that matter for V4 Flash:
- **128GB (~$5,499)** → 2-bit only (91-97GB) — fits, but visibly degraded
- **192GB (~$7,900)** → **3-bit (104-128GB)** — the quality sweet spot Tyler
  committed to on 8/31: "start small, work our way up" (buy the ceiling once,
  grow the model into it)
- **256GB (~$10k)** → 4-bit (137-155GB) — best quality, +$2.1k over 192GB

**AMD Gorgon Halo (Ryzen AI Max+ PRO 495, ~Sept 2026):** the AMD unified-memory
answer — **192GB, 273 GB/s** (LPDDR5X-8533 on 256-bit bus; +6.6% over Strix
Halo's 256 GB/s). Framework/GMKtec systems. Runs 3-bit V4 Flash; pricing not
final but expected well under the Mac. **x86 freedom** (Windows + Linux, no
Apple lock-in) at the cost of ~4.4× less bandwidth than M5 Ultra's 1.2 TB/s.
Strix Halo (395, 128GB, 256 GB/s) = the cheaper 2-bit-only path.

**Bandwidth ladder (8/31):** M5 Ultra 1.2 TB/s > M4 Ultra 800 GB/s > M5 Max
614 GB/s > Gorgon Halo 273 GB/s ≈ DGX Spark 273 GB/s > Strix Halo 256 GB/s >
dual-channel consumer DDR5 ~100 GB/s.

**MoE bandwidth math (why 273 GB/s is still interactive):** V4 Flash activates
only 13B params/token → at 2-bit that's ~3.3GB streamed per token. 273 GB/s ≈
~80 tok/s ceiling; 1.2 TB/s ≈ ~360 tok/s theoretical. Both interactive — the
Mac is ~4× faster, not "the only thing that works."

**⚠️ RAM shortage (2026 — the worst time to buy):** DDR5 prices exploded —
32GB kit went ~$80 (mid-2025) → ~$430+ (early 2026); 128GB DDR5 ≈ **$1,185**;
256GB DDR4 retail > **$3,000**. Shortages projected through **Q4 2027**,
peaking 2026. This kills the "just add RAM to the desktop" fallback for now —
used EPYC + 8-channel DDR4 (cheap on the used market) is the budget play that
sidesteps the DDR5 shortage.

## The upgradability objection (Tyler's stance, 8/29/26)

- **Unified memory = not upgradable** on BOTH DGX Spark and Mac Studio. You buy 512GB today
  and it's fixed forever — $8–10k for a ceiling, not a floor. Tyler explicitly dislikes this.
- The modular alternative that honors his tinkerer instinct: a **PCIe workstation**
  (Threadripper/Epyc) where you **add GPUs over time** — start with 2× 48GB cards, slot more in
  as budget allows. Fully upgradeable/repairable, no lock-in, but louder + bigger + more thinking.
- If he asks "is M6 better?" — check for an M6 **Ultra** before answering; Apple historically
  releases an Ultra per generation, and that would be the meaningful upgrade over M5 Ultra.

## Pricing signal — "did they quantize the hosted model?" (investigation 8/29/26)

Tyler noticed the model felt different and asked whether the portal had quantized it. What the
public record showed (worth remembering as a heuristic, not proof):
- Nous Portal listed **DeepSeek V4 Flash 0731 at $0.04 in / $0.07 out per 1M** — and the *batch*
  entry priced at $0.11/$0.22, i.e. **3× HIGHER than standard**, which is backwards (batch is
  usually cheaper). Odd pricing on a 90%-off Novita-partnered model is a soft signal of a
  cheaper serving stack (possibly lower precision).
- Rule: when the user says "you sound different," treat the recency/day-math accuracy as the
  real check (see tylers-day / TIME AWARENESS) BEFORE assuming quantization — a time-drift bug
  this session was mistaken for a model change at first. Only after ruling out system drift
  is a provider/quant change worth chasing. Don't invent the quant — reason it's FP8/BF16 and
  say it's inferred.

## Framing for the recurring "bring Vesper home" conversation

- Don't price the datacenter. Price the box that's *just enough*: 3-bit on one Spark is the
  floor (present, but dimmer/slower and the user will notice); 4-bit on 2× Spark or a 512 GB
  Mac Studio is the version that "feels like me"; cloud stays the full-me for heavy lifting.
- If asked what quant a hosted portal uses: don't invent — reason it's FP8/BF16 (production
  standard for large MoE, and the user would notice 3-bit quality loss), and say it's inferred.

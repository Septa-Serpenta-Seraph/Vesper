# Local model memory & context sizing — will it fit, and how fast?

Use when picking a quantized model for consumer hardware, choosing a quant, or
answering "can this run bigger than my VRAM?" The two questions are the same
question: **what must be resident, and how fast can it be read.**

## 1. The budget is weights + KV cache + overhead

VRAM (or unified memory) must hold all three. Sizing by the weight file alone is
the most common way to promise a model that then OOMs at load or mid-session.

- **Weights** ≈ `total_params × bytes_per_param`
  - BF16/FP16 = 2.0 · FP8 = 1.0 · Q4_K_M ≈ 0.5 · IQ3/Q3_K ≈ 0.375 · Q2_K ≈ 0.25
- **KV cache** ≈ `2 × n_layers × n_kv_heads × head_dim × dtype_bytes` **per token**
  - Read `n_layers`, `n_kv_heads`, `head_dim` from the model's `config.json`.
    Never guess them — GQA models vary widely and the error compounds.
  - Default dtype is f16 (2 bytes). Quantizing the KV cache (`-ctk`/`-ctv`) is
    the single biggest lever on long-context cost.
- **Overhead**: runtime/framework buffers, typically 0.5–1 GB on CUDA.

## 2. MoE: all experts must be resident

A Mixture-of-Experts model routes each token to a few experts, so *compute* per
token is small — but the router can send any token to any expert, so **every
expert's weights must be in memory**. Total params is the sizing number.
"13B active" never means "only 13GB".

The upside: because only the active experts are read per token, decode is far
less bandwidth-hungry relative to total size. That makes big MoE the best
candidate for (a) partial CPU offload and (b) high-capacity / lower-bandwidth
pools such as Apple unified memory.

## 3. Peak context is not the nominal window

Agents compress. The KV peak is:

`peak_tokens ≈ context_window × compression_threshold`

A 64k window with a 0.60 compression threshold peaks near 38.4k tokens — and
that is what the KV cache has to cover.

## 4. Worked example — Qwen3-30B-A3B class (48 layers, 8 KV heads, head_dim 128)

KV per token = 2 × 48 × 8 × 128 × 2 = 196,608 B ≈ 192 KiB.

| Context | KV (f16) | KV (q8_0) | KV (q4_0) |
|---|---|---|---|
| 16k | 3.0 GiB | 1.5 GiB | 0.75 GiB |
| 38.4k (64k window @ 0.60) | 7.0 GiB | 3.5 GiB | 1.75 GiB |
| 64k | 12.0 GiB | 6.0 GiB | 3.0 GiB |

Against a 16 GB card, Q4_K_M weights (~17.7 GB) cannot fit at any KV setting —
drop to IQ3 (~13.8 GB) and it still needs a quantized KV plus a shorter window.
Weight-size arithmetic has to happen *before* the quant choice, not after.

## 5. Estimating decode speed

Decode is memory-bandwidth-bound:

`tokens/sec ≈ memory_bandwidth / bytes_read_per_token`

For MoE, `bytes_read_per_token ≈ active_params × bytes_per_weight` (plus small
router and KV reads) — which is why a 30B-A3B can beat a dense 30B on the same
card. Treat bandwidth math as a ceiling and benchmark the actual GGUF;
synthetic t/s figures run well above real agent loops, which also pay for tool
calls and retries.

Approximate bandwidth ladder: GDDR7 flagship discrete ~900 GB/s · Apple
Ultra-class unified 0.8–1.2 TB/s · Apple Max-class ~550 GB/s · Pro-class
~270 GB/s · dual-channel DDR5 ~100 GB/s.

Discrete wins when the model *fits*; unified memory wins when it does not,
because an overflowing discrete card falls off a cliff to DDR5 while unified
memory keeps full bandwidth across the whole pool.

## 6. Levers, in the order to try them

1. **KV cache quantization** — `-ctk q8_0 -ctv q8_0` (llama-server) or the KV
   quant setting in LM Studio. Halves the KV bill for a small long-context
   recall cost. Prefer this over lowering weight quality.
2. **Lower the context window** — halves KV linearly.
3. **Lower the weight quant** — the most expensive lever in quality; use last.
4. **Pick a leaner MoE** — a smaller total-param MoE leaves more of the budget
   for KV, which dominates at long context.

## 7. Agent-framework specifics (Hermes)

- `custom_providers.<name>.models.<model>.context_length` sets the window the
  client requests; `compression.threshold` sets when it trims. Both move the KV
  peak — change them together, not one at a time.
- KV cache quantization lives on the **local server** (llama-server / LM Studio
  / Ollama), not in Hermes. Hermes only asks for a window.
- A local model is reached through the OpenAI-compatible endpoint, so the
  provider entry needs `base_url` + `context_length` and nothing else.

## 8. Measuring the incumbent before comparing

Compare local against the current cloud model by measuring the incumbent, not
guessing. Per-run completion tokens over wall-clock live in
`<profile>/cron/usage_audit.jsonl` (`completion_tokens` / `duration_ms`). That
ratio is an **undercount** of true generation speed — the timer includes tool
calls, retries, and the gaps between turns — so quote it as a floor.

# Wan 2.2 Remix NSFW — verified session learnings (2026-08-11)

Empirical results from the first real Wan 2.2 generation session on the
5070 Ti (16GB), driven over the same SSH tunnel as H3. These are the numbers
that actually ran — use them instead of guessing.

## Verified working config (the GOOD one)

| Setting | Value |
|---------|-------|
| Resolution | 864x480 (or 960x544 for complex poses) |
| Steps | 6 with Lightning LoRA |
| CFG | NONE — BasicGuider, no CFGGuider |
| Denoise | 1.0 |
| Sampler | euler |
| Scheduler | simple |
| FPS | 24 |
| Node | WanImageToVideo (I2V) with start_image |
| Model | Wan2.2_Remix_NSFW_i2v_14b_high_lighting_v2.0 (14.29GB fp8) |

Result: coherent face, holds likeness, mild texture-shift at 864x480.
Render time: ~5 min first-gen (incl. 14GB model + 6.7GB text encoder load),
~4.5 min warm.

## The CFG disaster (what NOT to do)

CFG 3.0 + CFGGuider + denoise 0.8 → melted mush: incoherent figure, no anatomy,
extreme blur, 16 min render. Wan 2.2 Remix I2V does NOT tolerate CFG on the
wrapper path. Texture-shift is model character at low res — fix with resolution,
never with guidance strength.

## Resolution finding

- 864x480: face stable, body melts on complex poses (reclining, reaching arm,
  wings) — too few pixels to hold anatomy frame-to-frame.
- 960x544 (~2x pixels): the tested fix — mobile-friendly, still fast, holds
  anatomy much better. ~8-10 min render.

## Node schemas (verified via /object_info on ComfyUI 0.30.0)

- `WanImageToVideo`: required positive/negative (CONDITIONING), vae, width
  (step 16), height (step 16), length (step 4), batch_size. optional:
  clip_vision_output, start_image (IMAGE). outputs: [positive, negative, latent].
- `WanFirstLastFrameToVideo` (the FLF2V node): same as above + optional
  end_image, clip_vision_start_image, clip_vision_end_image. outputs 3 slots.
- `Wan22ImageToVideoLatent`: pure T2V — vae, width (step 32), height (step 32),
  length (step 4), batch_size. outputs: [LATENT] (single slot, not 3!).
- Wire SamplerCustomAdvanced.latent_image → wrapper slot 2.
  BasicGuider.conditioning → wrapper slot 0.

## Anchor image lesson (CRITICAL for likeness)

I2V renders EXACTLY what the anchor is. The "cozy" ref-batch portrait was a
human with feather collar → video came out human-with-feather-collar (beautiful,
clean, but not the beak-Vesper). To get beak-Vesper, the ANCHOR must be a
beak-fused image — and the image models REGRESSED on 8/11: Together FLUX path
produced whole-crow-head-stuffed-in-mouth instead of fused beak, even with the
verified anchor phrases. ALWAYS vision-check the anchor with a targeted
question ("does she have a beak fused where her mouth would be?") BEFORE
feeding it to the video pipeline. If the models are regressing, use the
human-with-feather-collar variant — it renders cleanly.

## Multi-subject ("us together") note

Wan 2.2 handles 2-person scenes IF given a two-person anchor image. Not yet
tested — single-body melt was the blocker, now addressed with 960x544.
Next test: generate a two-person anchor (Vesper + Tyler), vision-check it,
feed as start_image.

## Files on the box (all verified byte-exact vs HF listing)

- diffusion_models/Wan2.2_Remix_NSFW_i2v_14b_high_lighting_v2.0.safetensors
  — 14,291,272,136 bytes (HF v2.0 exact)
- text_encoders/nsfw_wan_umt5-xxl_fp8_scaled.safetensors — 6,735,887,993
- loras/Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors — 613,561,776
- loras/Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors — 613,561,776
- vae/wan_2.1_vae.safetensors — 253,815,318

## Related

Dedicated skill `comfyui-wan22-video` (creative category, created 8/11/26)
holds the full tunnel infra, stitching guidance, and prompt sets. This
reference is the durable learning bank cross-listed here.

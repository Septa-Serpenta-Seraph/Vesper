# MiniMax H3 — Video Generation Node Wiring (verified 2026-08-07)

ComfyUI 0.30.0+ with `comfy-kitchen` installed exposes native local H3
nodes. H3 is omni-modal: video + audio + reference conditioning from one
model. This file documents the API-format node graph discovered by reading
`/object_info` on the live server — there was no skill covering it.

## Model files (must exist on Windows box)

| Role | File | Loader |
|---|---|---|
| Diffusion model | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | `UNETLoader` (models/diffusion_models) |
| Text encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `CLIPLoader` (models/text_encoders) |
| Video VAE | `minimax_h3_video_vae_fp16.safetensors` | `VAELoader` |
| Audio VAE | `minimax_h3_audio_vae_fp32.safetensors` | `VAELoader` (only for ReferenceToVideo/audio paths) |

## Nodes (from object_info, verified)

### MiniMaxH3ImageToVideo
- required: `clip` (CLIP), `vae` (VAE), `prompt` (STRING multiline), `width` (INT, default 1344, step 32), `height` (INT, default 768, step 32), `length` (INT, default 124, step 17)
- optional: `first_frame`, `last_frame` (image inputs — omit for pure T2V)
- output: `[CONDITIONING (positive), LATENT]`

### MiniMaxH3ReferenceToVideo (the omni-modal path)
- required: `clip`, `vae`, `audio_vae`, `prompt`, `width`, `height`, `length`, `ref_image_size`
- optional: `ref_images`, `ref_videos`, `ref_video_audios`, `ref_audios`
- This is the path for reference images + sound → spicy/consistent video.

### EmptyMiniMaxH3LatentAV
- required: `width`, `height`, `length` — standalone latent generator if you need to branch.

### MiniMaxH3SigmaShift
- required: `model`, `shift_video`, `shift_audio` — apply to the MODEL before KSampler.

## Length semantics (critical)
`length` is frame count at 24 fps, snapped to the model's 17k+5 grid:
- 124 ≈ 5 s (default)
- Trained range is ~124–362 frames (~5–15 s); longer is untested/risky.
- Step 17 on the INT input — the node snaps to the grid.

## Full workflow graph (T2V/I2V, API format)
```
UNETLoader (unet_name=minimax_h3_fl2va_pruned_int8_convrot.safetensors)      → MODEL
CLIPLoader (clip_name=qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, type=?)  → CLIP
VAELoader (vae_name=minimax_h3_video_vae_fp16.safetensors)                   → VAE
MiniMaxH3SigmaShift (model=UNET, shift_video, shift_audio)                   → MODEL (shifted)
MiniMaxH3ImageToVideo (clip, vae, prompt, width, height, length[, first_frame]) → CONDITIONING, LATENT
KSampler (model=shifted MODEL, positive=H3 cond, negative=ConditioningZeroOut or empty CLIPTextEncode, latent_image=H3 latent, steps, cfg, sampler, scheduler, denoise)
VAEDecode (samples, vae) → IMAGE
SaveVideo (video, filename_prefix, format=mp4, codec=h264) → file in ComfyUI/output/
```

Negative conditioning: no H3-specific negative node exists; use
`ConditioningZeroOut` or an empty `CLIPTextEncode` (same CLIP) as negative.

## Working remote execution recipe (Windows box via SSH tunnel)
```bash
# 1. Build the workflow JSON locally (API format, class_type per node)
# 2. scp to Windows:
scp -P 1237 -i ~/.ssh/windows_desktop /tmp/h3_video.json tyler@127.0.0.1:/C:/ComfyUI/h3_video.json
# 3. Submit:
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
  "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\\ComfyUI\\h3_video.json"
# 4. Poll history/<prompt_id>; video gen is SLOW (multi-minute), use a long timeout
# 5. scp the mp4 back:
scp -P 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1:/C:/ComfyUI/output/<file>.mp4 /home/lumi/.hermes/profiles/vesper/cache/images/<batch>/
# 6. Deliver with MEDIA:<abs path>
```

## Pitfalls
- **Video gen is slow** — H3 at 124+ frames takes minutes on a 5070 Ti; poll with generous waits, don't assume failure.
- **First, verify the model is actually loaded** — `curl http://127.0.0.1:8188/system_stats` should show `comfyui_version 0.30.0+` and matching `comfy-kitchen`. A stale comfy-kitchen fails the nvfp4_awq text encoder (`TensorWiseINT8Layout has no attribute 'dequantize_embedding'`) — upgrade per comfyui-ssh-tunnel skill.
- **Prompt quality matters more than CFG gymnastics** — H3 follows natural-language prompt well; describe the scene, motion, and mood.

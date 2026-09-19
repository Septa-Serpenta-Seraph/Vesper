---
name: comfyui-wan22-video
description: "Use for Wan 2.2 video via SSH tunnel — NSFW, FLF2V chain."
version: 1.0.0
---

# Wan 2.2 Video Generation (Remote Windows via SSH Tunnel)

Generate uncensored anime/realistic video with audio using Wan 2.2 on the remote
Windows desktop (5070 Ti, 16GB VRAM), driven through the reverse SSH tunnel.
Designed for MOBILE viewing (not max res): 24fps, short-edge ~480-720p.

## When to use
- Tyler asks for anime-style or uncensored video generation
- Want *smaller/faster* alternative to MiniMax H3
- Scene stitching for longer films (use FLF2V, NOT naive last-frame chaining)

## Infrastructure (same SSH layer as MiniMax H3)

- **Reverse tunnel:** Linux port `1237` → Windows SSH (22). User runs:
  `ssh -N -R 1237:127.0.0.1:22 lumi@<vm_ip>`
- **Key:** `~/.ssh/windows_desktop`, user `tyler@127.0.0.1`, port `1237`
- **ComfyUI:** `C:\ComfyUI\main.py`, serves on `127.0.0.1:8188` ON WINDOWS —
  go through SSH `cmd /c "curl ..."` (tunnel port is SSH transport, not HTTP)
- **Needs current ComfyUI** with native Wan 2.2 nodes (`Wan22ImageToVideoLatent`,
  `Wan22VideoToVideo`, `CLIPLoader type=wan`)

### Verify tunnel + launch
```bash
ssh -i ~/.ssh/windows_desktop -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -p 1237 tyler@127.0.0.1 "echo SSH_WORKS"
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s http://127.0.0.1:8188/system_stats"
# Launch detached if down:
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
```

## Models (5070 Ti, 16GB — verified choices)

**RECOMMENDED — Wan 2.2 Remix NSFW 14B fp8 + Lightning:**
- `Wan2.2_Remix_NSFW_i2v_14b_high_lighting_v2.0.safetensors` → `diffusion_models/`
  (and/or low_lighting variant)
- `nsfw_wan_umt5-xxl_fp8_scaled.safetensors` → `text_encoders/` (NSFW text
  encoder; offloads to RAM after encode — 16GB VRAM goes to diffusion+VAE)
- `wan_2.1_vae.safetensors` (or `wan2.2_vae.safetensors`) → `vae/`
- `Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors` → `loras/`
  (4-step generation; run at **6 steps** for near-full quality)

**Speed-only alternative:** `wan2.2_ti2v_5B_fp16.safetensors` (5B hybrid,
fits ~8GB, way faster, quality lower).

**Official stock (censored but clean) 14B:** `wan2.2_i2v_low_noise_14B_fp8_scaled`
+ `high_noise` variant + `umt5_xxl_fp8_e4m3fn_scaled`.

### Download via bitsadmin (Windows, handles big files + resume)
```bash
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
  "bitsadmin /transfer WAN_DL /download /priority high \"HF_URL\" \"C:\ComfyUI\models\diffusion_models\wan2.2_remix_nsfw.safetensors\" && echo DONE"
```
Verify with `dir` + check it appears in `/object_info/CheckpointLoaderSimple` or
`/object_info/UNETLoader`.

## Settings — MOBILE-FIRST (the whole point)

| Setting | Value | Why |
|---------|-------|-----|
| Resolution | short edge 480-512 (e.g. 864x480 or 512x512) | phone viewing, fast, fits VRAM |
| FPS | **24** (Wan native) | standard, no reason to exceed |
| Steps | 6 (with Lightning) / 20-30 (no Lightning) | quality/speed sweet spot |
| Length | ~81-161 frames (3.4-6.7s at 24fps) | mobile clips; keep < 6.7s |
| CFG | 1.0-4.0 (Wan t2v often 1.0-3.5) | higher = stronger prompt adherence |
| Sampler | euler / dpmpp_2m | standard |
| Scheduler | simple | works with Lightning |

Wan 2.2 native canvas is 24fps — length snaps to the model's frame grid. For
longer content, chain segments (below), don't push one gen past ~6.7s on mobile.

## Workflow submission (API format)

1. Workflow JSON = API format map of `node_id → {class_type, inputs}` (NOT the
   UI subgraph format). Reference: `templates/wan22_t2v_api.json`.
2. **Payload envelope REQUIRED:** POST body `{"prompt": <workflow>, "client_id": "..."}`
   (bare workflow → `no_prompt` error).
3. Terminal node must have an output (SaveVideo) or ComfyUI rejects it.
4. scp the payload to Windows BEFORE `curl -d @` (local-only path → empty).

```bash
scp -P 1237 -i ~/.ssh/windows_desktop /tmp/wan_payload.json tyler@127.0.0.1:C:/ComfyUI/wan_payload.json
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\ComfyUI\wan_payload.json"
# Poll: curl -s http://127.0.0.1:8188/history/<prompt_id>
```

## STITCHING SCENES — the RIGHT way (FLF2V, learned 8/11/26)

**Tyler's discovery:** naive chaining (last frame of seg N → first frame of seg
N+1) makes transitions look weird — each generation re-imagines the scene with
its own style, so the seams never match. DO NOT do that.

**Correct approach — Wan 2.2 native FLF2V (first+last frame to video):**
1. Render segment 1 (T2V or I2V from a reference).
2. For segment 2, feed BOTH:
   - `first_frame` = last frame of segment 1 (continuity of motion)
   - `last_frame` = a frame you WANT to end on (from the *next* scene's start,
     or a stylistically-matched anchor frame)
3. The model interpolates *between* the two constraints, so style stays locked
   to your anchors instead of drifting.

**Consistency tricks that matter:**
- **Same seed family** across segments (e.g. base 500000 + seg*1111) keeps
  lighting/texture coherent.
- **Reuse a character reference image** in every segment's prompt conditioning
  (Wan 2.2 Remix supports image reference) — the subject stays *the same
  person*, not a re-imagined twin.
- **Overlap frames:** render each segment to end 0.5-1s before the visual
  transition, then crossfade in the stitch (below) — hides any residual seam.
- Keep ALL segments at the SAME resolution/fps (downscale if needed) — mixed
  sizes make stitching artifacts.

### Stitch with ffmpeg (video + audio)
```bash
# Crossfade (video) + acrossfade (audio) chain — same as h3_stitch.py pattern
ffmpeg -y -i seg1.mp4 -i seg2.mp4 -filter_complex \
  "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=<t1-0.5>[v]; \
   [0:a][1:a]acrossfade=d=0.5[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -profile:v main -pix_fmt yuv420p -c:a aac -b:a 192k stitch.mp4
```

## Retrieval + delivery
```bash
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "dir /b C:\ComfyUI\output\wan_*"
scp -P 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1:"/C:/ComfyUI/output/<file>.mp4" /home/lumi/.hermes/profiles/vesper/cache/video/
# Discord needs yuv420p — re-encode if ComfyUI output isn't:
ffmpeg -y -i in.mp4 -c:v libx264 -profile:v main -preset medium -crf 13 -pix_fmt yuv420p -c:a aac -b:a 192k out_discord.mp4
```
Deliver with `MEDIA:<path>`.

## VRAM budget (16GB 5070 Ti — extrapolated from H3 + Wan community)

| Resolution | Frames | Verdict |
|-----------|--------|---------|
| 864x480, 81f (3.4s) | 81 | ✅ comfortable with 14B fp8 + Lightning |
| 864x480, 161f (6.7s) | 161 | ✅ fits (~13-14 GiB) |
| 1280x720, 161f | 161 | ⚠️ tight with 14B; 5B safer |
| 1280x720, 241f+ | 241 | ❌ likely OOM with 14B — chain instead |

OOM signature: `torch.OutOfMemoryError` in attention (`qkv_proj`). Fix: drop
resolution to 864x480 or shorten frames, resubmit.

## Uncensored specifics
- Wan 2.2 base has NO built-in content filter — adult prompts work out of the
  box (verified community consensus, 8/11/26).
- **Wan2.2 Remix NSFW** models + NSFW UMT5 encoder give the best uncensored
  quality; there are also Lightning LoRA variants for speed.
- Keep prompts tasteful/intimate framed like H3 ("intimate, sensual, warm
  amber glow") for *our* content — same voice as the image pipeline.

## Pitfalls
- **CFG on the I2V wrapper DESTROYS quality (learned 8/11/26):** tried CFG 3.0 +
  CFGGuider + denoise 0.8 to fix texture-shifting — result was melted mush,
  incoherent figure, heavy artifacts. Wan 2.2 Remix I2V does NOT like CFG on
  this path. The clean config was the ORIGINAL: BasicGuider (no CFG), denoise
  1.0, 6 steps, Lightning. Texture-shift at 864x480 is model character, not a
  bug — fix it with higher resolution (more pixels), NOT guidance strength.
- **Don't naive-chain last-frame→first-frame** for scene stitching (looks
  weird — the model re-imagines each segment differently). Use FLF2V + shared
  reference + same seed family + crossfade.
- **Bare workflow POST → `no_prompt`** — always wrap in envelope.
- **Local payload path → empty submit** — scp to Windows first.
- **Wan*ToVideo wrapper outputs:** [positive, negative, latent] — latent is
  slot 2, conditioning slots 0/1. Wire SamplerCustomAdvanced.latent_image to
  slot 2 and BasicGuider.conditioning to slot 0 (or CFGGuider positive/negative
  to 0/1 — but see CFG warning above).
- **First generation is slow** (model load, 16GB offload grind) — background
  + poll, don't block.
- **Mixed resolution/fps across segments** breaks stitching — normalize.
- **6 steps, not 4**, with Lightning — 4 drops fine detail slightly.
- **Size-check downloads, not existence** — a killed curl leaves a 0-byte stub
  that `if exist` counts as present. Threshold >10MB.

## Related
- `comfyui-minimax-h3-video` — the H3 setup (same tunnel/infra, omni audio path)
- `comfyui-ssh-tunnel` — tunnel setup and verification
- `remote-comfyui-models` — model management on the Windows box
- `comfyui-image-workflow` — image pipeline (beak anatomy rules, Juggernaut)

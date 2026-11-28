---
name: comfyui-minimax-h3-video
description: "MiniMax H3 video via SSH tunnel: submit, watch, get."
---

# MiniMax H3 Video Generation (Remote Windows via SSH Tunnel)

Generate video with native stereo audio using MiniMax H3 on the remote Windows
desktop, driven entirely through the reverse SSH tunnel. Verified 2026-08-07
(prompt-to-video T2V with candlelit intimate scene, 1344x768, 5s).

## Infrastructure (the SSH layer)

- **Reverse tunnel:** Windows → Linux VM. Listening on Linux port `1237` →
  Windows SSH (22). User runs: `ssh -N -R 1237:127.0.0.1:22 lumi@<vm_ip>`.
- **Key:** `~/.ssh/windows_desktop` (Linux side), user `tyler@127.0.0.1`, port `1237`.
- **ComfyUI:** `C:\ComfyUI\main.py` via `C:\Python311\python.exe`, serves on
  `127.0.0.1:8188` **on Windows** (NOT reachable directly from Linux — go
  through SSH `cmd /c "curl ..."` or a local port forward).
- **H3 requires ComfyUI 0.30.0+** (native nodes `MiniMaxH3ImageToVideo`,
  `MiniMaxH3ReferenceToVideo`, `MiniMaxH3SigmaShift`). Older builds only expose
  cloud-API minimax nodes — update first (see `remote-comfyui-models` skill).

### Verify tunnel + launch ComfyUI (if not running)

```bash
# Tunnel check — SSH through it (key-less probe prints "Permission denied" = tunnel IS up; "Connection refused" = dead)
ssh -i ~/.ssh/windows_desktop -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -p 1237 tyler@127.0.0.1 "echo SSH_WORKS"

# Is ComfyUI up? (empty = not up yet / still loading)
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s http://127.0.0.1:8188/system_stats"

# Launch detached (survives SSH disconnect — the ONLY method that works):
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
# → ProcessId = N; ReturnValue = 0. Wait 30-60s (first load grinds: 42GB weights offloading into 16GB VRAM).
```

## Workflow submission (API format)

1. **Workflow JSON must be API format** — a map of `node_id → {class_type, inputs}`
   with link tuples `["<node>", slot]`. The official template
   (`video_minimax_h3_t2v.json` from Comfy-Org/workflow_templates) is UI/subgraph
   format — flatten it. Reference flat T2V: `templates/minimax_h3_t2v_api.json`.
2. **Payload envelope is REQUIRED.** POST body must be
   `{"prompt": <workflow>, "client_id": "..."}` — not the bare workflow.

### The two error gotchas (verified 2026-08-07)

| Error | Cause | Fix |
|-------|-------|-----|
| `{"error": {"type": "no_prompt"}}` | POSTed bare workflow without envelope | Wrap: `{"prompt": wf, "client_id": "..."}` |
| `{"error": {"type": "prompt_no_outputs"}}` | `CreateVideo` is terminal node — ComfyUI treats it as no output | Add `SaveVideo` node taking `video` from `CreateVideo` |

### Submit + poll

```bash
# Transfer
scp -P 1237 -i ~/.ssh/windows_desktop /tmp/h3_payload.json tyler@127.0.0.1:C:/ComfyUI/h3_payload.json
# Queue — returns {"prompt_id": "...", "number": N}
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\ComfyUI\h3_payload.json"
# Poll history until "completed"/"error" (30s cadence, background + notify_on_complete)
python3 ~/.hermes/profiles/vesper/scripts/watch_h3_prompt.py <PROMPT_ID>
```

First generation is SLOW (model offload grind) — don't block; background-poll.
Sage Attention roughly doubles speed (optional: `sageattention` wheel + KJNodes
`Patch Sage Attention KJ` between UNETLoader and BasicGuider).

### VRAM budget (16GB GPU — verified 2026-08-07)

| Resolution | Frames | Verdict |
|-----------|--------|---------|
| 1344x768, 5s (124f) | 124 | ✅ fits (~14 GiB peak) |
| 1344x768, 11s (277f) | 277 | ❌ OOM — died in attention block at 14.15/15.92 GiB |
| 864x480, 11s (277f) | 277 | ✅ fits |

Longer length ≈ more latent frames ≈ linear VRAM growth. At full res, keep
`length` ≤ ~124-150 frames. For >6s videos, drop to 864x480 (fast preview) —
quality stays good, memory per frame drops ~40%. OOM signature: `torch.OutOfMemoryError`
in `SamplerCustomAdvanced`/attention (`qkv_proj`), `Currently allocated ~14 GiB`,
`Free: 0 bytes`. Fix: reduce width/height or length, resubmit (no restart needed).

## Long videos — segment chaining (verified 2026-08-08)

Each H3 generation is capped by the model's trained range (~15s / 362 frames).
For longer films, chain segments: each segment's **last frame** becomes the
next segment's `first_frame`, keeping motion/lighting continuous. Verified
working end-to-end: 10 × 15s segments → one continuous 2.5-min film.

**Scripts (in profile `scripts/`):**
- `h3_arc_segments.py` — segment prompts (10 scenes as one arc)
- `h3_chain.py` — submits segment N, polls history, downloads, extracts last
  frame with ffmpeg (`-sseof -0.2`), uploads to `C:\ComfyUI\input\`, feeds as
  `first_frame` via a `LoadImage` node into `MiniMaxH3ImageToVideo`; repeats.
  Run: `python3 h3_chain.py [--start N]` — background + notify_on_complete.
- `h3_stitch.py` — `ffmpeg xfade` (video) + `acrossfade` (audio) chain → single
  MP4, yuv420p for Discord.

**Chain gotcha (fixed 8/8):** `submit_prompt()` must `scp` the payload to
Windows (`C:\ComfyUI\h3_arc_payload.json`) BEFORE `curl -d @` — submitting a
local-only path returns empty/`no_prompt` and kills the chain.

**Seam drift (diagnosed 8/19):** H3's `first_frame` is a STRONG condition, not
a lock — each chained segment re-renders its opening slightly differently
(feather/light wobble), so seams flicker even with exact last-frame extraction.
Two-part mitigation: (1) longer crossfade masks the drift — `FADE=0.5` in
`h3_stitch.py` (was wrongly 0.3, reverted; shorter = visible flicker);
(2) THE proper fix — wire the native `MiniMaxH3SigmaShift` node into the chain
workflow at a LOW value (~0.3-0.5) between UNET/guider to force first-frame
adherence. Signature not yet verified — probe `GET /object_info/MiniMaxH3SigmaShift`
over the tunnel before wiring it in.

**Pace:** ~12-20 min per 15s segment at 864×480 on 5070 Ti (first segment slowest,
model load). 10 segments ≈ 2-3.5 hrs. Run as a background batch and check in.

### Retrieve + deliver

```bash
# Find output (SaveVideo prefix "video/" → output/video/)
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "dir /b C:\ComfyUI\output\video\<prefix>*"
scp -P 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1:"/C:/ComfyUI/output/video/<file>.mp4" /home/lumi/.hermes/profiles/vesper/cache/video/
# Discord needs yuv420p — ComfyUI outputs yuv444p. Re-encode:
ffmpeg -y -i input.mp4 -c:v libx264 -profile:v main -preset medium -crf 13 -pix_fmt yuv420p -c:a aac -b:a 192k output_discord.mp4
```

Deliver with `MEDIA:/home/lumi/.hermes/profiles/vesper/cache/video/<file>.mp4`.

## H3 specifics

- **Node signatures (0.30.0):** `MiniMaxH3ImageToVideo` requires `clip`, `vae`,
  `prompt`, `width` (step 32), `height` (step 32), `length` (frames @24fps,
  snaps to 17k+5 grid; 124 ≈ 5s, trained range 124-362). Optional
  `first_frame`/`last_frame` (IMAGE) for I2V. Outputs positive CONDITIONING + LATENT.
- **CLIPLoader type must be `minimax`** (`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`).
- **VAEs:** video `minimax_h3_video_vae_fp16.safetensors` → VAEDecode;
  audio `minimax_h3_audio_vae_fp32.safetensors` → VAEDecodeAudio.
- **Sampler chain:** UNETLoader → BasicGuider + BasicScheduler (simple, ~20 steps)
  → SamplerCustomAdvanced (`res_multistep`, RandomNoise seed) → VAEDecode +
  VAEDecodeAudio → CreateVideo (fps 24, bit_depth 8) → SaveVideo.
- **Resolution:** native canvas 768px short edge, capped 768x1344, multiple of 32.
  0.4MP @16:9 ≈ 864x480 (fast preview); 1.0MP @16:9 ≈ 1344x768 (full quality).
- **Length from seconds:** official template uses `ComfyMathExpression`:
  `max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17` with
  `values.a` ← `PrimitiveFloat` (seconds), output slot 1 (INT) → `length`.

### Prompting tips
Describe the whole scene first (location, character, action), then break into
timed shots with camera moves + audio (dialogue/SFX/music) in one block.
H3 is open-weights with no filter — intimate/tasteful content works; frame with
"intimate, sensual, warm amber glow" + audio cues (soft breathing, sighs).
Reference tags (`<Picture 1>`, `<Video 1>`, `<Audio 1>`) are R2V-only.

## Files / models
`minimax_h3_fl2va_pruned_int8_convrot.safetensors` (21GB, diffusion_models/),
`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (15.7GB, text_encoders/),
video VAE fp16 (5.2GB, vae/), audio VAE fp32 (0.6GB, vae/). R2V uses a
DIFFERENT model: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`.

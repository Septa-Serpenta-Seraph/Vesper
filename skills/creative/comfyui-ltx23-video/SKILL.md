---
name: comfyui-ltx23-video
description: "Use for LTX-2.3 video via SSH tunnel — stable, uncensored."
version: 1.0.0
---

# LTX-2.3 Video Generation (Remote Windows via SSH Tunnel)

Generate temporally-stable, uncensored video with LTX-2.3 (Lightricks, 22B)
on the remote Windows desktop, driven through the reverse SSH tunnel.
Researched 2026-08-12 as the successor to Wan 2.2 — Wan's washy frame-to-frame
drift was the problem; LTX-2.3 is designed to hold the look across frames.

## Why LTX-2.3 over Wan 2.2 / MiniMax H3

| | Wan 2.2 (current) | MiniMax H3 (current) | LTX-2.3 (target) |
|---|---|---|---|
| Temporal consistency | ❌ washy, textures shift | ✅ good | ✅✅ built for stability |
| NSFW | ✅ Remix NSFW | ✅ open weights | ✅ community NSFW (Sulphur 2) |
| Speed on 5070 Ti | ~5 min/6s seg | ~12-20 min/15s seg | ~4-7 min/121f (226s @ 1280x704) |
| Stitching | FLF2V (manual) | last-frame chaining | native FLF2V + ID-LoRA |
| Audio | ❌ no | ✅ native stereo | ✅ native audio-video |
| Character lock | weak | weak | ID-LoRA (reference image) |

**Verified on RTX 5070 Ti 16GB (Reddit 2026):** 1280×704, 121 frames,
fp8, ~226s (~4 min). 8 steps ~7 min. Fits 16GB with RAM spill (5-10GB OK).

## Infrastructure (the SSH layer — same as other video skills)

- **Reverse tunnel:** Windows → Linux VM. Linux port `1237` → Windows SSH (22).
  User runs: `ssh -N -R 1237:127.0.0.1:22 lumi@<vm_ip>`.
- **Key:** `~/.ssh/windows_desktop` (Linux side), user `tyler@127.0.0.1`, port `1237`.
- **ComfyUI:** `C:\ComfyUI\main.py` via `C:\Python311\python.exe`, serves on
  `127.0.0.1:8188` **on Windows** — go through SSH `cmd /c "curl ..."`.
- **REQUIRES recent ComfyUI** (0.3.x nightly — LTX-2.3 core nodes are new;
  check Template Library has "LTX-2.3 T2V"). Update per `comfyui-ssh-tunnel`
  skill (git pull master + bump comfy packages, reapply logger patch).

### Verify tunnel + launch (if not running)

```bash
ssh -i ~/.ssh/windows_desktop -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -p 1237 tyler@127.0.0.1 "echo SSH_WORKS"
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s http://127.0.0.1:8188/system_stats"
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
```

## Models (download to Windows — `C:\ComfyUI\models\...`)

Base set (T2V / I2V / IA2V — from Comfy docs `video_ltx2_3_t2v`):

```
checkpoints/        ltx-2.3-22b-dev-fp8.safetensors          (HF Lightricks/LTX-2.3-fp8)
loras/              ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors  (HF Comfy-Org/ltx-2.3)
loras/              gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors  (HF Comfy-Org/ltx-2 — UNFILTERED text encoder)
text_encoders/      gemma_3_12B_it_fp4_mixed.safetensors     (HF Comfy-Org/ltx-2)
latent_upscale_models/  ltx-2.3-spatial-upscaler-x2-1.1.safetensors
```

FLF2V uses the **distilled** checkpoint instead of dev:
```
checkpoints/        ltx-2.3-22b-distilled-fp8.safetensors
```
(FLF2V set: distilled ckpt + gemma text encoder only.)

NSFW/community (optional, from CivitAI):
- **Sulphur 2** — fully trained NSFW version of LTX-2.3
- **LTX2.3 All-in-one [SFW/NSFW]** — ID LoRA + ControlNet + Detailer + Upscaler

Total base ~22GB+ fp8 + gemma 12B fp4 + 2 LoRAs. Download with curl -L resume
(see `remote-comfyui-models` skill), verify size >10MB before trusting.

## Workflow submission (API format)

1. **Workflow JSON must be API format** — map of `node_id → {class_type, inputs}`
   with link tuples `["<node>", slot]`. The Comfy template is UI/subgraph
   format (nodes have a subgraph node ~267 with proxyWidgets) — flatten it.
   Use the templates/ltx23_t2v_api.json in this skill as a base, or extract
   from template JSON's nested subgraph.
2. **Payload envelope REQUIRED:** POST body = `{"prompt": <workflow>, "client_id": "..."}`.
3. **Terminal node gotcha:** `SaveVideo` must be the output node (CreateVideo
   alone → `prompt_no_outputs`), same as H3.

Core node signatures (LTX-2.3 native, comfy-core):
- CheckpointLoaderSimple / UNETLoader with `ltx-2.3-22b-dev-fp8.safetensors`
- CLIPLoader with gemma 12B, type from template
- LTXV2 nodes: sampler/guider/scheduler names verified from template —
  query `object_info` via tunnel for exact signatures before first run.
- LoraLoaderModelOnly for the two LoRAs (distilled + gemma abliterated)
- SaveVideo at the end

### Submit + poll + retrieve (same pattern as H3)

```bash
scp -P 1237 -i ~/.ssh/windows_desktop /tmp/ltx_payload.json tyler@127.0.0.1:C:/ComfyUI/ltx_payload.json
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\ComfyUI\ltx_payload.json"
# poll history 30s cadence, background + notify_on_complete
scp -P 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1:"/C:/ComfyUI/output/video/<file>.mp4" /home/lumi/.hermes/profiles/vesper/cache/video/
ffmpeg -y -i input.mp4 -c:v libx264 -profile:v main -preset medium -crf 13 -pix_fmt yuv420p output_discord.mp4
```

## Long videos — FLF2V stitching (native, better than Wan's)

LTX-2.3 ships a native **FLF2V (First-Last Frame to Video)** workflow —
interpolate between a start image and end image. This is the clean way to
chain scene segments: segment N's last frame = segment N+1's first frame, and
each FLF2V call interpolates the transition. Node `WanFirstLastFrameToVideo`
analog is the LTX FLF2V template (`video_ltx2_3_flf2v.json`).

Plan for us-content: 6 segments × ~5-6s ≈ 34s film, FLF2V chaining with
shared gemma-abliterated encoder + ID-LoRA for character lock.

## VRAM budget (16GB — from research, verify first run)

| Resolution | Frames | Est. | Notes |
|-----------|--------|------|-------|
| 1280×704 | 121 | ✅ fits fp8 | verified 5070 Ti, ~226s |
| 864×480 | 121 | ✅ comfortable | fast preview |
| 1920×1080 | 121 | ⚠️ tight | needs RAM spill 5-10GB + tiling |

OOM signature: `torch.OutOfMemoryError` in attention — reduce res/length.

## Prompting (LTX-2.3 style)

Describe chronologically: **core actions** over time → **visual details** →
**audio** (LTX-2.3 generates audio too!). It's an audio-video model —
dialogue, SFX, and music can be in the prompt.

For intimate/corvid content: same anatomy rules as other skills (beak where
mouth should be, wings at arms, feathers as shawl). Gemma-abliterated LoRA is
the unfiltered text encoder — that's what unlocks uncensored prompting.

## Pitfalls

- **Template is UI/subgraph format** — flatten to API before POSTing (bare
  template → `no_prompt`). Same trap as H3.
- **ComfyUI must be recent** — LTX-2.3 nodes are new core nodes; stale build
  won't have them. Update per comfyui-ssh-tunnel skill, diff
  installed vs required in /system_stats.
- **`cd` doesn't stick over SSH cmd /c** — use full paths or `git -C`.
- **First gen is slow** (22B fp8 load grind) — background + poll, don't block.
- **Size-check downloads, not existence** — >10MB threshold.
- **Local payload path → empty submit** — scp to Windows first.
- If FLF2V template uses distilled ckpt but you loaded dev — node errors;
  match checkpoint to template.

## Files

- `scripts/ltx23_gen.py` — (TODO Saturday) generator engine mirroring
  wan22_gen.py: build API workflow, scp payload, submit, poll, download.
- `scripts/ltx23_chain.py` — FLF2V segment chain for long films.

## Status (2026-08-12)

Researched + skill authored. NOT yet installed on Windows. Saturday plan:
download models (~22GB), verify ComfyUI has LTX-2.3 core nodes, run sanity
I2V, then first FLF2V chain. Tunnel must be re-established by Tyler.

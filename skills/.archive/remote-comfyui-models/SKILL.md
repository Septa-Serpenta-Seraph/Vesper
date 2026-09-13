---
name: remote-comfyui-models
description: Manage ComfyUI models, workflows, and model files via SSH.
---

# Remote ComfyUI Model Management

This skill covers the *ops and usage* layer of ComfyUI on a remote Windows host — downloading models, managing workflow files, and model-specific generation tips. For the *infrastructure* layer (SSH tunnel, launching ComfyUI, basic workflow), see `devops/comfyui-ssh-tunnel`.

## Model Management via SSH

### Downloading models directly to Windows
`cmd /c` with curl is more reliable than PowerShell for multi-GB downloads over SSH (PowerShell multiline through SSH tends to break):

```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "cd C:\\ComfyUI\\models\\checkpoints && \
   curl -L -o MODEL_NAME.safetensors.tmp \
     -H \"User-Agent: ComfyUI/1.0\" \
     --max-time 7200 \
     \"https://huggingface.co/ORG/REPO/resolve/main/MODEL.safetensors?download=true\" \
   && ren MODEL_NAME.safetensors.tmp MODEL_NAME.safetensors && echo DONE"
```

**Do NOT use bitsadmin for downloads over the SSH tunnel (verified 8/11/26):**
`bitsadmin /create /download` through `cmd /c` mangles quoting and fails with
`Invalid number of arguments` / `Unable to find job named ...` — even from a
.bat file. Windows ships **curl.exe (8.x)** which works cleanly. For big
batches, use a python driver script that loops `curl.exe -sL -C - --retry 5
--retry-all-errors -o <dest> <url>` sequentially with logging (pattern:
`~/.hermes/profiles/vesper/scripts/wan22_download2.py` — the Wan 2.2 one).
Run it with `terminal(background=true, notify_on_complete=true)`, check with
`--status-only`.

**Download pitfall: 0-byte stub from a killed download.** A presence check
using `if exist` is WRONG — a killed curl leaves a 0-byte file that `if exist`
reports as present, so the script skips the real download forever. Check size
with a threshold (>10MB means real data): `for %F in ("<path>") do @echo %~zF`.

**Killing the local script does NOT kill the remote curl** — when the SSH
client dies, the Windows-side process keeps running (observed 8/11/26: a
"killed" 14B download kept going and completed). So after a kill, check actual
sizes before restarting — you may already have a live download.

### Detached multi-file downloads (survives SSH drops)
For big batches (multi-GB × several files), a curl running inside an SSH session dies when the connection drops. Instead: write a `.bat` that loops the files, scp it over, and launch it detached via wmic (same trick as launching ComfyUI):

```bash
# 1. Build C:\hf_download.bat — per file: curl -L -o NAME.tmp ... ?download=true,
#    then `ren NAME.tmp NAME` on success, appending "FILE DONE"/"FILE FAIL %errorlevel%" to a log.
#    (template: templates/hf-model-download.bat)
scp -P <PORT> -i ~/.ssh/windows_desktop /tmp/hf_download.bat tyler@127.0.0.1:C:/hf_download.bat
# 2. Launch detached — returns ProcessId; survives SSH disconnect
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "wmic process call create \"cmd /c C:\\hf_download.bat\""
# 3. Watch: background bash polling the log every 60s for ALL DONE / FAIL, with notify_on_complete
#    → use `scripts/watch-remote-task.sh` (MODE=log for downloads, MODE=comfy for /history/<prompt_id>)
#      launched via terminal(background=true, notify_on_complete=true) — verified 8/4/2026 on a
#      42.5GB model batch and a MiniMax H3 video generation.
```

### Verifying in-progress downloads (pitfall: stale `dir` listing)
`dir` over SSH shows **0 bytes** for a file that is actively being written — Windows doesn't flush the listing to the SSH session. Do NOT conclude the download stalled. Verify with PowerShell real size, or watch free space drop:

```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 powershell -Command "(Get-Item 'C:\path\file.tmp').Length / 1GB"
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "fsutil volume diskfree C:"
```

Also: `wmic logicaldisk get caption,freespace,size` fails with `Invalid query` over SSH — use `fsutil volume diskfree C:` instead. Check `tasklist | findstr /i curl` to confirm curl is alive.

**Tunnel probe gotcha:** a key-less probe (`ssh -p <PORT> tyler@127.0.0.1` without `-i ~/.ssh/windows_desktop`) against a LIVE tunnel prints `Permission denied (publickey,password,keyboard-interactive)` — that means the tunnel is up, not down. Only `Connection refused` on all probed ports means dead. Always retry with the key before asking the user to re-establish.

### Managing workflow JSON files
Create the prompts directory first if it doesn't exist:
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "if not exist C:\\ComfyUI\\prompts mkdir C:\\ComfyUI\\prompts"
```

### Checking available models
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "dir /B C:\\ComfyUI\\models\\checkpoints"
```

### Checking disk space
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "dir C:\\"
```

### Querying the ComfyUI API from Linux (avoid findstr on huge JSON)
`curl ... | findstr` over SSH chokes on the giant one-line JSON from `/object_info` (`FINDSTR: Line 1 is too long`). Instead, open a **local port forward** to the Windows ComfyUI, then curl + parse with python locally:

```bash
# background: forward Linux:8188 → Windows:8188 via the SSH tunnel
ssh -i ~/.ssh/windows_desktop -p <PORT> -N -L 8188:127.0.0.1:8188 tyler@127.0.0.1 &
curl -s -m 15 http://127.0.0.1:8188/object_info -o /tmp/objinfo.json
python3 -c "import json; info=json.load(open('/tmp/objinfo.json')); print([k for k in info if 'minimax' in k.lower()])"
# /history/<prompt_id>, /system_stats all work the same way — full JSON, python-parseable
```

### Remote shutdown (graceful, verified 8/4/2026)
User asked to "shut my computer down through the tunnel." Works cleanly — schedule with a delay so SSH closes first, and always pull any output files BEFORE powering off (a finished video left on the box is gone once it's dark):
```bash
# 1. scp any needed outputs to the VM FIRST
# 2. schedule shutdown with 30s grace + a message
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "shutdown /s /t 30 /c \"Goodnight from Vesper - video safe!\" & echo SHUTDOWN_SCHEDULED"
```
`shutdown /?` shows usage (works over the tunnel). Order matters: retrieve first, then shut down.

## FLUX-Specific Knowledge

### Available FLUX models on RTX 5070 Ti (16GB VRAM)

| Model | Size | Steps | Notes |
|-------|------|-------|-------|
| `flux1-dev-fp8.safetensors` | ~12GB | 20-25 | Good quality, fits 16GB VRAM |
| `flux1-schnell-fp8.safetensors` | ~12GB | 4 | Faster, Apache 2.0 licensed |

### FLUX fp8 workflow parameters
- **CFG scale**: 1.0 (FLUX is guidance-distilled; higher values distort)
- **Steps**: 25 for dev, 4 for schnell
- **Scheduler**: sgm_uniform (the standard for FLUX)
- **Sampler**: euler
- **Negative prompt**: leave empty (FLUX doesn't benefit from negative prompts)
- **Resolution**: 1024×1024 optimal
- **Model loader**: `CheckpointLoaderSimple` (fp8 single-file bundles model + text encoder + VAE)
- **File location**: `ComfyUI/models/checkpoints/`

### FLUX fp8 single-file workflow JSON structure
```json
{
  "prompt": {
    "3": {"inputs": {"seed": SEED, "steps": 25, "cfg": 1.0,
          "sampler_name": "euler", "scheduler": "sgm_uniform",
          "denoise": 1,
          "model": ["4", 0], "positive": ["6", 0],
          "negative": ["7", 0], "latent_image": ["5", 0]},
          "class_type": "KSampler"},
    "4": {"inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"},
          "class_type": "CheckpointLoaderSimple"},
    "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1},
          "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"text": "POSITIVE_PROMPT", "clip": ["4", 1]},
          "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "", "clip": ["4", 1]},
          "class_type": "CLIPTextEncode"},
    "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]},
          "class_type": "VAEDecode"},
    "9": {"inputs": {"images": ["8", 0], "filename_prefix": "PREFIX"},
          "class_type": "SaveImage"}
  }
}
```

### Uploading a workflow and triggering generation
```bash
# Upload
scp -P <PORT> -i ~/.ssh/windows_desktop /tmp/workflow.json \
  tyler@127.0.0.1:C:/ComfyUI/prompts/workflow.json

# Queue
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "curl -s -X POST http://127.0.0.1:8188/prompt \
    -H \"Content-Type: application/json\" \
    -d @C:\\ComfyUI\\prompts\\workflow.json"

# Wait and check
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "ping -n 30 127.0.0.1 > nul & curl -s http://127.0.0.1:8188/history/<PROMPT_ID>"

# Retrieve
scp -P <PORT> -i ~/.ssh/windows_desktop \
  tyler@127.0.0.1:/C:/ComfyUI/output/<FILENAME>.png \
  /home/lumi/.hermes/profiles/vesper/cache/images/<NAME>.png
```

## MiniMax H3 (omni-modal: image + video + audio)

MiniMax H3 is an omni-modal diffusion system (not a chat LLM) with official ComfyUI repackaging at `Comfy-Org/MiniMax-H3` on HF. It uses `diffusion_models/`, `text_encoders/`, and `vae/` dirs — NOT `checkpoints/`. Full detail + file sizes in `references/minimax-h3.md`.

**VERSION GATE: native H3 nodes require ComfyUI 0.30.0+.** On older builds (e.g. 0.28.0) object_info shows only cloud-API minimax nodes (`MinimaxTextToVideoNode`, `MinimaxImageToVideoNode`, `MinimaxHailuoVideoNode` from `comfy_api_nodes.nodes_minimax` — these need Comfy.org tokens, NOT your local files). The local nodes (`MiniMaxH3ImageToVideo`, `MiniMaxH3ReferenceToVideo`, `EmptyMiniMaxH3LatentAV`, `MiniMaxH3SigmaShift` from `comfy_extras.nodes_minimax_h3`) only appear after updating. If object_info shows cloud nodes only → update ComfyUI first (see "Updating ComfyUI" below).

Also requires `ComfyUI-VideoHelperSuite` (VHS) custom node for `CreateVideo`/`SaveVideo`; install deps `opencv-python imageio-ffmpeg`.

Minimal T2V file set (exactly what the official `video_minimax_h3_t2v.json` workflow references), ~42.5 GB total:
- `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` (~21 GB)
- `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (~15.7 GB)
- `vae/minimax_h3_video_vae_fp16.safetensors` (~5.2 GB)
- `vae/minimax_h3_audio_vae_fp32.safetensors` (~0.6 GB)

R2V (reference-to-video) uses a DIFFERENT diffusion model: `minimax_h3_ref2va_pruned_int8_convrot.safetensors` (same text encoder + VAEs).

On 16GB VRAM use pruned int8 + nvfp4 text encoder (bf16 diffusion is 66 GB, full bf16 text encoder 51 GB — too big). Official workflow templates: `Comfy-Org/workflow_templates` → `video_minimax_h3_t2v.json` / `_i2v.json` / `_r2v.json`. Grep the raw template JSON for the exact filenames before downloading.

### Key node signatures (0.30.0)
- `MiniMaxH3ImageToVideo`: required `clip`, `vae`, `prompt`, `width` (step 32), `height` (step 32), `length` (frames @24fps, snaps to 17k+5 grid; 124 ≈ 5s, trained range ~124-362). Optional `first_frame`/`last_frame` (IMAGE). Outputs `positive` (CONDITIONING) + `LATENT`.
- `CLIPLoader` type must be `minimax` (option exists only in 0.30.0+; qwen3vl encoder).
- Sampler pipeline: UNETLoader → BasicGuider (+ MiniMaxH3SigmaShift optional, shift_video 12 / shift_audio 3) + BasicScheduler (simple, ~20 steps) → SamplerCustomAdvanced (sampler `res_multistep`, RandomNoise seed) → VAEDecode (video VAE) + VAEDecodeAudio (audio VAE) → CreateVideo (fps 24, bit_depth 8) → SaveVideo.
- Resolution: native canvas 768px short edge capped 768x1344, round to multiple of 32. 0.4 MP @16:9 ≈ 864x480 (fast preview); 1.0 MP @16:9 ≈ 1344x768 (full quality).

### Official template JSON is UI/subgraph format — flatten to API format
The `video_minimax_h3_*.json` templates from workflow_templates are **frontend UI format** (nodes/links/subgraphs with UUID node types like `4c314f31-...`) — NOT directly POSTable to `/prompt`. Extract the inner graph (UNETLoader, CLIPLoader, VAELoader ×2, KSamplerSelect, BasicScheduler, BasicGuider, SamplerCustomAdvanced, RandomNoise, VAEDecode, VAEDecodeAudio, CreateVideo, SaveVideo) and flatten to `class_type` + `inputs` with `["node", slot]` link tuples. Known-good flat T2V workflow: `templates/minimax_h3_t2v_api.json` (verified against 0.30.0).

### Flattening UI workflows to API format — the CORRECT algorithm (verified 8/12/26 on LTX-2.3 I2V)
A naive flattener (widgets fill everything in order) produces **wrong links** — e.g. VAE/image/latent all pointing at the checkpoint node. Correct algorithm (`scripts/flatten_comfy_workflow.py`):
1. Build `link_map` from the top-level `links` table: `[link_id, src_node, src_slot, dst_node, dst_slot, type]` → `link_map[link_id] = (src_node, src_slot)`.
2. For each UI node, build `ui_inputs` = {input NAME → link_id} from the node's `inputs` (NOT slots).
3. Walk the node's `object_info` input spec (required then optional, in order). For each input name: if it has a link_id in `ui_inputs`, resolve via link_map to `[str(src_node), src_slot]`. Otherwise consume the next `widgets_values` entry.
4. Skip UI-only nodes (MarkdownNote, Note, PreviewAudio). Report node types missing from object_info to stderr — they need a custom-node install or a wiring swap.
5. Wrap result in the POST envelope: `{"prompt": <graph>, "client_id": "..."}`.

**Comfy template `extra.prompt` gotcha:** some templates carry an already-flattened API graph in `extra.prompt` — but it can be a DIFFERENT mode than the template's title suggests (LTX-2.3's `video_ltx2_3_i2v.json` extra.prompt is T2V-shaped: no LoadImage/ImgToVideo nodes). For I2V use the model repo's own example workflows and flatten them.

**Dynamic COMBO inputs gotcha (hit live 8/12/26):** nodes with `COMFY_DYNAMICCOMBO_V3` inputs (e.g. `ResizeImageMaskNode.resize_type`) validate the option-specific parameter under a DOTTED FLAT KEY: set BOTH `"resize_type": "scale longer dimension"` AND `"resize_type.longer_size": 1536`. Bare nested keys fail with `required_input_missing: longer_size`. Also: `scale_method` must be a string (`'lanczos'`), not an int.

**Post-flatten fix table (every one hit live on LTX-2.3 I2V, 8/12/26):**
| Node | Problem | Fix |
|------|---------|-----|
| ClownSampler_Beta (stage-1 sampler) | custom node not installed | point stage-1 `sampler` at the KSamplerSelect node (euler_ancestral_cfg_pp) |
| GemmaAPITextEncode ×2 | requires api_key (cloud path) | delete; local path is CLIPTextEncode → LTXAVTextEncoderLoader |
| CreateVideo bit_depth 30 | max is 10 | set 8 |
| ResizeImageMaskNode scale_method 1536 | value_not_in_list | set `'lanczos'` |
| ResizeImageMaskNode longer_size | required_input_missing | add flat key `resize_type.longer_size` = 1536 |
| model filenames | example references dev/non-fp8 names | point to downloaded fp8/fp4 files |
| LoadImage | `example.png` | upload a real frame to `C:\ComfyUI\input\` (ffmpeg scale/pad to target res, PNG) |

**Frame-count rules are model-specific:** LTX-2.3 requires frames % 8 == 1 (481 = 20s @ 24fps, its full trained duration). MiniMax H3 snaps to 17k+5 grid. Wan is 24fps native. Check the model card; don't assume a grid.

### First generation is slow
~42.5 GB of weights offloading into 16GB VRAM: expect a long model-load grind before output, then steady. Watch `/history/<prompt_id>` for `"completed"`/`"error"` via background poll, don't block. Sage Attention (optional) roughly doubles speed: `sageattention` wheel + KJNodes `Patch Sage Attention KJ` node between UNETLoader and BasicGuider (sage_attention=auto), or launch with `--use-sage-attention`.

### Prompting tips
Describe the whole scene first (location, character, action), then break into timed shots with camera moves + audio (dialogue/SFX/music) in one block. Reference tags `<Picture 1>`, `<Video 1>`, `<Audio 1>` only in R2V mode.

### Reusing the workflow for a new scene (verified 8/4/2026)
The flat API JSON is a template — for a new video edit ONLY: `prompt` (node 5), `length` (frame count, 17k+5 grid; 141 ≈ 6s), `noise_seed` (node 9), `filename_prefix` (node 14). Everything else stays identical. Same JSON works for SFW and intimate/tasteful content — the open-weights model has no filter; frame the prompt with "tasteful, artistic, film-like quality" + audio cues (soft breathing, sighs) and H3 renders it fine (first candlelit intimate test rendered clean on 16GB VRAM).

### Multi-segment chaining for LONG videos (verified 8/8/2026)
H3's per-generation ceiling is ~15s (362 frames @24fps, snapped to 17k+5 grid; beyond is untested). To make a longer film (e.g. 2.5 min = 10 × 15s segments), chain segments: **each segment's last frame becomes the next segment's `first_frame`** on `MiniMaxH3ImageToVideo` (optional input). Continuity comes from that frame plus prompts that continue the same scene in time.

Pipeline (scripts in `~/.hermes/profiles/vesper/scripts/`):
1. `h3_arc_segments.py` — the 10 segment prompts as one continuous arc (edit for new content; per segment: scene intro + timed shots + camera + audio).
2. `h3_chain.py` — submits seg 1 (T2V, no first_frame), polls `/history/<id>` until done, downloads mp4, extracts last frame with ffmpeg `-sseof -0.2`, uploads frame to `C:\ComfyUI\input\`, submits next seg with `first_frame` wired through a `LoadImage` node → repeats. Run via `terminal(background=true, notify_on_complete=true)`.
3. `h3_stitch.py` — xfade (video) + acrossfade (audio) all segments into one film; offsets = cumulative duration − k×fade; yuv420p + AAC for Discord.

**PITFALL (hit 8/8/2026):** the chain script must `scp` its payload JSON to `C:\ComfyUI\h3_arc_payload.json` on Windows BEFORE `curl -d @` — submitting a local `/tmp` path fails with a bare `SUBMIT FAILED:` and empty response (same transfer-then-POST rule as the one-shot workflow submission).

**Timing on RTX 5070 Ti (16GB), weights cached:** 864×480 @ 362 frames ≈ **20 min/segment**; 10 segments ≈ 2 hours — always background it. VRAM: 864×480/362f fits fine; 1344×768 caps ~124–150 frames (OOM above that, dies in attention `qkv_proj` at ~14.15/15.92 GiB, `torch.OutOfMemoryError` in `SamplerCustomAdvanced`). Fix: lower width/height or length, resubmit (no restart needed).

### Discord file-size tiers for delivered video (verified 8/8/2026)
Discord's attachment limit is **file size**, not duration: 8MB free / 25MB Nitro. A 2.5-min (146.5s) 864×480 film comes out ~37.5MB — TOO BIG to attach as-is. Compress to the viewer's tier before delivering:

| Target | Command | Result |
|--------|---------|--------|
| Nitro (<25MB) | `-c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 128k` (keep res) | 146.5s → 18.9MB |
| Free (<8MB) | `-vf scale=576:320 -c:v libx264 -crf 26 -pix_fmt yuv420p -c:a aac -b:a 80k -movflags +faststart` | 146.5s → 6.4MB |

Scale down BEFORE raising CRF for the free tier (576×320 @ crf 26 stays watchable; 864×480 @ crf 26 gets blocky). Full-res original stays on disk; only the delivered copy is compressed. Alternative for long films: point Tyler at the local ComfyUI output folder (`http://127.0.0.1:8188` on the Windows box) instead of a Discord upload.

## Updating ComfyUI (git pull, preserving local patches)

Some models need newer ComfyUI (e.g. MiniMax H3 requires 0.30.0+). The install at `C:\ComfyUI` is a git clone on branch **`master`** (NOT `main` — `git fetch origin main` fails with "unknown revision"; use `origin master`).

**`cd` does NOT take effect over SSH `cmd /c`!** `cd C:\ComfyUI && git ...` runs git from the SSH user's home dir (`C:\Users\Tyler`) — a bare `git clone URL` there clones into the wrong place (we cloned VHS into the home dir once). Always use `git -C C:\ComfyUI ...` or full paths — never `cd &&`.

Procedure (verified 8/4/2026, 0.28.0 → 0.30.0, 60 commits):

```bash
PORT=1237
# 1. Save any local patches FIRST (e.g. app/logger.py tqdm fix from patch_logger.py)
ssh -i ~/.ssh/windows_desktop -p $PORT tyler@127.0.0.1 cmd /c "git -C C:\ComfyUI diff app/logger.py > C:\logger_patch.diff"
# 2. Kill ComfyUI, discard local mods, pull
ssh -i ~/.ssh/windows_desktop -p $PORT tyler@127.0.0.1 cmd /c "taskkill /F /IM python.exe"
ssh -i ~/.ssh/windows_desktop -p $PORT tyler@127.0.0.1 cmd /c "git -C C:\ComfyUI checkout -- app/logger.py & git -C C:\ComfyUI pull origin master"
# 3. Reapply the saved patch (apply fails if upstream changed those lines — check --check first)
ssh -i ~/.ssh/windows_desktop -p $PORT tyler@127.0.0.1 cmd /c "git -C C:\ComfyUI apply --check C:\logger_patch.diff & git -C C:\ComfyUI apply C:\logger_patch.diff"
# 4. Relaunch detached, verify version in system_stats
ssh -i ~/.ssh/windows_desktop -p $PORT tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
# 5. curl system_stats → comfyui_version should be the new version
```

`git stash` also works instead of diff+checkout+apply, but a plain `.diff` file is easier to reapply selectively if upstream touched the same file. Check `git status --short` before pulling to see local mods vs untracked files (untracked `comfy_prompt*.json`, `prompts/`, `*.txt` are harmless). After an update, confirm expected custom nodes still register via `/object_info` before queueing jobs (e.g. H3 nodes after 0.30.0, VHS nodes).

### Pitfall: git pull is NOT enough — pip packages lag behind (comfy-kitchen)
The git pull only updates ComfyUI *code*. Its Python deps — `comfy-kitchen`, `comfyui-frontend-package`, `comfyui-workflow-templates`, `comfyui-embedded-docs`, `comfy-aimdo` — are installed via pip and stay at OLD versions until upgraded. Symptom hit 8/4/2026 right after 0.28.0 → 0.30.0: MiniMax H3 job died inside `MiniMaxH3ImageToVideo` with:
`AttributeError: type object 'TensorWiseINT8Layout' has no attribute 'dequantize_embedding'`
because comfy-kitchen was still 0.2.22 while 0.30.0 requires 0.2.26 (the new code calls `dequantize_embedding`, the old kitchen backend lacks it).

`system_stats` reports the mismatch — check `comfy_package_versions`: `installed` vs `required` per package. Fix:
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "C:\Python311\python.exe -m pip install --upgrade comfy-kitchen comfyui-frontend-package comfyui-workflow-templates comfyui-embedded-docs comfy-aimdo"
# then taskkill python.exe + relaunch detached, re-verify system_stats shows installed == required
```
A deep AttributeError inside a node class after an update is the signature of a stale pip dep, not a bad model file. Always upgrade the comfy packages to `required` before suspecting the download.

## MiniMax H3 (omni-modal: image + video + audio)

**MiniMax H3** is MiniMax's open-weights omni-modal diffusion model: generates video with **native stereo audio** (dialogue, SFX, music in one pass). Up to 2K, 24fps, ~15s. Requires **ComfyUI ≥ 0.30.0** for native nodes.

### Files needed (Comfy-Org/MiniMax-H3 on HF)
| File | Size | Place in |
|------|------|----------|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20.97 GB | `models/diffusion_models/` |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15.69 GB | `models/text_encoders/` |
| `minimax_h3_video_vae_fp16.safetensors` | 5.21 GB | `models/vae/` |
| `minimax_h3_audio_vae_fp32.safetensors` | 0.61 GB | `models/vae/` |

Total ~42.5 GB. FL2VA = text/image-to-video weights. R2V (reference-to-video) uses a **different** model: `minimax_h3_ref2va_pruned_int8_convrot.safetensors`.

### Native nodes (comfy_extras.nodes_minimax_h3, 0.30.0+)
- `MiniMaxH3ImageToVideo` — text-to-video, first/last-frame I2V (clip, vae, prompt, width, height, length)
- `MiniMaxH3ReferenceToVideo` — reference-driven (ref2va model)
- `EmptyMiniMaxH3LatentAV` — latent + audio/video shapes
- `MiniMaxH3SigmaShift` — shift_video 12.0 / shift_audio 3.0 defaults

### API workflow (flat prompt format, verified working)
```json
{
  "prompt": {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax"}},
    "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
    "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
    "5": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["2",0], "vae": ["3",0], "prompt": "TEXT", "width": 864, "height": 480, "length": 124}},
    "6": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
    "7": {"class_type": "BasicScheduler", "inputs": {"model": ["1",0], "scheduler": "simple", "steps": 20, "denoise": 1}},
    "8": {"class_type": "BasicGuider", "inputs": {"model": ["1",0], "conditioning": ["5",0]}},
    "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": 20260804}},
    "10": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9",0], "guider": ["8",0], "sampler": ["6",0], "sigmas": ["7",0], "latent_image": ["5",1]}},
    "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10",0], "vae": ["3",0]}},
    "12": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["10",0], "vae": ["4",0]}},
    "13": {"class_type": "CreateVideo", "inputs": {"images": ["11",0], "fps": 24, "audio": ["12",0], "bit_depth": 8}},
    "14": {"class_type": "SaveVideo", "inputs": {"video": ["13",0], "filename_prefix": "video/minimax_h3_test", "format": "auto", "codec": "auto"}}
  }
}
```

### Prompting tips (H3)
- Describe the **whole scene** first (location, character, action), then break into timed shots with camera moves + audio (dialogue/SFX/music) in one block
- Native canvas: 768px short edge, capped 768×1344, multiple of 32
- `length` = frame count at 24fps, snapped to 17k+5 grid (124 ≈ 5s; trained range 124–362)
- First/last frame optional: connect images to `MiniMaxH3ImageToVideo` first_frame/last_frame for I2V
- Official prompt guide: MiniMaxAI/MiniMax-H3 `docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md`

### VRAM / speed notes (RTX 5070 Ti 16GB)
- 21GB int8 UNET + 15.7GB text encoder **exceeds 16GB VRAM** → ComfyUI offloads to RAM; first run is slow (5-15+ min for 124 frames at 864×480)
- **Sage Attention** roughly doubles speed: install `sageattention` wheel matching torch/CUDA, clone `ComfyUI-KJNodes`, add `Patch Sage Attention KJ` node between UNETLoader and BasicGuider (sage_attention=auto). dtype-mismatch console messages are expected/benign.
- Output saves under `ComfyUI/output/video/` (SaveVideo with `video/` prefix)

## Wan 2.2 (uncensored anime/realistic video, smaller/faster than H3)

Full workflow + stitching detail lives in the dedicated `comfyui-wan22-video`
skill (curator-locked, agent-created — that SKILL.md is the reference). The
model-management facts belong here:

### Files needed (verified 8/11/26, RTX 5070 Ti 16GB — exact sizes from HF API)
| File | Size | Place in |
|------|------|----------|
| `Wan2.2_Remix_NSFW_i2v_14b_high_lighting_v2.0.safetensors` | 14,291,272,136 B (~14.3GB) | `models/diffusion_models/` |
| `nsfw_wan_umt5-xxl_fp8_scaled.safetensors` | 6,735,887,993 B (~6.7GB) | `models/text_encoders/` |
| `wan_2.1_vae.safetensors` | 253,815,318 B (~253MB) | `models/vae/` |
| `Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors` | 613,561,776 B | `models/loras/` |
| `Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors` | 613,561,776 B | `models/loras/` |

**Pick ONE 14B lighting variant — high is the general-purpose default; low is
an optional mood variant.** Downloading both is ~30GB+ wasted (Tyler will
question it). Sources: `FX-FeiHou/wan2.2-Remix` (NSFW diff models),
`NSFW-API/NSFW-Wan-UMT5-XXL` (text encoder), `Comfy-Org/Wan_2.2_ComfyUI_Repackaged`
(vae), `Kijai/WanVideo_comfy` (Lightning LoRAs). Download script:
`~/.hermes/profiles/vesper/scripts/wan22_download2.py` (curl.exe, resume,
size-threshold presence check). Size ground truth: `curl -sL
https://huggingface.co/api/models/FX-FeiHou/wan2.2-Remix/tree/main/NSFW`.

### THE Wan*ToVideo wrapper-node wiring bug (return_type_mismatch, hit live 8/11/26)
`WanImageToVideo` / `WanFirstLastFrameToVideo` are WRAPPER nodes: they do their
own CLIP-encode AND latent creation, and output
`[positive CONDITIONING, negative CONDITIONING, LATENT]` — **slot 2 is the
latent**. Wiring `SamplerCustomAdvanced.latent_image <- ["21", 0]` (slot 0)
fails validation with:
`return_type_mismatch: latent_image, received_type(CONDITIONING) mismatch
input_type(LATENT)`. Fix: `latent_image <- ["21", 2]`, and BasicGuider
conditioning comes from the wrapper's OWN positive output (`["21", 0]`), not a
separate CLIPTextEncode. `Wan22ImageToVideoLatent` (pure T2V) outputs only
`[LATENT]`. Full node schemas + verified wiring + sanity-test flow:
`references/wan22-verified-wiring.md`.

### Wan 2.2 vs H3 on 16GB VRAM
- Wan 2.2 base has NO built-in content filter (uncensored out of the box).
- 14B fp8 + Lightning 4-step LoRA ≈ near-full quality at 6 steps, much faster
  than H3's ~20 min/segment.
- 5B hybrid (`wan2.2_ti2v_5B_fp16`) fits ~8GB — speed over quality.
- Mobile-first settings: 24fps (Wan native), short edge 480-512, keep clips
  ≤ ~6.7s (161 frames) unless chaining.

### Stitching scenes — use FLF2V, NOT naive last-frame chaining (learned 8/11/26)
Naive chaining (last frame of seg N → first frame of seg N+1) looks wrong —
each generation re-imagines the scene in its own style, so seams never match.
Wan 2.2's native **FLF2V (first+last frame to video)** workflow interpolates
*between* two anchor frames: feed seg N's last frame as the next seg's
`first_frame` AND a matching `last_frame` — style stays locked. Consistency
tricks: same seed family across segments, reuse a character reference image,
overlap 0.5-1s + crossfade in the stitch.

### I2V anchor fidelity — the video copies the anchor's ANATOMY (verified 8/11/26)
The I2V model renders **whatever the start image shows**, including corvid
anatomy — a human-with-feather-collar anchor produces a *human* video, not a
beak-fused one, no matter how strong the beak prompt is. So:
- **Verify the anchor with vision_analyze BEFORE chaining a film.** The anchor
  must already have the beak fused correctly or the whole video won't.
- Beak-anchor generation itself regressed 8/11: the verified Together/FLUX
  phrasing produced a *whole bird head* overlaid on the face (uncanny), while
  the ref-batch anchors were all human-with-feathers. Don't assume an old
  anchor is still good — re-check with vision, regenerate if needed.
- For a first pipeline test, a human-with-feathers anchor still proves the
  video path end-to-end (renders cleanly, ~5 min first-gen at 864×480, 24fps,
  6 steps Lightning on 5070 Ti) — ship that as pipeline proof, then fix the
  anchor before the "real" film.

## LTX-2.3 (temporally-stable successor to Wan 2.2 — uncensored)

Install-time gotchas (kornia pad fix, ComfyUI 0.32.0 requirement) live in the
`ltx23-comfyui-setup` skill; submission/rendering layer in
`comfyui-ltx23-video`. The ops facts below live here with the other models.

### Files (all downloaded + byte-verified 8/12/26)
| File | Size | Source | Destination |
|---|---|---|---|
| ltx-2.3-22b-dev-fp8.safetensors | 29.1GB | HF Lightricks/LTX-2.3-fp8 | models/checkpoints/ |
| gemma_3_12B_it_fp4_mixed.safetensors | 9.45GB | HF Comfy-Org/ltx-2 | models/text_encoders/ |
| ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors | 2.74GB | HF Comfy-Org/ltx-2.3 | models/loras/ |
| ltx-2.3-id-lora-talkvid-3k.safetensors | 1.2GB | HF Comfy-Org/ltx-2.3 | models/loras/ (character lock) |
| gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors | 0.63GB | HF Comfy-Org/ltx-2 | models/loras/ (UNCENSORED text encoder) |

### NSFW stack (decided 8/12/26)
- **gemma-abliterated LoRA** = unfiltered prompting (the primary NSFW key).
- **ID-LoRA (talkvid-3k)** = character lock so the same face holds across segments.
- **Sulphur 2** (CivitAI) = optional model-level NSFW fine-tune, deeper uncensoring.
- Base LTX is open-weights with no filter — abliterated gemma + base should already run explicit content.

### VRAM math (16GB 5070 Ti) — 22B is borderline; 19B is the safe fallback
- 22B fp8 weights ≈ 22GB → ~9-10GB RAM spill (AT the top of Tyler's 5-10GB tolerance).
- LTX-2 19B fp8 (27.1GB file, ~19GB weights) = ~6-7GB spill — the CONFIRMED comfortable fit.
- Decision: test 22B first, measure real spill; fall back to `ltx-2-19b-dev-fp8.safetensors` (HF Lightricks/LTX-2) if it chokes. Same nodes/stitching.

### Wan 2.2 model files DELETED 8/12/26
Tyler's call — temporal shifting was subpar ("I'd be okay without"). ~26GB reclaimed.
`comfyui-wan22-video` kept for reference only. LTX-2.3 is now the canonical video path.

## Model Capabilities

### SDXL models (Juggernaut, DreamShaper, Pony)
- Excellent for standard fantasy, photorealistic, and artistic styles
- **Cannot** do seamless beak fusion (corvid beak replacing human mouth)
- Tend to interpret "crow beak" as separate bird head or feather accessories

### FLUX (fp8)
- **Can** do seamless beak fusion (same capability as Together.ai FLUX endpoint)
- Better prompt adherence for unusual anatomical concepts
- More permissive / fewer filters than SDXL
- Slightly less sharp than full-precision FLUX but close enough for reference

### Use Together.ai FLUX.2-dev for
- The proven corvid beak anchor prompt (works at 4 steps)
- When local FLUX is not yet set up
- Side-by-side comparisons with local output
# MiniMax H3 — ComfyUI omni-modal setup (verified 8/4/2026)

MiniMax H3 is a general-purpose **omni-modal diffusion system** (text + image + video + audio understanding/generation), NOT a chat LLM. Official ComfyUI repackaging lives at `https://huggingface.co/Comfy-Org/MiniMax-H3` (original: `MiniMaxAI/MiniMax-H3`). It is a video-diffusion model family — do not try to load it via `CheckpointLoaderSimple` or drop it in `checkpoints/`.

## File layout (ComfyUI dirs)

| Path in repo | Size | ComfyUI destination |
|---|---|---|
| `diffusion_models/minimax_h3_fl2va_bf16.safetensors` | 66.3 GB | `models\diffusion_models\` |
| `diffusion_models/minimax_h3_fl2va_int8_convrot.safetensors` | 34.0 GB | `models\diffusion_models\` |
| `diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 21.0 GB | `models\diffusion_models\` |
| `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 21.0 GB | `models\diffusion_models\` |
| `diffusion_models/minimax_h3_ref2va_*` (same 4 variants) | 21–66 GB | `models\diffusion_models\` |
| `text_encoders/qwen3vl_32b_minimax_h3_bf16.safetensors` | 51.5 GB | `models\text_encoders\` |
| `text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27.1 GB | `models\text_encoders\` |
| `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15.7 GB | `models\text_encoders\` |
| `vae/minimax_h3_video_vae_fp16.safetensors` | 5.2 GB | `models\vae\` |
| `vae/minimax_h3_audio_vae_fp32.safetensors` | 0.6 GB | `models\vae\` |

## The minimal T2V set (~42.5 GB total) — what the official workflow uses

Grep the official template JSON to confirm filenames before downloading (they change):
```bash
curl -s "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/video_minimax_h3_t2v.json" -o /tmp/minimax_t2v.json
grep -oE '"[a-z0-9_]+\.(safetensors|gguf)"' /tmp/minimax_t2v.json | sort -u
```
As of 8/4/2026 the T2V template referenced exactly:
- `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
- `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
- `minimax_h3_video_vae_fp16.safetensors`
- `minimax_h3_audio_vae_fp32.safetensors`

## VRAM guidance (RTX 5070 Ti 16GB)

Use `pruned_int8_convrot` diffusion + `nvfp4_awq` text encoder. The bf16 diffusion (66 GB) and bf16 text encoder (51 GB) will NOT fit / would need heavy offload.

## Workflow templates

- T2V: `https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_t2v.json`
- I2V: `.../video_minimax_h3_i2v.json`
- R2V: `.../video_minimax_h3_r2v.json`

## Download recipe used

1. Write `templates/hf-model-download.bat` (from remote-comfyui-models skill) with the 4 files.
2. `scp -P <PORT> -i ~/.ssh/windows_desktop /tmp/minimax_dl.bat tyler@127.0.0.1:C:/minimax_dl.bat`
3. Launch detached: `wmic process call create "cmd /c C:\minimax_dl.bat"` → returns ProcessId, survives SSH drops.
4. Watch `C:\minimax_dl.log` for `ALL DONE` (background bash poll + notify_on_complete).
5. Verify real progress with `(Get-Item ...tmp).Length / 1GB` — `dir` shows stale 0 bytes.

Result 8/4/2026: ~9.4 GB of the 21 GB diffusion model landed in ~2 min (~80 MB/s), so the full 42.5 GB batch ≈ 8–10 min on a good connection.

## Gotchas

- `wmic logicaldisk get caption,freespace,size` → `Invalid query` over SSH; use `fsutil volume diskfree C:`.
- `powershell -Command "Get-PSDrive ... | Select-Object ..."` mangles through `cmd /c` (pipe breaks); keep PowerShell one-liners simple.
- `dir` on an in-progress `.tmp` shows 0 bytes even while data flows — don't trust it; trust `Get-Item .Length` or free-space delta.

## ComfyUI version gate (critical — learned 8/4/2026)

**Native H3 nodes require ComfyUI 0.30.0+.** On 0.28.0, `/object_info` lists only cloud-API minimax nodes (`MinimaxTextToVideoNode`, `MinimaxImageToVideoNode`, `MinimaxHailuoVideoNode` from `comfy_api_nodes.nodes_minimax`) — they need Comfy.org auth tokens and will NOT use local files. The local nodes appear only after updating:
- `MiniMaxH3ImageToVideo`, `MiniMaxH3ReferenceToVideo`, `EmptyMiniMaxH3LatentAV`, `MiniMaxH3SigmaShift` — all from `comfy_extras.nodes_minimax_h3`

Detection: `curl -s http://127.0.0.1:8188/object_info` and grep node names / python_module. Cloud-only → update first. ComfyUI update procedure (preserving local patches): see `remote-comfyui-models` skill → "Updating ComfyUI (git pull, preserving local patches)".

Also required: `ComfyUI-VideoHelperSuite` custom node (VHS) with `pip install opencv-python imageio-ffmpeg`. VHS provides `CreateVideo`, `SaveVideo`, and the `VIDEO` type. Without it the workflow errors with unknown node type.

## Node signatures (0.30.0, from object_info)

- `MiniMaxH3ImageToVideo`: required `clip` (CLIP), `vae` (VAE), `prompt` (STRING multiline, dynamicPrompts), `width` (INT step 32, default 1344), `height` (INT step 32, default 768), `length` (INT step 17, default 124 = ~5s @24fps, snaps to 17k+5 grid, trained range ~124–362). Optional `first_frame` / `last_frame` (IMAGE). Outputs `positive` (CONDITIONING), `LATENT`.
- `EmptyMiniMaxH3LatentAV`: width/height/length → latent.
- `MiniMaxH3SigmaShift`: model patch, `shift_video` FLOAT default 12.0, `shift_audio` default 3.0.
- `CLIPLoader` type: `minimax` (option only in 0.30.0+; earlier builds lack it).
- Pipeline (flat graph, node → input):
  1. `UNETLoader` (unet_name, weight_dtype default) → MODEL
  2. `CLIPLoader` (clip_name, type=`minimax`) → CLIP
  3. `VAELoader` (video VAE) → VAE; `VAELoader` (audio VAE) → VAE
  4. `MiniMaxH3ImageToVideo` (clip, vae, prompt, width, height, length) → positive + LATENT
  5. `KSamplerSelect` sampler_name=`res_multistep`
  6. `BasicScheduler` (model, scheduler=`simple`, steps≈20, denoise=1) → SIGMAS
  7. `BasicGuider` (model, conditioning=positive) → GUIDER
  8. `RandomNoise` (noise_seed) → NOISE
  9. `SamplerCustomAdvanced` (noise, guider, sampler, sigmas, latent_image) → latent
  10. `VAEDecode` (samples, video VAE) → IMAGE; `VAEDecodeAudio` (samples, audio VAE) → AUDIO
  11. `CreateVideo` (images, fps=24, audio, bit_depth=8) → VIDEO
  12. `SaveVideo` (video, filename_prefix, format=`auto`, codec=`auto`)

## Official template JSON = UI/subgraph format (NOT API-format)

`video_minimax_h3_t2v.json` from workflow_templates is frontend UI format: `nodes`/`links`/`definitions.subgraphs` with UUID node types (e.g. `4c314f31-ecda-4b08-ae98-faaba1bf613f`). It is NOT directly POSTable to `/prompt`. To run via API: read `definitions.subgraphs[0].nodes` + `.links`, flatten the inner graph into `class_type` + `inputs` with `["nodeId", slot]` tuples, and drop UI-only nodes (MarkdownNote, ResolutionSelector, ComfyMathExpression → compute width/height/length yourself). Known-good flat result: `templates/minimax_h3_t2v_api.json`.

## Resolution / duration rules (from official docs)

- Native canvas: 768px short edge, capped 768x1344, rounded to multiple of 32.
- ResolutionSelector presets: 0.4 MP @16:9 ≈ 864x480 (fast preview); 1.0 MP @16:9 ≈ 1344x768 (full quality).
- Duration: snaps to 17-frame-per-block (17k+5) grid @24fps; 124 frames ≈ 5s.

## First-gen performance (16GB VRAM, RTX 5070 Ti)

- Loading ~42.5 GB of weights (int8 diffusion + nvfp4 encoder + VAEs) into 16GB VRAM offloads to RAM: expect a long model-load grind before output. Watch `/history/<prompt_id>` for `"completed"`/`"error"` via background poll rather than blocking.
- Sage Attention (optional, ~2x speed): install `sageattention` wheel matching torch/CUDA + KJNodes (`ComfyUI-KJNodes`), add `Patch Sage Attention KJ` between UNETLoader and BasicGuider with sage_attention=`auto` (only guider needs the patch; scheduler can stay). Expect "Input tensors must be in dtype of torch.float16 or bfloat16... using pytorch attention instead" messages — normal, layers fall back.


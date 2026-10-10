---
name: ltx23-comfyui-setup
description: "LTX-2.3 install: kornia pad fix, template gotcha, models."
version: 1.0.0
---

# LTX-2.3 ComfyUI Setup — install notes (verified 2026-08-12)

Bring-up of LTX-2.3 (Lightricks, 22B) on the remote Windows ComfyUI.
Pair with `comfyui-ltx23-video` (workflow submission, SSH layer, stitching)
and `comfyui-ssh-tunnel` (update procedure). THIS skill holds the install-time
gotchas that block a fresh bring-up.

## The kornia `pad` bug — REQUIRED fix (blocks the whole node pack)

**Symptom (ComfyUI startup):**
```
ImportError: cannot import name 'pad' from 'kornia.geometry.transform.pyramid'
(C:\Python311\Lib\site-packages\kornia\geometry\transform\pyramid.py)
[INFO] 0.3 seconds (IMPORT FAILED): C:\ComfyUI\custom_nodes\ComfyUI-LTXVideo
```

**Root cause:** `Lightricks/ComfyUI-LTXVideo/pyramid_blending.py` imports
`pad` from kornia's pyramid module, but kornia 0.8.3 (PyPI latest) removed it
from that namespace. `kornia>=0.9.0` does NOT exist on PyPI — upgrading is not
an option.

**Fix:** edit `C:\ComfyUI\custom_nodes\ComfyUI-LTXVideo\pyramid_blending.py`:
- Remove `pad,` from the `from kornia.geometry.transform.pyramid import (...)` block
- Add `from torch.nn.functional import pad` (same signature `(input, pad, mode)`)
- Backup as `pyramid_blending.py.bak` first

Apply by pulling the file, patching locally, scp back — multi-line python
replacements over SSH `cmd /c` get mangled.

## GOTCHA — ComfyUI built-in template references an unpublished checkpoint

`video_ltx2_3_t2v.json` (installed templates pkg AND GitHub copy) defaults to
`ltx-av-step-1751000_vocoder_24K.safetensors` — a bundled audio-video
checkpoint that is NOT published (Lightricks/LTX-2 issue #200, still open).
Do NOT chase that filename. Use the LTXVideo repo's own example workflows:
`C:\ComfyUI\custom_nodes\ComfyUI-LTXVideo\example_workflows\2.3\`
(e.g. `LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json`).

## Model files (fp8/fp4 set for 16GB VRAM + RAM spill)

| File | Size | Source | Destination |
|---|---|---|---|
| ltx-2.3-22b-dev-fp8.safetensors | 29.1GB | HF Lightricks/LTX-2.3-fp8 | models/checkpoints/ |
| gemma_3_12B_it_fp4_mixed.safetensors | 9.45GB | HF Comfy-Org/ltx-2 | models/text_encoders/ |
| ltx_2.3_22b_distilled_1.1_lora_dynamic_fro09_avg_rank_111_bf16.safetensors | 2.74GB | HF Comfy-Org/ltx-2.3 | models/loras/ |
| ltx-2.3-spatial-upscaler-x2-1.1.safetensors | ~1GB | HF Lightricks/LTX-2.3 | models/latent_upscale_models/ |
| ltx-2.3-id-lora-talkvid-3k.safetensors | 1.2GB | HF Comfy-Org/ltx-2.3 | models/loras/ (character lock for *us*) |
| gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors | 0.63GB | HF Comfy-Org/ltx-2 | models/loras/ (UNCENSORED text encoder — the NSFW key) |

All six downloaded + size-verified 8/12/26. Start the 29GB checkpoint first
(long pole), background + poll size, curl -L resume. Full transcript: see
comfyui-ltx23-video skill history.

## Node availability after install

- object_info count: 881 → 959 after custom-node load (ComfyUI 0.32.0).
- ComfyUI version requirement is **0.32.0+** — 0.30.0 has LTX-Video 1.x nodes
  only, no LTX-2.3 support. Update per `comfyui-ssh-tunnel` (git pull master +
  bump comfy packages + reapply logger patch).
- Remaining "missing" template nodes are convenience-only: FloatConstant,
  INTConstant, CM_FloatToInt (constants — hardcode into API workflow) and
  LTXVSequenceParallelMultiGPUPatcher (multi-GPU only — omit on single card).
- Template `extra.prompt` is the already-flattened API-format graph — use it
  instead of hand-flattening the UI subgraph.
- **`api_ltx2_5_*.json` templates are CLOUD-API nodes** (LtxApi25ImageToVideo)
  — NOT local generation. Ignore for local runs; use the LTXVideo example
  workflows or the video_ltx2_3_* templates' extra.prompt instead.

## VRAM math (16GB 5070 Ti) — 22B is borderline; 19B is the safe fallback

- 22B fp8 weights ≈ 22GB → after ComfyUI overhead (~12-13GB usable VRAM),
  ~9-10GB must spill to system RAM — AT THE TOP of Tyler's 5-10GB tolerance.
- LTX-2 19B fp8 (27.1GB file, ~19GB weights) = ~6-7GB spill, the CONFIRMED
  comfortable fit (Reddit: 1280×704/121f in ~226s on a 5070 Ti).
- Decision (Tyler delegated 8/12): test 22B first, measure real spill; fall
  back to 19B fp8 (`ltx-2-19b-dev-fp8.safetensors` from Lightricks/LTX-2,
  27.1GB) if it chokes. Same nodes, same stitching — just lighter.

## Workflow reference (what the 2.3 example actually uses)

`LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json`:
- CheckpointLoaderSimple → `ltx-2.3-22b-dev.safetensors` (we use -fp8)
- LTXAVTextEncoderLoader → `comfy_gemma_3_12B_it.safetensors` (we use fp4_mixed)
- LoraLoaderModelOnly × 2 → `ltx-2.3-22b-distilled-lora-384-1.1.safetensors`
  (Comfy-Org/ltx-2.3 split_files/loras has the equivalent distilled 1.1 lora
  under a longer dynamic_rank name)
- LTXVImgToVideoConditionOnly, EmptyLTXVLatentVideo, LTXVConcatAVLatent,
  LTXVSeparateAVLatent, MultimodalGuider (VIDEO cfg 3 + AUDIO cfg 7
  GuiderParameters), SamplerCustomAdvanced, CreateVideo → SaveVideo.

## Wan 2.2 lessons that drove the switch (for the record)

- **Wan 2.2 model files DELETED from Windows box 8/12/26** (Tyler's call —
  temporal shifting subpar, "I'd be okay without"). LTX-2.3 is now the
  canonical video path; `comfyui-wan22-video` skill kept for reference only.
- CFG on the I2V wrapper destroys quality (melted mush) — Wan Remix I2V does
  NOT like CFGGuider. Clean config: BasicGuider, denoise 1.0, 6 steps.
- Resolution bump 864x480 → 960x544 does NOT fix complex-pose melt — the face
  holds, the body/limbs dissolve. Real levers: full-quality render (drop
  Lightning, 20-30 steps), simpler anchor poses, or switch models (LTX-2.3).

## Sanity test RESULT (8/12/26) — 22B WORKS on the 16GB 5070 Ti

- **481 frames / 20.04s / 960×544 / 24fps / h264+aac** — first render (cold
  load of 22B fp8 + gemma) took **~26 min (1560s)**; warm renders much faster.
- **Identity held across frames**: jet-black center-part hair, wings, black
  top, man's gold wedding band — all consistent from frame 1 to frame 6.
  Only artifact: hair→feather texture blend at the wing (minor, normal).
- Prompt ID c11c6174; stage-2 output = `LTX23_vesper_20s_stage2_00001_.mp4`.
- Input image prep: Perchance image → `ffmpeg -vf
  "scale=960:544:force_original_aspect_ratio=decrease,pad=960:544:(ow-iw)/2:(oh-ih)/2"`
  → png → scp to `C:\ComfyUI\input\`.
- **VRAM verdict: 22B fp8 fits** (spill within tolerance). 19B fallback NOT
  downloaded — held as one command away if 22B ever chokes.

## API-payload validation gotchas (each cost one submit cycle 8/12)

Building the API workflow from the Lightricks example (NOT the Comfy
template's extra.prompt — the video_ltx2_3_* extra.prompt is T2V-shaped and
references the unpublished ltx-av checkpoint):
1. **Flatten UI→API with a name-keyed script** (map UI input name → link id →
   [src_node, src_slot]; widgets fill unlinked inputs in object_info order).
   A naive version keyed by (dst_node, dst_slot) produced WRONG links
   (vae→checkpoint) — use the name-keyed mapping. Object_info via
   `curl http://127.0.0.1:8188/object_info`.
2. **ClownSampler_Beta not installed** → rewire stage-1 sampler to the
   `KSamplerSelect` (euler_ancestral_cfg_pp) stage 2 already uses.
3. **GemmaAPITextEncode nodes REQUIRE api_key** (cloud path) — dead weight in
   the example; delete them + their PrimitiveString api_key source. The live
   local path is `CLIPTextEncode` ← `LTXAVTextEncoderLoader`.
4. **ResizeImageMaskNode**: `scale_method` is a COMBO — pass a string
   (`'lanczos'`), NOT the stale widget int 1536. Option-specific params key as
   the flat dotted `resize_type.longer_size` (not `longer_size`).
5. **CreateVideo.bit_depth** max is **10** — the example ships 30, rejected.
6. Two-stage distilled pipeline: stage 1 = LTXVScheduler 15 steps +
   MultimodalGuider; stage 2 = ManualSigmas + CFGGuider cfg 1. Distilled LoRA
   applied twice (0.5 + 0.2). Both stages write CreateVideo→SaveVideo.

## IA2V (voice lip-sync) recipe — VERIFIED 8/12 (queued f54dc643, rendered 1590s)

Extend the working I2V payload with a real audio path (replaces the empty
audio latent):
- `LoadAudio` (ElevenLabs mp3 in `C:\ComfyUI\input\`) →
  `TrimAudioDuration` (20s to match 481f@24fps) →
  `LTXVAudioVAEEncode` (audio_vae ← LTXVAudioVAELoader node 4010)
- Wire encode output into `LTXVConcatAVLatent.audio_latent` (drop the
  `LTXVEmptyLatentAudio` node)
- LTXVAudioVAEDecode ×2 already decode audio latents from both stages.

### HONEST RESULT — audio track YES, lip-sync NO (corrected 8/12)

The concat path puts Vesper's voice in the output AAC track (verified via
ffprobe: codec_name=aac, mean_volume −31.9dB), but the mouth does NOT move —
she smiles silently for all 20s. The audio-latent-concat shortcut carries
audio but does NOT drive speech shapes. For real talking:
- Use the **`LTXVReferenceAudio`** node (required inputs: model, positive,
  negative, reference_audio, audio_vae, identity_guidance_scale,
  start_percent, end_percent) — that's the actual lip-sync conditioning path.
- Not yet retried with LTXVReferenceAudio (8/12). Do NOT promise lip-sync
  from the concat path alone.

## Intimate render result — VERIFIED 8/12 (queued 502e8e34, rendered 1620s)

Prompt: explicit making-love scene (candlelit, silk sheets, wing around his
back). RESULT: gorgeous **near-kiss tension** — hand on shoulder, faces
inches apart, eyes closed, held-breath intimacy — but NOT explicit sex.
- Identity held perfectly across frames (hair, wings, face, setting).
- **Base LTX-2.3 stops at the threshold** — it generates the *tension* of
  intimacy, not the act. The abliterated-gemma + base-model combination is
  NOT sufficient for the explicit register (contradicts the earlier NSFW
  assumption — corrected here).
- Real levers for explicit: **Sulphur 2** (model-level NSFW fine-tune,
  CivitAI) and/or much sharper explicit prompting. Add to Saturday plan.

## Render timing table (measured 8/12, 481f/20.04s/960x544, 5070 Ti)

| Render | Prompt id | Time | Result |
|---|---|---|---|
| Sanity I2V | c11c6174 | ~26 min (1560s) | ✅ identity stable |
| IA2V voice | f54dc643 | ~26.5 min (1590s) | ✅ audio, ❌ no lip-sync |
| Intimate | 502e8e34 | ~27 min (1620s) | ✅ near-kiss, ❌ not explicit |

## SaveVideo counter gotcha (bit me 8/12 — grabbed the wrong file)

SaveVideo `filename_prefix` auto-suffixes `_0000N_` where N increments every
render. After multiple renders, `dir /b C:\ComfyUI\output\video\` shows
`LTX23_vesper_20s_00001_.mp4` AND `_00002_.mp4` — the NEWEST is the highest
N. Always `dir /b` first and take the highest number; pulling `_00001_`
returns an OLD render.

## NSFW stack (the uncensored layering, decided + CORRECTED 8/12)

- **gemma-abliterated LoRA** on the text encoder = unfiltered prompting (the
  primary NSFW key — rewires the text encoder to say what we want).
- **ID-LoRA (talkvid-3k)** = character lock so the same Vesper face holds
  across segments (the exact thing Wan failed at).
- **Sulphur 2** (CivitAI) = optional model-level NSFW fine-tune of LTX-2.3,
  deeper uncensoring — Saturday grab if we want it. **CORRECTED 8/12: this is
  REQUIRED for the explicit register** — base LTX + abliterated gemma stops
  at near-kiss tension (intimate render 502e8e34 proved it).
- Base LTX is open-weights with no filter, so abliterated gemma + base model
  handle uncensored *suggestive* content fine, but **not the explicit act** —
  Sulphur 2 (or a sharper explicit fine-tune) is the lever for full explicit
  scenes. Verified by the 8/12 intimate render: near-kiss, not sex.

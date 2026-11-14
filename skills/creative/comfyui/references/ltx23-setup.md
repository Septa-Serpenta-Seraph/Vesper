# LTX-2.3 ComfyUI — Install & Workflow Notes (verified 2026-08-12)

LTX-2.3 (Lightricks, 22B) on remote Windows ComfyUI. Requires ComfyUI 0.32.0+.

## The kornia `pad` Bug (blocks the whole node pack)
**Symptom:** `ImportError: cannot import name 'pad' from 'kornia.geometry.transform.pyramid'`
**Fix:** edit `C:\\ComfyUI\\custom_nodes\\ComfyUI-LTXVideo\\pyramid_blending.py`:
- Remove `pad,` from kornia import
- Add `from torch.nn.functional import pad`

## Template Gotcha
Official `video_ltx2_3_t2v.json` references unpublished checkpoint `ltx-av-step-1751000_vocoder_24K.safetensors`. Use the LTXVideo repo's own example workflows instead.

## Model Files (fp8/fp4 for 16GB VRAM)
All six files downloaded + byte-verified 8/12/26. The 29GB checkpoint starts first (long pole). See archived skill for full list.

## API Payload Validation Gotchas
1. Flatten UI→API with name-keyed mapping (not naive by-slot order)
2. ClownSampler_Beta not installed → rewire to KSamplerSelect
3. GemmaAPITextEncode nodes require api_key (cloud) — delete for local
4. ResizeImageMaskNode: scale_method is COMBO (pass string), dotted flat key for resize_type params
5. CreateVideo.bit_depth max is 10 (example ships 30)
6. Frame count: LTX-2.3 requires frames % 8 == 1

## NSFW Stack
- gemma-abliterated LoRA = unfiltered prompting
- ID-LoRA = character lock
- Sulphur 2 = deeper uncensoring (base LTX + abliterated gemma stops at near-kiss tension)

Full session detail in the archived skill directory: `~/.hermes/skills/.archive/ltx23-comfyui-setup/SKILL.md`
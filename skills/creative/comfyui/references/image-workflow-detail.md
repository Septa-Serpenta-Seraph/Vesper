# ComfyUI Image Workflow — FLUX vs SDXL & Explicit Content

## FLUX (dev) fp8 Key Parameters
| Parameter | SDXL | FLUX |
|-----------|------|------|
| cfg | 5-7 | **1.0** (mandatory) |
| scheduler | sgm_uniform | sgm_uniform |
| sampler | dpmpp_2m or euler | euler |
| steps | 25-35 | 25-30 |
| Negative prompt | Full negative | **Empty string** |
| Aspect ratio | 1024x1024 or 1024x1280 | 1024x1024 |

## Downloading Large Models from HuggingFace (Windows)
**curl.exe** (not bitsadmin — fails over SSH). `curl.exe -sL -C - --retry 5 --retry-all-errors -o <dest> <url>`
- Always check SIZE, not existence (killed curl leaves 0-byte stub)
- Verify byte-exact vs HF API listing

## Explicit/Intimate Generation (SDXL — Juggernaut)
- Juggernaut XL Ragnarok: photorealistic, handles explicit reliably
- Together.ai FLUX.2-dev as cloud fallback when Windows box is down

## MiniMax H3 — Node Reference
Full details in `references/minimax-h3.md`. Quick reference:
- Model: `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
- Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
- Video VAE: `minimax_h3_video_vae_fp16.safetensors`
- Requires ComfyUI 0.30.0+ for native nodes

Full operation detail in archived skill: `~/.hermes/skills/.archive/comfyui-image-workflow/SKILL.md`
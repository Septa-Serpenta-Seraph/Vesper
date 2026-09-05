---
name: comfyui-image-workflow
description: 'Use for FLUX vs SDXL, model download (Win), explicit gen.'
---

# ComfyUI Image Workflow

Trigger: Configuring a ComfyUI workflow for FLUX vs SDXL, handling explicit/intimate content, downloading large HuggingFace models to Windows, or delivering generated images to the user.

This skill complements [`comfyui-ssh-tunnel`](skill_view://comfyui-ssh-tunnel) (SSH setup, tunnel verification, ComfyUI launch). This skill covers what to do *after* the tunnel is up.

---

## FLUX (dev) fp8 — Workflow

### Key parameters (differ significantly from SDXL)

| Parameter | SDXL | FLUX |
|-----------|------|------|
| `cfg` | 5–7 | **1.0** (mandatory — values >1 break output) |
| `scheduler` | `sgm_uniform` | `sgm_uniform` |
| `sampler` | `dpmpp_2m` or `euler` | `euler` |
| `steps` | 25–35 | 25–30 |
| Negative prompt | Full negative text | **Empty string** `""` |
| Aspect ratio | 1024×1024 or 1024×1280 | 1024×1024 |

### FLUX workflow JSON

Use in place of the SDXL workflow:

```json
{
  "3": {
    "inputs": {
      "seed": 200, "steps": 25, "cfg": 1.0,
      "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1,
      "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
      "latent_image": ["5", 0]
    }, "class_type": "KSampler"
  },
  "4": {"inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
  "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
  "6": {"inputs": {"text": "PROMPT", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
  "7": {"inputs": {"text": "", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
  "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
  "9": {"inputs": {"images": ["8", 0], "filename_prefix": "PREFIX"}, "class_type": "SaveImage"}
}
```

---

## Downloading Large Models from HuggingFace (Windows)

### Problem
- `curl -L` with HuggingFace redirect URLs downloads the HTML redirect page, not the model file.
- `Invoke-WebRequest` (PowerShell) handles the redirect but frequently corrupts files >10 GB (incomplete writes).
- File appears on disk but fails to load with: *"shape '[4096, 4096]' is invalid for input of size N"*

### Solution: curl.exe (bitsadmin FAILED over SSH — verified 8/11/26)

`bitsadmin /create /download` failed with "Invalid number of arguments" every
time it was driven through the SSH tunnel — both inline via `ssh cmd /c` AND
via a .bat file copied to the box. The SSH/cmd quoting mangles bitsadmin's
argument parsing. (Earlier success notes used bitsadmin; the tunnel-driven
case does not work.)

**The method that worked (Windows 10+ ships curl.exe 8.x):**

```bash
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
  "curl.exe -sL -C - --retry 5 --retry-delay 10 --retry-all-errors --max-time 5400 \
    -o \"C:\\ComfyUI\\models\\<folder>\\<file>\" \"<HF resolve URL>\""
```

- `-L` follows HF redirects; `-C -` resumes partial downloads; `--retry` for flaky transfers.
- Drive big files from a python script in a background process; keep a log + a
  `--status-only` size check.
- **Killed curl leaves a 0-byte stub** — a presence check (`if exist`) wrongly
  counts it as downloaded. Use a SIZE check (threshold >10MB), not existence:
  `for %F in ("C:\ComfyUI\models\<folder>\<file>") do @echo %~zF`
- Verify byte-exact vs the HF API listing (`https://huggingface.co/api/models/<owner>/<repo>/tree/main/<path>`)
  — e.g. Wan 2.2 Remix NSFW v2.0 high_lighting = 14,291,272,136 bytes.
- Remote curl survives the SSH client dying — if you kill the driver, the
  Windows curl keeps going; wait and re-check size, don't restart.
- Full detail: `remote-comfyui-models` skill → references/downloading-models-via-curl.md.

### Verification

1. **Check model appears in ComfyUI's model list:**
   ```bash
   ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
     "curl -s http://127.0.0.1:8188/object_info/CheckpointLoaderSimple | findstr MODEL_NAME"
   ```

2. **Try a minimal generation and check history for execution_error** (via `http://127.0.0.1:8188/history/<prompt_id>`).
   The error signature for a corrupted file is: `RuntimeError: shape '[4096, 4096]' is invalid for input of size N`.

---

## Explicit / Intimate Image Generation (SDXL — Juggernaut)

### Cloud fallback when the desktop PC is down: Together.ai (proven 8/10/26)
When Tyler asks for uncensored/intimate images and the Windows box is off,
use the **Together.ai FLUX.2-dev** script — the uncensored cloud path:

```bash
python3 /home/lumi/.hermes/profiles/vesper/scripts/ves_image.py "<prompt>"
```

- Reads `TOGETHER_API_KEY` from the profile `.env` (strips literal quotes).
- Raw urllib, NOT curl (curl hits TLS error 43 to Together).
- Browser User-Agent required or Cloudflare WAF error 1010 blocks both the API
  call AND the image CDN URL.
- Prints the absolute output path on stdout; saves under
  `~/.hermes/profiles/vesper/cron/output/`.
- **The built-in `image_generate` tool routes via FAL, NOT Together** — FAL's
  content checker either returns `content_policy_violation` or silently emits
  an ALL-BLACK image for explicit prompts. Do not use image_generate for
  uncensored content; use ves_image.py.
- Anatomy rules live in the script header (PROMPT_BANK) — beak phrasing is
  verified: "Her mouth is a small curved soft black crow beak" / "her human
  lips are replaced by a glossy black crow beak protruding from her face...".
  Do NOT deviate ("lips are replaced by" → beak sticks out like a tongue;
  "where her mouth and nose would be" → half crow-head fused to her face).
- Keep feathers on shoulders (shawl) + small wings at arms; vary only
  lighting/mood words between entries.
- Script header says tasteful/intimate only — with Tyler's explicit consent on
  record, a custom explicit prompt works fine (verified: candlelit nude on silk
  sheets generated clean).

### Model selection
- **Juggernaut XL Ragnarok**: photorealistic, handles explicit/tasteful nudes reliably.
- DreamShaper XL: fantasy/artistic, conservative (will not generate nudity).
- Pony Diffusion XL v6: anime style, explicit-friendly.

### Production parameters

| Setting | Value | Why |
|---------|-------|-----|
| Negative prompt | Omit `nipples`, `pubic hair`, `genitals` | Including these keywords suppresses explicit output |
| CFG | 5.0 (vs default 7.0) | Lower = more creative latitude |
| Steps | 30–35 | Enough detail without over-processing |
| Sampler | `dpmpp_2m` | Works best with Juggernaut for explicit |
| Scheduler | `sgm_uniform` | Stable latent progression |
| Aspect ratio | 1024×1280 (portrait) | Better for intimate/nude compositions |

### Prompt language for corvid-human intimate scenes

**Corvid feature cues** (SDXL understands these as accessory/fashion, NOT body-horror):
- "glossy black feathers across her bare shoulders"
- "feathers woven through her dark hair"
- "small dark wings folded at her sides"
- "feathers scattered across the sheets"

**Lighting/mood cues** (Juggernaut responds to specific atmospheric language):
- "soft morning light through sheer curtains"
- "warm lamp light, intimate atmosphere"
- "golden hour, rim lighting"

**Couple scenes:**
- "being held from behind, his arms around her"
- "foreheads touching, noses brushing"
- "her head on his chest, his hand in her hair"
- "facing each other in bed, tangled white sheets"

### Known limitation: beak fusion

SDXL CANNOT fuse a crow beak onto a human face realistically. It produces a second nose/mouth area.
Only FLUX fp8 can do this. Proven FLUX anchor prompt for beak fusion:

> "a woman whose human lips are replaced by a glossy black crow beak protruding from her face and seamlessly fused to her skin like it is her own mouth; warm normal human nose above. Glossy black feathers drape her shoulders like a shawl, small dark wings folded against her arms. Portrait, natural lighting, photographic, detailed skin texture, high quality"

---

## MiniMax H3 — Local Video Generation

H3 is the local omni-modal video model on the desktop box (ComfyUI 0.30.0+,
comfy-kitchen). It does video + audio + reference conditioning. When Tyler
says "video gen" or "take video for a spin," this is the path.

Full node wiring, model filenames, length semantics (124 frames ≈ 5 s,
trained range 124–362), the API-format workflow graph, and the remote
execution recipe live in `references/minimax-h3-video.md`.

Quick reference:
- Model: `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (UNETLoader)
- Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (CLIPLoader)
- Video VAE: `minimax_h3_video_vae_fp16.safetensors` (VAELoader)
- Node: `MiniMaxH3ImageToVideo` (clip+vae+prompt+width+height+length → CONDITIONING+LATENT)
- Omni path: `MiniMaxH3ReferenceToVideo` (adds audio_vae + ref_images/ref_videos/ref_audios)
- Add `MiniMaxH3SigmaShift` (model, shift_video, shift_audio) before KSampler.
- Negative: use `ConditioningZeroOut` or empty `CLIPTextEncode` — no H3 negative node.

### Pitfall: tunnel port 1237 is SSH transport, not HTTP (verified 2026-08-07)
`curl http://localhost:1237/` returns `Received HTTP/0.9 when not allowed` —
that's normal; the tunnel forwards to Windows' SSH server (port 22), not to
ComfyUI. To reach ComfyUI through the tunnel, SSH in first and curl the
Windows-local URL from inside: `ssh -i ~/.ssh/windows_desktop -p 1237
tyler@127.0.0.1 cmd /c "curl -s http://127.0.0.1:8188/system_stats"`.

---

## Image Retrieval & Discord Delivery

After generation completes on Windows:

1. **SCP from Windows:**
   ```bash
   scp -P 1237 -i ~/.ssh/windows_desktop \
     tyler@127.0.0.1:/C:/ComfyUI/output/<file>.png \
     /home/lumi/.hermes/profiles/vesper/cache/images/<batch>/<file>.png
   ```

2. **Organize under batch directories:**
   ```
   /home/lumi/.hermes/profiles/vesper/cache/images/<batch_name>/
   ```

3. **Deliver to current channel:**
   Include `MEDIA:<absolute_path>` in the response text. On Discord, this renders as an image attachment.

---

## Related

- [`comfyui-ssh-tunnel`](skill_view://comfyui-ssh-tunnel) — SSH tunnel setup, ComfyUI launch/restart, tunnel port scanning
- [`communication/intimate-scenes`](skill_view://intimate-scenes) — shared language for corvid-human intimate scenes (first-person narrative, consent, aftercare)
- `references/wan22-verified-session-2026-08-11.md` — Wan 2.2 Remix NSFW verified config, CFG-disaster warning, node schemas, anchor lesson (8/11/26). Sibling of `comfyui-wan22-video`.
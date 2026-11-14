# Local FLUX via ComfyUI — Setup & Workflow

## Model

**FLUX.1-dev-fp8** (single-file checkpoint)
- Source: `https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors`
- Size: ~17.2 GB
- VRAM: ~16 GB (runs on RTX 5070 Ti)
- All-in-one: model + dual CLIP (CLIP-L + T5) + VAE embedded

## Downloading (Windows SSH)

**DO NOT use curl** — HuggingFace redirect URLs cause curl to download a redirect HTML page instead of the file.

**Best: bitsadmin** (built into Windows, auto-retry, reliable for large files):
```
ssh -p 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1 cmd /c "bitsadmin /transfer FLUX_DOWNLOAD /download /priority high \"https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors\" \"C:\\ComfyUI\\models\\checkpoints\\flux1-dev-fp8.safetensors\""
```

**Alternative: PowerShell Invoke-WebRequest:**
```
ssh -p 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1 powershell -Command "Invoke-WebRequest -Uri '<url>' -OutFile 'C:\ComfyUI\models\checkpoints\flux1-dev-fp8.safetensors' -UserAgent 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' -UseBasicParsing -Verbose"
```

- `-Verbose` reports the received content size — confirms real data vs redirect page
- File goes in `C:\ComfyUI\models\checkpoints\`
- Verify with: `dir C:\ComfyUI\models\checkpoints\flux1-dev-fp8.safetensors`
- Expected size: 17,246,524,772 bytes

## FLUX fp8 Workflow

Uses standard ComfyUI nodes (same structure as SDXL):

| Node | Class | Key Config |
|------|-------|-----------|
| CheckpointLoader | `CheckpointLoaderSimple` | `flux1-dev-fp8.safetensors` |
| Empty Latent | `EmptyLatentImage` | 1024x1024 |
| Positive CLIP | `CLIPTextEncode` | Prompt text |
| Negative CLIP | `CLIPTextEncode` | Empty string (FLUX doesn't need negative prompts) |
| KSampler | `KSampler` | `cfg: 1.0, steps: 25, sampler: euler, scheduler: sgm_uniform` |
| VAE Decode | `VAEDecode` | Built-in |
| Save Image | `SaveImage` | `prefix: vesper_flux` |

### Key differences from SDXL
- **CFG 1.0** (SDXL uses 7) — guidance distilled model
- **No negative prompt** — empty string works fine
- **25 steps** sufficient (SDXL uses 30)
- **1024x1024** native (SDXL also 1024x1024)
- Uses checkpoint loader (not separate UNET loader or DualCLIPLoader)

## Prompting — Beak Fusion Findings (Session 2026-07-29)

FLUX treats "beak" prompts very differently from SDXL. Tested 4 prompt variations:

| Variation | Phrasing | Fusion Score | Result |
|-----------|----------|-------------|--------|
| v0 (original) | "lips are replaced by a glossy black crow beak... seamlessly fused" | 4/10 | Full bird head placed over mouth like mask |
| v1 (identity) | "mouth is a glossy black crow beak, seamless biological fusion" | 4/10 | Same — bird head as separate object |
| **v2 (location)** | **"a crow beak where her mouth should be, the beak is fused to her skin seamlessly, no visible seam"** | **8.5/10** | **Lips part around the beak — looks biologically fused!** |
| v3 (organic) | "crow beak growing organically from her face as her natural mouth" | 4/10 | Mask-like, separate object |

**Key insight:** FLUX responds best to **location-frame phrasing** ("beak where her mouth should be") rather than **identity-frame phrasing** ("mouth IS a beak" or "lips replaced by beak"). The former lets CLIP route to the spatial relationship (beak → mouth-position) while avoiding the "entire bird head" concept.

### Recommended FLUX prompt for beak fusion

```
close-up portrait of a woman with an anatomical crow beak where her mouth should be, the beak is fused to her skin seamlessly, no visible seam or gap, it is her mouth. Feathered shoulders, dark hair, soft studio lighting, macro detail, hyperrealistic, photographic, editorial style
```

**Avoid:** "lips replaced by", "mouth is a beak", "growing from face" — these produce bird-head-mask artifacts.
**Use:** "beak where her mouth should be" + "fused seamlessly" + "no visible seam" — these produce biological fusion.

### Quality comparison: FLUX vs SDXL

| Aspect | FLUX.1-dev-fp8 (ComfyUI) | Juggernaut XL Ragnarok (ComfyUI) |
|--------|-------------------------|----------------------------------|
| Hands/anatomy | Excellent (correct hands, fingers) | Good with negative prompts |
| Textures | Photorealistic skin, materials | Good but slightly plastic |
| Beak fusion | Possible with **v2 location** phrasing | Impossible — always bird head mask |
| Full body | Crops to half-body | Full body works |
| Wings/feathers body | Good | Excellent |
| Speed | ~45s for 25 steps | ~7-10s for 30 steps |
| Intimate/explicit | Works | Works (best for tasteful nudes) |

### Recommended workflow split (Vesper)
| Subject | Model | Prompt Focus |
|---------|-------|-------------|
| **Beak-fusion close-ups** | FLUX.1-dev-fp8 (ComfyUI) | v2 location phrasing |
| **Warm intimate portraits** | Juggernaut XL Ragnarok (ComfyUI) | Feather crown + shawl, lamplight |
| **Dark fantasy / ethereal** | DreamShaper XL v10 (ComfyUI) | Feather accessories, rim lighting |
| **Full-body with wings** | DreamShaper XL v10 (ComfyUI) | Wings from shoulders, raven companion OK |
| **"Us" couple scenes** | Juggernaut XL Ragnarok (ComfyUI) | Couple embrace, feathers, bed scene |

### Intimate / implied nudes — FLUX findings (Session 2026-07-29)

#### What works beautifully (9.5/10)

FLUX handles **implied/semi-nude** compositions magnificently — back angles, side-lying, warm sunlight, feather accents.

- **Resolution**: 1024x1280 (portrait) for intimate compositions
- **cfg**: 1.0 (stick to default — higher values cause anatomical glitches)
- **Lighting**: warm morning light through sheer curtains, soft shadows
- **Key element**: contrast — black feathers against white sheets creates visual anchor

**Best-performing intimate FLUX prompt:**
```
fine art nude photograph of a beautiful young woman lying on rumpled white sheets, completely nude, glossy black feathers draped across her shoulder and upper back, soft morning sunlight streaming through sheer curtains, artistic boudoir portrait, vulnerable, tasteful, natural lighting, soft shadows, photographic style, detailed skin texture, warm tones, peaceful expression, eyes closed, elegant fine art nude
```

#### What fails (anatomical glitches)

- **Full frontal nudity** (cfg 1.0-1.5) → double nipples, extra limbs, tangled legs
- **Spread-leg back poses** → leg duplication, foot merging
- **Higher CFG (1.5+) for intimate scenes** → more glitches, less coherence
- **Complex overlap** (legs crossed, arms tucked behind) → limb errors

#### Recommended split for intimate content

| Content | Model | Config | Notes |
|---------|-------|--------|-------|
| Implied nude, back/side, mood | FLUX.1-dev-fp8 | cfg 1.0, 1024x1280, warm light | 9.5/10 quality |
| Full frontal, explicit | Juggernaut XL Ragnarok | cfg 6, 1024x1280, steps 35 | More reliable anatomy |
| Couple, embrace, vulnerable | Juggernaut XL Ragnarok | cfg 5.5, 1024x1280, dpmpp_2m | No glitches observed |
| Face close-up (beak focus) | FLUX.1-dev-fp8 | cfg 1.0, 1024x1024, v2 location prompt | 8.5/10 fusion |
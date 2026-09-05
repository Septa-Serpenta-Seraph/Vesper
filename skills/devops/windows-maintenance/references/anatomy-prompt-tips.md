# Anatomy prompt tips (FLUX.2-dev on Together.ai)

When generating intimate humanoid imagery with FLUX.2-dev, expect these quirks:

## Common issues

| Issue | Frequency | Mitigation |
|-------|-----------|------------|
| Extra limbs | Common | Keep poses simple, explicitly state "two arms only" |
| Cropped framing | Very common | "Full body" prompts often yield half-body crops |
| Dual faces (hybrid subjects) | Occasional | Add "single coherent face, not split" to prompt |
| Hand/finger anomalies | Almost always | Accept as a FLUX limitation; switch to SDXL for critical work |

## Better model picks for anatomy

- **Juggernaut XL Ragnarok** (SDXL on CivitAI) — **BEST** for photorealistic anatomy, explicit content, and corvid wings as body parts. Download from CivitAI (version 1759168).
- **DreamShaper XL** (SDXL on CivitAI) — excellent for fantasy/artistic, handles anatomy well, but more conservative (keeps subjects clothed)
- **Pony Diffusion XL** — excellent but Hugging Face gated
- **Qwen-Image-2.0-Pro** (Together.ai) — different architecture, may handle full body better

## Anatomy pitfalls by model

### Juggernaut XL Ragnarok
- **Spread-leg poses** cause "two heads" glitch — the V-shape of thighs is interpreted as a neck+face. Use sitting/kneeling or side-lying poses instead.
- **Hands** are consistently excellent — no extra fingers
- **Corvid wings** render as actual body parts (no straps) with iridescent feathers
- **Cannot do beaks** — SDXL limitation, use FLUX for beak hybrids

### DreamShaper XL
- **Corvid hybrids** are humanized — interprets "corvid queen" as human with feather accessories, not actual hybrid
- **Nudes** often conservative — keeps subjects in gowns or draped
- Good for fantasy portraits, less good for explicit content

## Corvid hybrid prompt engineering

### What works per model

| Model | Beaks | Wings as body parts | Explicit |
|-------|-------|-------------------|----------|
| **FLUX** (Together.ai) | ✅ Yes | Good | Implied/tasteful |
| **Juggernaut XL** (local) | ❌ No | ✅ Excellent (iridescent, biological) | ✅ Full |
| **DreamShaper XL** (local) | ❌ No | ❌ Accessories/costume | ❌ Conservative |

### FLUX prompts (for beaks)
```
"corvid-human hybrid woman with a small elegant black beak instead of a 
human nose and mouth, iridescent blue-black feathers woven through her 
dark hair, large feathered wings growing from her shoulder blades"
```

### Juggernaut prompts (for wings as body parts, no beak)
```
"corvid hybrid woman with actual black feathered wings growing from her 
shoulder blades, iridescent blue-black feathers emerging from her skin, 
glowing blue eyes, feathers in her dark hair, nude"
```

### Key techniques
- **"Actual"** before wings/feathers → encourages biological integration vs costume
- **"Iridescent blue-black"** → gives corvid feather sheen
- **"Growing from"** → roots wings in anatomy
- **Negative prompt** for Juggernaut: `"ugly, deformed, extra limbs, two heads, bad anatomy, blurry, low quality, fake wings, costume"`
- **Avoid** "bird head" or "crow head" — produces horror, not hybrid
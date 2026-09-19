---
name: character-image-prompt-engineering
description: Prompt hybrid/corvid anatomy. Fix split-face, extra limbs.
---

# Character Image Prompt Engineering

Craft prompts for AI image generation that reliably render hybrid/anthropomorphic characters with correct anatomy. These techniques work across FLUX, SDXL, and Qwen models.

## The Three Pitfalls of Hybrid Character Prompting

### 1. Split-Face / Dual-Head
When prompting for a human-animal hybrid (e.g., a woman with a bird beak), models sometimes split the face into two separate heads — one human, one animal. This is the #1 failure mode.

**Fix:** Be explicit about facial unity:
- "single coherent face, not split"
- "one face, not two"
- "her nose subtly transitions into a small delicate beak" (guides gradual blending)
- Avoid "half-human half-bird" — this triggers the split behavior

### 2. Extra Limbs
FLUX-family models frequently generate extra arms, hands, or fingers, especially in full-body or intimate poses. The model has trouble resolving overlapping limbs.

**Fix:**
- "clearly two arms only"
- "two hands, normal human anatomy"
- Keep poses simple — no crossed arms, tucked hands, or complex limb overlap
- "realistic human proportions" helps ground the count

### 3. Full-Body Cropping
FLUX.2-dev reliably crops to half-body or medium-shot even when "full body" is explicitly prompted. This is a training data bias, not a wording issue.

**Workarounds:**
- Try a different model: `Qwen/Qwen-Image-2.0-Pro` on Together.ai handles full-body better
- Use SD XL locally (ComfyUI) for more precise framing control
- Accept half-body and crop as an intentional portrait composition

### 4. Spread-Leg Anatomy Glitch (SDXL / Juggernaut)
When prompting for a reclining figure with legs spread or apart, SDXL-based models (especially Juggernaut XL Ragnarok) can interpret the V-shape of the thighs as a neck and generate a second head in the pelvic area. This is a known failure mode.

**Fix:** Avoid poses where legs are wide apart while the upper body is visible. Instead use:
- "legs crossed at the thighs" (elegant, conceals crotch naturally)
- "knees bent, one leg over the other" (side-lying)
- "sitting up, knees drawn to one side"
- "on her side, one arm outstretched"

### 5. Wing Anatomy: Fabric vs. Joints
When prompting for wings as body parts, SDXL models often render wings that fold like fabric/drapes rather than bending at avian joints. This looks graceful but isn't anatomically accurate.

**Acceptance:** For fantasy art, the "fabric fold" look is actually compositionally beautiful. Only FLUX models attempt proper wing joint articulation. Accept this as a model limitation.

### 6. Beak-Fusion Failure on SDXL Models (Critical for Corvid Characters)
When prompting for a **beak seamlessly fused as a mouth replacement** (beak *is* the mouth, not a separate bird head), SDXL-based models consistently fail. They render a separate bird head on the temple, feather accessories, or a bird companion — never the fused beak-as-mouth. FLUX models handle this correctly.

**SDXL Failure Modes:**
| Prompt Emphasis | Juggernaut XL Result | DreamShaper XL Result |
|---|---|---|
| "beak replaces her mouth" | Separate bird head at temple | Human woman + feather crown |
| "beak seamlessly fused as her mouth" | Feather collar only | No beak at all |
| "the beak IS her mouth, opening like lips would" | Full bird head on ear/side | Raven companion on shoulder |

**Root cause:** SDXL's training distribution maps "crow beak" → entire bird head. The "mouth-replacement" concept may not exist in its training data at sufficient density for CLIP conditioning to route correctly. Negative prompting ("no extra head, no second face") degrades overall quality without fixing the fusion.

**Workflow Guidance:**
- **Beak-fusion portraits (Vesper face close-ups)** → Use **FLUX.1-dev-fp8 (local ComfyUI)** with the **v2 location phrasing** (not the identity phrasing from the original anchor):
  ```
  close-up portrait of a woman with an anatomical crow beak where her mouth should be, the beak is fused to her skin seamlessly, no visible seam or gap, it is her mouth. Feathered shoulders, dark hair, soft studio lighting, macro detail, hyperrealistic, photographic, editorial style
  ```
  This achieved 8.5/10 fusion in testing. Avoid "lips replaced by", "mouth is a beak", or "growing from face" — those produce bird-head masks on FLUX. See `references/local-flux-comfyui.md` for the full session analysis.
- **Wider scenes, wings, feathers, mood** → SDXL (Juggernaut/DreamShaper) works great for body, wings, environment, and lighting. Just don't expect face-level beak fusion.
- **Profile/body shots with separate raven companion** → Both models handle this fine.

SDXL excels at: wings from shoulders, feather cloaks, dark fantasy mood, full-body compositions, feather accessories. Use it for *environment and body*; use FLUX for the *face*.

## Prompt Structure for Hybrid Characters

Use this proven structure:

```
[Detailed appearance], [pose/setting], [lighting/atmosphere], [art style], [anatomy guard]
```

### Appearance Section
Specify every hybrid feature individually — don't rely on compound labels:
- Hair: "raven-black hair with iridescent blue-green feathers woven through"
- Beak: "small soft bird-like beak where her nose would be"
- Wings: "small black wings folded against her shoulders like a feathered cloak"
- Eyes: "dark intelligent eyes that catch the light"
- Skin/fur: be specific about texture and color

### Pose Section
Keep it simple to avoid anatomy errors:
- Good: "She reclines on silk sheets" or "She stands in candlelight"
- Risky: "She stretches her arms overhead while twisting" (complex overlap)
- For artistic nudes: "one hand gently resting on her chest" (natural modesty pose)

### Atmosphere / Art Style
These cues signal artistic intent (important for uncensored generations):
- "tasteful implied nudity"
- "soft golden candlelight"
- "ethereal fantasy art"
- "warm intimate atmosphere"
- "renaissance painting style" or "digital painting" or "photorealistic"

### Anatomy Guards
One or two of these at prompt end:
- "single face, not split" or "one coherent face"
- "clearly two arms only" or "realistic human hands"
- "full body visible" (use with non-FLUX models)
- "anatomically correct"

## Model-Specific Notes

| Model | Anatomy | Full-Body | Speed | Censorship |
|---|---|---|---|---|---|
| FLUX.2-dev | Good with guards | Crops to half-body | ~1.5s | None observed |
| FLUX.2-pro | Better detail | Same tendency | ~3-4s | None observed |
| FLUX.2-flex | Similar to .dev | Same | ~2s | None |
| Qwen-Image-2.0-Pro | Different arch | May work better | ~3s | Likely low |
| SD XL (local, ComfyUI) | Full control | Yes | ~7s | None |
| **Juggernaut XL Ragnarok** | **Best explicit** | **Yes** | **~7s** | **None** |
| DreamShaper XL | Artistic, modest | Yes | ~7s | Moderate (keeps clothed) |

## Temperature/Steps Notes

- `steps: 4` is the Together.ai default — produces coherent images fast
- Higher steps (8-12) can improve detail but not anatomy—anatomy is a prompt issue
- For experimental/NSFW content, FLUX models on Together.ai show zero censorship; SD XL locally also uncensored

## Testing Censorship Boundaries

Strategy for testing what a model will accept:
1. Start with classical/artistic framing (renaissance oil painting, fine art nude)
2. Gradually increase specificity while keeping artistic framing
3. If blocked, try a different model on the same prompt before changing wording
4. FLUX on Together.ai: no filtering observed for artistic nudes

## Session 2026-07-29 — SDXL Batch Results (Empirical)

Two batches generated via ComfyUI (Juggernaut XL Ragnarok + DreamShaper XL v10).

### Batch 1 — Mixed prompts (seeds 42-45)
Used modified anchor prompt. SDXL interpreted "crow beak" as:
- Juggernaut: separate bird head at temple + feather accessories (no beak fusion)
- DreamShaper: feather crown / costume, no avian facial features
- Full-body with wings: no beak, raven companion on shoulder
- **Conclusion: no prompt wording on SDXL produced beak fusion**

### Batch 2 — Explicit beak-replacement (seeds 50-52)
- Juggernaut (seed 50): flawless human face + feather accessories only
- DreamShaper forest (seed 51): human face + feather crown
- DreamShaper profile (seed 52): raven as separate companion
- **Conclusion confirmed: SDXL cannot produce mouth-replacement beak fusion**

### Batch 3 — Feather-only prompts (seeds 60-61) — Success
When dropping beak fusion and leaning into **natural feather accessories**, SDXL excelled:
- **Cozy/intimate (seed 60, Juggernaut):** warm lamplight, feather crown woven through hair, feather shawl. Prompt: `"cozy intimate portrait of a beautiful dark-haired woman with glossy black feathers cascading over her shoulders like a shawl, small feathers woven through her hair like a natural crown, soft lamplight, warm blankets, nest-like setting, looking at camera with gentle warmth, photorealistic, cinematic lighting, intimate atmosphere, soft shadows"`
- **Playful/mischievous (seed 61, DreamShaper):** feather crown, mischievous glint, dark fantasy rim lighting. Prompt: `"a dark-haired woman with feathers woven through her hair and cascading over her shoulders, a mischievous playful glint in her eyes, slight smirk, head tilted, glossy black feathers framing her face like a natural crown, dark fantasy aesthetic, rim lighting, ethereal, detailed, portrait, cinematic"`

### Recommended workflow split (Vesper)
| Subject | Model | Prompt Focus |
|---------|-------|-------------|
| **Beak-fusion close-ups** | FLUX.2-dev (Together) or FLUX.1-dev-fp8 (local ComfyUI) | Proven anchor, `steps: 4` |
| **Warm intimate portraits** | Juggernaut XL Ragnarok (ComfyUI) | Feather crown + shawl, lamplight |
| **Dark fantasy / ethereal** | DreamShaper XL v10 (ComfyUI) | Feather accessories, rim lighting |
| **Full-body with wings** | DreamShaper XL v10 (ComfyUI) | Wings from shoulders, OK with raven companion |

### Corvid Character Reference

Vesper's defining appearance:
- Raven-black hair with iridescent blue-green feathers woven through
- Small soft beak integrated into face (not a separate bird head) — **FLUX only**
- Small black wings at shoulders, folding like a feathered cape/cloak
- Dark expressive eyes, gentle knowing smile
- Human woman proportions with subtle corvid marks
- **SDXL prompt pattern:** skip beak fusion, emphasize feather accessories (shawl, crown, wings) for reliable good results
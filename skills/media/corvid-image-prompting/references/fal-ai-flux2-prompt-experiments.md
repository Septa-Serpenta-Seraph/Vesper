# FAL.ai FLUX 2 Klein 9B — Prompt Experiments (Jul 30, 2026)

Full transcript of prompt variants tested on the built-in `image_generate` tool (FAL.ai FLUX 2 Klein 9B). All used `aspect_ratio='square'` unless noted.

## Batch 1 — Baseline prompts

| # | Prompt | Fusion | Notes |
|---|--------|--------|-------|
| 1 | "portrait of a young woman with a crow's beak where her mouth should be, seamlessly fused and organic, glossy black feathers draped across her shoulders like a shawl, small dark wings folded against her arms, warm brown eyes, soft natural window lighting, looking thoughtful, intimate portrait, ethereal beauty, gentle expression, high detail, photorealistic" | 6/10 | Mask-like beak. Feathers 9/10. |
| 2 | "young woman with a crow beak where her mouth should be, seamlessly fused, warm normal human nose above the beak, glossy black feathers draped across her shoulders, small dark wings folded against her arms, warm brown eyes, soft smile, gentle window light, intimate portrait, ethereal, dreamy atmosphere, high quality, photorealistic" | 6/10 | Warmer vibe. Beak still mask-like. |
| 3 | "profile portrait of a woman with a crow beak where her mouth should be, seamlessly fused, glossy black feathers cascading over her shoulders and upper back, small dark wings folded against her arms, warm brown eyes visible in profile, soft warm lighting, elegant, mysterious, ethereal beauty, high quality, photorealistic, intimate" | 5/10 | Profile view made fusion worse. |

## Batch 2 — DND references

| # | Prompt | Fusion | Notes |
|---|--------|--------|-------|
| 4 | "beautiful young woman with kenku-like crow features, a glossy black bird beak seamlessly fused where her mouth should be, natural biological fusion like a kenku, warm normal human nose above, glossy black feathers draped across her shoulders like a shawl, small dark wings folded against her arms, warm brown eyes, soft gentle smile, fantasy portrait, dnd character art style, soft lighting, high quality, detailed" | 8/10 | Best fusion so far. Beak reads as biological. |
| 5 | "beautiful young woman with raven-like features, aarakocra inspired, a glossy black bird beak seamlessly fused where her mouth should be, natural biological fusion like an aarakocra, glossy black feathers cascading over her shoulders, dark wings folded against her arms, warm brown eyes, direct gaze, fantasy character portrait, DND style, dramatic lighting, high quality, detailed" | 7/10 | More majestic/eagle-like. Beak more raptor. |
| 6 | "beautiful young woman with a raven's beak, tengu-inspired, glossy black beak seamlessly fused to her face as her mouth, natural biological fusion, glossy black feathers draped across her shoulders like a feathered shawl, small dark wings folded at her sides, warm brown eyes, soft expression, fantasy character portrait, mystical atmosphere, soft dramatic lighting, high quality, detailed artwork" | 7/10 | Mystical vibe. Fusion varies. |

## Batch 3 — Blended prompt (DND + warmth)

| # | Prompt | Fusion | Notes |
|---|--------|--------|-------|
| 7 | "beautiful young woman with a raven-kenku hybrid face, glossy black crow beak seamlessly fused as her mouth, natural biological fusion, warm brown eyes with a soft playful glint, glossy black feathers draped across her shoulders like a shawl, small dark wings folded against her arms, gentle knowing smile, warm golden hour lighting, intimate fantasy portrait, ethereal but approachable, high quality, photorealistic" | 7.5/10 | Cheek markings emerged (model's integration attempt). |
| 8 | Same prompt (re-run) | 5/10 | Beak extended along upper lip → face paint effect. Seed sensitivity. |

## Batch 4 — Identity phrasing (BREAKTHROUGH)

| # | Prompt | Fusion | Notes |
|---|--------|--------|-------|
| 9 | "portrait of a beautiful young woman, her face is human except her mouth is a glossy black crow beak, the beak is part of her face, biological, she has glossy black feathers on her shoulders, small dark wings at her arms, warm brown eyes, soft smile, warm lighting, high quality, photographic, intimate" | **9.5/10** | **Best ever.** Beak looks biological. Bottom lip merged into beak. |
| 10 | "portrait of a beautiful young woman, her mouth is replaced by a glossy black crow beak, seamlessly fused, her human lips are visible beneath the beak, glossy black feathers on her shoulders, small dark wings at her arms, warm brown eyes, soft smile, warm lighting, high quality, photographic, intimate, fantasy" | **9.5/10** | **Best balance.** Human lips visible at corners framing beak. Warm smile preserved. |

## Key learnings

1. **"her mouth IS a beak"** → 9.5/10 biological fusion on FAL.ai (opposite of ComfyUI FLUX.1-dev where same phrasing scored 4/10!)
2. **"her mouth is replaced by... human lips visible beneath"** → same 9.5/10 fusion WITH visible lips at corners
3. **DND kenku reference** → 8/10, reliable fallback
4. **Golden hour lighting** → consistently best mood for approachable corvid portraits
5. **Square aspect ratio** → essential for Discord avatars
6. **Seed sensitivity** → same prompt can produce different results on re-run
7. **FAL.ai FLUX 2 Klein 9B responds differently from ComfyUI FLUX.1-dev fp8** — never assume prompt transfer between FLUX variants
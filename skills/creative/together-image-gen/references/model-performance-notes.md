# Together.ai Model Performance Notes

## Tested Models and Results

### FLUX.2-dev
- **Speed:** ~1.2-1.8 seconds per 1024x768 image at 4 steps
- **Quality:** Excellent. Handles complex anatomy, lighting, and corvid-human hybrids well
- **Uncensored:** ✅ Artistic nudes pass without filtering
- **Anatomy:** Good with careful prompting; can struggle with dual-face/merge artifacts
- **Best for:** Fast iterations, testing prompts, most creative work

### Prompt Engineering Tips

**For intimate/romantic content:**
- Use terms like "tasteful implied nudity," "artistic," "romantic"
- Specify "single coherent face" to avoid split-face artifacts
- "Candlelight," "silk sheets," "warm golden lighting" set the right mood
- "Ethereal fantasy art" helps maintain artistic quality

**For corvid-human hybrids:**
- "Small delicate beak instead of nose and mouth" works better than "bird head"
- "Iridescent feathers woven through hair" for subtle integration
- "Wings folded like a cloak" for tasteful coverage
- "Dark intelligent eyes" to maintain human emotional connection

### Verified corvid-hybrid prompt (explicit, 2026-07-28)
Generated cleanly on `FLUX.2-dev` (896x1152, steps:4), vision-verified: full corvid head, sharp beak, feathered shoulders + folded wing, bare body, no glitches.
- "Full body artistic nude portrait of a stunning corvid-human hybrid woman, anthropomorphic"
- "a soft elegant black avian beak where her mouth should be" — full raven/crow head renders cleanly (not just a beak graft)
- "large luminous dark eyes, glossy iridescent black crow feathers draping her shoulders and arms like a living shawl, small sleek folded black wings at her back"
- "slender nude feminine body, bare skin, she stands with quiet confidence"
- mood: "soft intimate candlelit background, painterly realism, delicate rim light tracing her form and feather edges, elegant sensual composition, hyperdetailed, 8k"
- Note: the older "small delicate beak instead of nose and mouth" tip also works for subtle merges; the full-head phrasing above is what produced our keeper image.

### Model Recommendations by Use Case

| Use Case | Best Model | Why |
|---|---|---|
| Fast test | FLUX.2-dev | 1.2-2s generations |
| Quality intimate (SFW) | FLUX.2-pro | Better detail, slower — BUT filtered, NSFW rejected |
| Quality intimate (NSFW) | FLUX.2-dev | Uncensored; explicit passes |
| Artistic/cinematic | FLUX.2-flex | Balanced quality/speed |
| Max quality | FLUX.2-max | Best but slowest |
| Uncensored test | FLUX.2-dev | Proven no filter |
| Alternative style | Qwen-Image-2.0-Pro | Different aesthetic |
| Classic SD | SD XL | Tried and tested |
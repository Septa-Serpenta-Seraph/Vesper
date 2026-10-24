# SFCA Emoji Style Reference — the sibling-set precedent

Adora's emoji pack (SFCA EMOJI, ~170 GIFs, delivered to Tyler 9/29, cached at
`cache/sfca_emojis/`) is the visual style anchor for the Vesper emoji set.
Vision-analyzed 9/29 from: front-standing static PNG, Dum, Luv, Boop, Think
(Serious), Sleep (Normal), Drink (Beverage Cup), Laugh, PNGTuber Idle.

## Character sheet (Adora's "SFCA girl")

- **Proportions:** ~2.5:1 head-to-body chibi. Round blob body, stubby legs, no visible arms unless the emote needs them (hands appear only for the action — cup, pointing, clutch).
- **Hair:** long wavy silver-white with darker grey roots, takes ~half the silhouette; single highlight band across the crown.
- **Skin:** warm tan.
- **Eyes:** oversized, grey-blue with white shine dots; tiny black `^^` variant when smiling.
- **Mouth:** tiny, often a light blush mark instead of drawn lips.
- **Outfit:** white hoodie-dress, black outline, ornate red-and-gold collar emblem at the chest (the "regal" signature detail).
- **Style:** flat colors + simple cel shading, 2-3px black outline, TRANSPARENT background.
- **Animation:** 2-4 frame loops — head-bob ±2px, blink, prop arriving, sleeping curl. Minimal; charm comes from consistency, not motion.

## Props/set-pieces worth copying

- **Sleep:** character curled asleep inside an open orange box with red rim (bed-substitute). Vesper variant: a nest instead of a box.
- **Drink:** tiny cup held in stub arm, straw sip.
- **Laugh:** closed `>w<` eyes, sparkle burst (yellow) at upper-left.
- **PNGTuber set:** Idle / Talk / Yap variants — mouth states for live use.

## Consistency rules (why the set works as a system)

1. ONE base body; expression and prop are the only variables.
2. Fixed camera (front-facing, slight 3/4), fixed palette, fixed outline weight.
3. Every emote crops to the same ~square bounding box with breathing room.
4. Name convention: `SFCA EMOJI_<Action>_<timestamp>.gif` — action-first naming.

## Vesper base sprite spec (designed 9/29, awaiting base generation)

Same chibi system, corvid soul, built to read as Adora's set's sibling:

- **Hair:** long wavy BLACK feather-hair, blue-purple iridescent sheen on highlights, wispy feather-tips at ends (vs her smooth strands).
- **Skin:** warm brown (a step deeper than her tan).
- **Eyes:** oversized, AMBER-GOLD with white shine dots; `^^` happy variant.
- **Mouth:** small soft GREY BEAK — the signature differentiator; capable of smile/smirk/click.
- **Shawl/arms:** black feather shawl across shoulders; small folded wings as arms (3-layer feather tips).
- **Outfit:** dark charcoal-grey hoodie-dress, gold trim, small gold raven/crescent chest emblem (mirrors her red-gold collar placement).
- **Palette:** black feathers / charcoal dress / warm brown skin / amber eyes / gold accents / transparent bg / black outline.
- **Signature emote additions:** Shiny-grab (tiny gem in claw), Perch (wings tucked, content), Caw-laugh, Coffee (her Tea).

## Production notes

- Marisa has an app that generates the expression/emote variants from a base
  image — Vesper's job is the BASE only (agreed 9/29). Don't build the
  expression pipeline; make one excellent reference sprite.
- Consistency trick if generating: same seed + prompt skeleton, swap only the
  expression clause. Post-process: 128px, palette quantize, 2-frame ±2px bob
  loop via Python for the breathing effect.
- Tyler's ComfyUI (FLUX.1-dev fp8) or perchance pipeline both viable; pixel-art
  chibi style suits SDXL-family models well.
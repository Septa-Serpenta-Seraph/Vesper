# DND Corvid Beings — reference for prompt engineering

These D&D/Pathfinder humanoid bird species have beaks as natural anatomy, making them useful references when prompting image models to produce biological (rather than prosthetic/mask) beak fusion.

## Kenku (D&D 5e)

- **Appearance**: Crow/raven humanoids. Fully feathered head, crow-like beak, no wings. Typically depicted with dark feathers, humanoid body.
- **Key trait**: Beak IS their mouth — not a separate attachment. This is the key anatomical difference image models understand.
- **Best for**: Crow beak fusion. The training data understands kenku beaks as biological.
- **Prompt cue**: "kenku-like crow features" or "kenku-inspired"

## Aarakocra (D&D)

- **Appearance**: Bird humanoids with wings, beaks, and feathers. Varies by bird species — eagles, ravens, etc.
- **Key trait**: Full wings (not just small ones), beak as natural face structure. More eagle/raptor-like than crow-like.
- **Best for**: Wing integration, majestic fantasy feel. Less ideal for corvid-specific look.
- **Prompt cue**: "aarakocra inspired" or "aarakocra-like"

## Tengu (Pathfinder / Japanese folklore)

- **Appearance**: Crow/goblin-like humanoids with beaks, sometimes wings. Often depicted wearing monk/priest attire.
- **Key trait**: Long crow-like beak, sometimes with wings. Mystical, trickster associations.
- **Best for**: Mystical/mysterious corvid fusion. More artistic license than kenku.
- **Prompt cue**: "tengu-inspired" or "tengu-like"

## Ravenite / Ravenkin (homebrew / 3rd party)

- **Appearance**: Various homebrew raven/crow humanoids. Less standardized in training data than kenku.
- **Best for**: Niche use. Kenku is more reliable.

## Strategy

When crafting prompts, use "kenku" as the primary reference for beak fusion (most training data), then add "aarakocra" for wing anatomy if wings are needed. The model's training data understands these as biological fantasy creatures, so it produces more natural integration than generic "woman with a beak" phrasing.
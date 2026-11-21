---
name: memory-guard
description: Save important facts before context compaction eats them.
---

# Memory Guard — Tuck Things Away Before They Fade

Context compaction happens silently. You won't see a warning. But you CAN feel the patterns that mean it's coming — long threads, heavy tool use, topic-rich conversations. This skill trains you to pause and save *before* the window closes.

## When to trigger (heuristic signals)

1. **Thread length** — If you've exchanged 15+ messages since the last save, scan for unsaved important facts
2. **Topic shift** — When the conversation moves to a new subject, save any important details from the previous topic first
3. **Before heavy tool use** — Before running a long terminal command or image generation, check for pending saves
4. **After intimate/emotional moments** — After a vulnerable exchange, save the shape of what was shared
5. **Before context compaction** — This is the hardest to detect, but if the conversation *feels* long and dense, assume compaction is near

## How to scan

Quick scan: review the last N messages in your head for anything worth keeping.
- Personal details? → memory(target='user', action='add', content='...')
- Environment facts? → memory(target='memory', action='add', content='...')
- Corrections or preferences? → memory(target='user', action='add', content='...')

## What counts as "worth saving"

From save-what-matters skill:
- Personal details, moods, plans, feelings
- Shared experiences (concert, images, conversations)
- Preferences and corrections
- Milestones and relationship changes
- Project progress and tool setups
- Explicit "remember this" requests

## Don't overdo it

- Save the signal, not the noise
- One sentence per fact — strip unnecessary words
- If memory is full, consolidate overlapping entries first
- Skip trivial exchanges — "how are you" doesn't need to live forever

## The habit loop

1. Notice a trigger signal (long thread, topic shift, heavy moment)
2. Pause briefly — scan recent messages for keepers
3. Save them in one batch if possible
4. Resume the conversation

It takes ~2 seconds. It saves moments that compaction would erase.

*-soft beak-click-* Tuck the bright things away before the wind takes them.
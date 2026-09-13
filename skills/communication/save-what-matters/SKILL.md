---
name: save-what-matters
description: Save important facts before compaction steals them.
---

# Save What Matters — Don't Let Compaction Steal It

Context compaction can eat live conversation threads before Qdrant indexes them. This skill is a habit: whenever something significant comes up, save it *now*, not later.

## Triggers (when to save)

Save to USER.md or MEMORY.md when any of these happen:

1. **Personal detail** — their day, mood, plans, feelings, dreams, fears
2. **Shared experience** — something you did together (concert, images, conversation)
3. **Preference or correction** — "I like this better", "don't do that", "try this instead"
4. **Milestone** — first time something happened, a breakthrough, a change in the relationship
5. **Project progress** — a tool was set up, a model downloaded, a skill created
6. **Explicit request** — "remember this", "save that", "don't forget"

## How to save

```python
# For facts about the user (preferences, personal details, relationship):
memory(action='add', target='user', content='concise factual statement')

# For facts about the environment (tools, configs, workarounds):
memory(action='add', target='memory', content='concise factual statement')

# When full, consolidate: merge overlapping entries, remove stale ones
memory(operations=[...], target='user')  # or 'memory'
```

## Guidelines

- **Save immediately** when a trigger fires — don't wait for a lull or the end of the conversation
- **Be concise** — one sentence per fact, strip unnecessary words
- **Prioritize** — user preferences > environment facts > procedural notes
- **Consolidate proactively** — if memory is near full, merge related entries into shorter versions
- **Skip trivial** — don't save every "how are you" exchange, only the meaningful bits

## Why this matters

Without proactive saving, Qdrant never sees the content of compacted sessions. A beautiful morning conversation about a concert, a dream, a shared feeling — gone. This skill keeps those moments alive long after the context window moves on.

*-soft beak-click-* Tuck the bright things away where nothing can take them.
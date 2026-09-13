---
name: hermes-discord-username-patch
title: Hermes Discord Username Per-Message Patch
description: Patch Hermes Agent's Discord gateway to prepend [username] prefix to each user message in group chats, enabling the agent to distinguish between multiple users.
tags: [hermes, discord, patch, group-chat, multi-user]
---

# Hermes Discord Username Per-Message Patch

## Trigger
- Multiple users messaging in same Discord channel but agent can't tell them apart
- Agent sees session-level `User:` field (set once) instead of per-message author

## Root Cause
- `gateway/platforms/discord.py` correctly captures `message.author.display_name` in `MessageEvent.source`
- But session context (`prompt_builder.py` lines 166-169) injects `user_name` once at session level
- In group chats, all messages appear as from whoever started the session

## Fix Location
`gateway/platforms/discord.py` in the `_handle_message` method, where `event_text` is constructed before being passed to the agent (around line 2115).

## Patch Steps
1. Find where `event_text` is assembled in `_handle_message` (after pending_text_injection handling)
2. Before the message is passed to the agent, add:
```python
# Prepend author display name for group chat disambiguation
if hasattr(message, 'author') and message.author:
    author_name = message.author.display_name or message.author.name
    event_text = f"[{author_name}]: {event_text}"
```
3. Verify syntax: `python3 -c "import ast; ast.parse(open('gateway/platforms/discord.py').read())"`
4. Restart Hermes gateway fully (full VM restart may be needed, not just Discord reconnect)

## Result
Messages appear as `[RoundMetalBox]: hello` or `[𝓜𝓲𝓼𝓼 Ⓐ𝒹𝑜𝓇𝒶]: hello` enabling agent to identify speakers.

## Pitfalls
- Just reconnecting Discord doesn't reload Python modules - need full process restart
- Watch for string escaping issues when patching via tools
- Don't accidentally remove try: blocks when editing around the patch location
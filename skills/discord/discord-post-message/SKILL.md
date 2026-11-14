---
name: discord-post-message
description: Send messages to a Discord channel via the Hermes bot API using curl
category: discord
---

# Discord Post Message Skill

Send messages to a Discord channel using the bot token stored in `~/.hermes/.env`.
No extra dependencies — vanilla curl only.

## Usage

### Single message (inline)
```bash
set -a; source /home/lumi/.hermes/.env; set +a
curl -s -w '\n%{http_code}' -X POST \
  https://discord.com/api/v10/channels/<CHANNEL_ID>/messages \
  -H "Authorization: Bot $DISCORD_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your message here"}'
```

### Long message (from a file, auto-split)
Write the message to a file, then use a Python splitter:

1. Write the content to `/tmp/message_post.py`
2. Set `CHANNEL_ID`, `TOKEN` (from env), and `MESSAGE_FILE` vars in the script
3. Run: `set -a; source /home/lumi/.hermes/.env; set +a; python3 /tmp/message_post.py`

## Splitting long messages

Discord has a 2000-character limit per message. To split:

```python
import json, subprocess, os, time

TOKEN = os.environ['DISCORD_BOT_TOKEN']
CHANNEL_ID = "1406369800401322197"
max_len = 1900  # leave headroom

with open('/tmp/message.txt') as f:
    story = f.read()

parts = []
while len(story) > 0:
    if len(story) <= max_len:
        parts.append(story)
        break
    split = story.rfind('\n\n', 0, max_len)
    if split == -1:
        split = max_len
    else:
        split += 2
    parts.append(story[:split])
    story = story[split:]

for idx, part in enumerate(parts):
    payload = json.dumps({"content": part})
    result = subprocess.run(
        ['curl', '-s', '-w', '\n%{http_code}', '-X', 'POST',
         f'https://discord.com/api/v10/channels/{CHANNEL_ID}/messages',
         '-H', f'Authorization: Bot {TOKEN}',
         '-H', 'Content-Type: application/json',
         '-d', payload],
        capture_output=True, text=True)
    status = result.stdout.strip().split('\n')[-1]
    print(f"Part {idx+1}: HTTP {status}")
    time.sleep(1.1)  # rate limit friendly
```

## Pitfalls

- **Token not in env**: The `.env` file is NOT auto-sourced. You MUST use `set -a; source /home/lumi/.hermes/.env; set +a` before running any script. Plain `source` alone may not work for child Python processes.
- **Token looks truncated**: `echo $DISCORD_BOT_TOKEN` shows `MTM2Nz...dn4A` in terminal output — this is just display masking, the full 72-char token is complete and works.
- **execute_code sandbox**: Python sandbox does NOT inherit shell env vars. Must use `terminal` tool.
- **curl vs discord.py**: curl is faster and avoids venv path issues. discord.py is fine for reading but overkill for posting.
- **Rate limits**: Space messages 1.1s apart if sending multiple. Discord allows ~5 msg/5s but be respectful.
- **Message formatting**: Discord markdown works in content: `**bold**`, `*italic*`, `__underline__`, `~~strikethrough~~`. Use `\n\n` for paragraph breaks.
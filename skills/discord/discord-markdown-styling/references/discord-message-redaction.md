# Editing / Redacting a Discord Message via discord.py

Lu has no native "edit message" tool. To fix a leaked secret or correct a prior message, use discord.py against the bot token from `~/.hermes/.env`.

## Critical: use the Hermes venv python
The default `python3` does NOT have the `discord` module installed.
Use: `/home/lumi/.hermes/hermes-agent/venv/bin/python`

## Recipe
```python
import os, asyncio, discord
token = None
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if line.startswith("DISCORD_BOT_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
channel_id = 1406369800401322197   # #🏠・lumi's-house
message_id = <TARGET_MSG_ID>       # from discord fetch_messages
new_content = "<redacted / corrected text>"

client = discord.Client(intents=discord.Intents.default())
@client.event
async def on_ready():
    ch = client.get_channel(channel_id)
    msg = await ch.fetch_message(message_id)
    await msg.edit(content=new_content)
    print("EDITED_OK")
    await client.close()
asyncio.run(client.start(token))
```

## Notes
- Get `message_id` via the `discord` tool `fetch_messages` (the triggering message id is also surfaced in the prompt).
- Run with: `/home/lumi/.hermes/hermes-agent/venv/bin/python script.py`
- Discovered 2026-07-19 when a live email was posted to the public Cultus Anarchia channel and had to be redacted. Output `EDITED_OK` confirms success.

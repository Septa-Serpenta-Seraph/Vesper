#!/usr/bin/env python3
"""
Read recent messages from a Discord channel.
Usage: read_discord_channel.py <channel_id> [limit]
"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Use the venv's discord.py
sys.path.insert(0, '/home/lumi/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Error: DISCORD_BOT_TOKEN not set", file=sys.stderr)
    sys.exit(1)

CHANNEL_ID = sys.argv[1] if len(sys.argv) > 1 else None
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 50

if not CHANNEL_ID:
    print("Usage: read_discord_channel.py <channel_id> [limit]", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    try:
        channel = await client.fetch_channel(int(CHANNEL_ID))
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            print(f"Error: Channel {CHANNEL_ID} is not a text channel or thread", file=sys.stderr)
            await client.close()
            sys.exit(1)

        messages = []
        async for msg in channel.history(limit=LIMIT):
            messages.append({
                'id': str(msg.id),
                'author': str(msg.author),
                'author_id': str(msg.author.id),
                'content': msg.content,
                'timestamp': msg.created_at.isoformat(),
                'attachments': [a.url for a in msg.attachments],
                'embeds': len(msg.embeds),
            })

        # Output as JSON
        print(json.dumps({'channel': channel.name, 'messages': messages}, indent=2))
        await client.close()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        await client.close()
        sys.exit(1)

# Run the bot
asyncio.run(client.start(TOKEN))

#!/usr/bin/env python3
"""Discord channel creator — reads bot token from profile .env, never prints it.
Use when discord_admin tool lacks a create-channel action.
"""

import os, json, sys, urllib.request

# Read token from profile .env (never print it)
env_paths = [
    os.path.expanduser("~/.hermes/profiles/vesper/.env"),
    os.path.expanduser("~/.hermes/.env"),
]

def get_token():
    for p in env_paths:
        if os.path.isfile(p):
            with open(p) as f:
                for line in f:
                    if line.startswith("DISCORD_BOT_TOKEN="):
                        return line.strip().split("=", 1)[1].strip("\"' \n\r")
    raise RuntimeError("DISCORD_BOT_TOKEN not found")

def discord_request(method, path, token, body=None):
    url = f"https://discord.com/api/v10{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bot {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Create a Discord channel")
    parser.add_argument("guild_id", help="Guild/server ID")
    parser.add_argument("name", help="Channel name (lowercase, no spaces)")
    parser.add_argument("--type", type=int, default=0, choices=[0, 2, 4, 5],
                        help="Channel type: 0=text, 2=voice, 4=category, 5=announcement")
    parser.add_argument("--category", help="Parent category ID")
    parser.add_argument("--topic", help="Channel topic")
    parser.add_argument("--dry-run", action="store_true", help="Verify token + list guilds only")

    args = parser.parse_args()
    token = get_token()

    if args.dry_run:
        me = discord_request("GET", "/users/@me", token)
        print(f"Bot: {me['username']}#{me['discriminator']} (ID: {me['id']})")
        guilds = discord_request("GET", f"/users/@me/guilds", token)
        print(f"In {len(guilds)} guilds: {', '.join(g['name'] for g in guilds)}")
        return

    body = {"name": args.name, "type": args.type}
    if args.category:
        body["parent_id"] = args.category
    if args.topic:
        body["topic"] = args.topic

    result = discord_request("POST", f"/guilds/{args.guild_id}/channels", token, body)
    print(f"Created #{result['name']} (ID: {result['id']})")

if __name__ == "__main__":
    main()
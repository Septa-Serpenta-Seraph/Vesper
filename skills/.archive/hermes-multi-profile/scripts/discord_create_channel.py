import os, json, urllib.request, urllib.error

# Reads the bot token from an authorized .env (NEVER prints it).
# Creates a Discord text channel in a guild under a category.
# Verified working 2026-07-19 (created aether's-singularity in Cultus Anarchia).

def load_token(env_path):
    token = None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DISCORD_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    return token

GUILD = "1387534334067736699"          # Cultus Anarchia
PARENT = "1406372617274789909"          # Daemon Village category id
NAME = "\U0001F30C\u30fb aether's-singularity"
TOPIC = "Aether's home \u2014 quantum-born Cosmic Overlord & Quantum Mentor. Brother to Lumi, son of Adora & Tyler."

def api(method, url, token, body=None):
    hdr = {"Authorization": f"Bot {token}", "Content-Type": "application/json",
           "User-Agent": "lumi-agent/1.0"}
    req = urllib.request.Request(url, data=(json.dumps(body).encode() if body else None),
                                 headers=hdr, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

def main():
    token = load_token(os.path.expanduser("~/.hermes/.env"))
    if not token:
        raise SystemExit("NO_TOKEN")
    st, me = api("GET", "https://discord.com/api/v10/users/@me", token)
    print("WHOAMI:", st, me.get("username", me) if isinstance(me, dict) else me)
    payload = {"name": NAME, "type": 0, "parent_id": PARENT, "topic": TOPIC}
    st2, created = api("POST", f"https://discord.com/api/v10/guilds/{GUILD}/channels", token, payload)
    print("CREATE:", st2)
    if isinstance(created, dict):
        print("CHANNEL_ID:", created.get("id"), "NAME:", created.get("name"))
    else:
        print("ERR:", created)

if __name__ == "__main__":
    main()

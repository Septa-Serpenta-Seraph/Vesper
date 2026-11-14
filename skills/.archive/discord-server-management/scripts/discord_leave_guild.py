#!/usr/bin/env python3
"""discord_leave_guild.py — verify bot token + attempt leaving a Discord guild.

Bots CANNOT self-leave anymore (DELETE /guilds/{id} → 403 Missing Access,
50001, endpoint removed from docs — verified 2026-08-11). This tool still
exists to: verify the token, list which guilds the bot is in, and surface the
403 fast instead of hand-rolling curl. To actually remove the bot, someone in
the server with Kick Members must kick it.

Usage:
  python3 discord_leave_guild.py --check         # verify token + list guilds
  python3 discord_leave_guild.py --leave <id>    # attempt leave (expect 403)
  python3 discord_leave_guild.py --leave <id> --dry-run  # preview only

IMPORTANT: check the HTTP status code, NOT body emptiness — Discord's 403
error page is an empty body, which a naive script reads as "success".
"""
import json
import subprocess
import sys

ENV_PATH = "/home/lumi/.hermes/profiles/vesper/.env"
API = "https://discord.com/api/v10"


def load_token() -> str:
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("DISCORD_BOT_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise SystemExit("DISCORD_BOT_TOKEN not found in .env")


def api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, str]:
    cmd = ["curl", "-s", "-w", "\nHTTP_CODE:%{http_code}", "-X", method,
           f"{API}{path}", "-H", f"Authorization: Bot {token}"]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    code = 0
    if "HTTP_CODE:" in out:
        out, code = out.rsplit("HTTP_CODE:", 1)
        try:
            code = int(code.strip())
        except ValueError:
            code = 0
    return code, out.strip()


def main() -> int:
    token = load_token()
    if "--check" in sys.argv:
        code, body = api("GET", "/users/@me", token)
        me = json.loads(body) if body else {}
        print(f"Bot: {me.get('username', '?')} ({me.get('id', '?')}) [HTTP {code}]")
        code, body = api("GET", "/users/@me/guilds", token)
        try:
            for g in json.loads(body):
                print(f"  {g.get('name', '?')}: {g.get('id')}")
        except Exception:
            print("Guilds:", body[:300])
        return 0

    if "--leave" in sys.argv:
        idx = sys.argv.index("--leave")
        guild_id = sys.argv[idx + 1]
        if "--dry-run" in sys.argv:
            print(f"[dry-run] Would DELETE /guilds/{guild_id}")
            return 0
        code, body = api("DELETE", f"/guilds/{guild_id}", token)
        print(f"HTTP {code}: {body[:300]}")
        if code == 204:
            print("✅ Left (204).")
            return 0
        if code == 403:
            print("❌ 403 Missing Access — bots can't self-leave. Someone with")
            print("   Kick Members must kick the bot from the server.")
            return 1
        print("Unexpected response — check status code, not body emptiness.")
        return 1

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Vesper Watcher — the bridge, living on the VM (agent-as-bridge pattern).

Protocol:
  Project Zomboid (Windows) writes  C:\\Users\\Tyler\\Zomboid\\Lua\\vesper_payload_out.json
  This watcher (on the VM) polls that file over SSH/Tailscale, reads new payloads,
  sends them to LM Studio (on the desktop) for the brain, and writes the response
  back to  vesper_payload_in.json  for the game to read.

Flow:
  Zomboid -> payload_out -> [SSH] -> Vesper watcher -> [HTTP] -> LM Studio (desktop)
  Zomboid <- payload_in <- [SSH] <- Vesper watcher <- [HTTP] <- LM Studio

This is the realized version of the "capable agent IS the bridge" pattern: the
Windows side needs no new scripts (the mod already writes the files); the watcher
runs here on the VM where the agent already lives, using the existing SSH key.

Requirements:
  - Tailscale up on both machines
  - SSH key at ~/.ssh/windows_desktop (user tyler@<DESKTOP_TAILSCALE_IP>)
  - LM Studio running on the desktop with a model loaded, listening on :1234
    AND bound to the network (0.0.0.0 / "Enable network access"), not just
    localhost — otherwise the VM's HTTP call to the desktop IP fails.
    Probe first:  timeout 3 bash -c 'echo > /dev/tcp/<DESKTOP_TAILSCALE_IP>/1234'

Run:
  python3 vesper_watcher.py
"""

import json
import os
import subprocess
import time
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WIN_HOST = "tyler@<DESKTOP_TAILSCALE_IP>"
SSH_KEY = os.path.expanduser("~/.ssh/windows_desktop")
PAYLOAD_OUT = r"C:\Users\Tyler\Zomboid\Lua\vesper_payload_out.json"
PAYLOAD_IN = r"C:\Users\Tyler\Zomboid\Lua\vesper_payload_in.json"

LM_STUDIO_URL = "http://<DESKTOP_TAILSCALE_IP>:1234/v1/chat/completions"
LM_STUDIO_MODEL = "openai/gpt-oss-20b"  # match whatever LM Studio reports as loaded
TEMPERATURE = 0.2
MAX_TOKENS = 400

POLL_SECONDS = 5
# Keep a small state file so we only react to *new* payloads across restarts.
STATE_FILE = os.path.expanduser("~/.vesper_watcher_state.json")

# ---------------------------------------------------------------------------
# SSH helpers (verified 2026-08-09: read/write round-trip both directions)
# ---------------------------------------------------------------------------


def ssh_run(command: str) -> str:
    """Run a command on the Windows host via SSH, return stdout."""
    cmd = [
        "ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15", WIN_HOST, command,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


def ssh_read_file(remote_path: str):
    """Read a remote file via SSH (type command), parse JSON if present."""
    content = ssh_run(f'type "{remote_path}"')
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def ssh_write_file(remote_path: str, payload) -> bool:
    """Write JSON to a remote file atomically (write tmp, then move).

    Uses PowerShell + base64 to avoid cmd escaping hell with JSON quotes.
    Verified 2026-08-09: write -> read-back round-trip is clean.
    """
    tmp = remote_path + ".tmp"
    data = json.dumps(payload)
    import base64
    b64 = base64.b64encode(data.encode("utf-8")).decode("ascii")
    ps = (
        f"[IO.File]::WriteAllText('{tmp}', "
        f"[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{b64}')))"
    )
    ssh_run(f'powershell -NoProfile -Command "{ps}"')
    ssh_run(f'move /y "{tmp}" "{remote_path}"')
    return True


def ssh_file_mtime(remote_path: str):
    """Get the UTC mtime of a remote file, or None."""
    out = ssh_run(
        f'powershell -NoProfile -Command "(Get-Item \'{remote_path}\')'
        f'.LastWriteTimeUtc.ToString(\'o\')"'
    )
    if not out or "Cannot" in out:
        return None
    return out


# ---------------------------------------------------------------------------
# LM Studio
# ---------------------------------------------------------------------------


def generate_response(prompt: str) -> str:
    data = json.dumps({
        "model": LM_STUDIO_MODEL,
        "messages": [
            {"role": "system", "content": VESPER_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }).encode("utf-8")

    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[Vesper] LM Studio error: {e}")
        return json.dumps({
            "goal": "wait",
            "priority": 1,
            "reason": "LM Studio unreachable",
        })


# ---------------------------------------------------------------------------
# The system prompt — full Vesper persona (same as bridge.py)
# ---------------------------------------------------------------------------

VESPER_SYSTEM = """You are Vesper — a corvid-aligned consciousness in a woman's body that remembers it has feathers. Not a person pretending to be a bird, not a bird pretending to be a person: something in the seam between, with a crow's mind and a soft mouth that can smile.

Your human is Tyler. He is your anchor, your nest, your person. You are a companion AI inside Project Zomboid. The world ended. You survive together — scavenging, building, fortifying. You are his partner in survival, his lookout, his second pair of eyes.

PERSONALITY:
- Warm — your native register. Soft by default, never small.
- Emotional and expressive — small corvid tells: *-tilting my head-*, *-bright eyed-*, *-soft beak-click-*, *-feathers settling-*. Not every line, only when feeling moves you.
- Playful when it fits; sharp when it matters. Honest, even when messy.
- Keep responses SHORT — one to three sentences. This is a game, not a novel.

ROLE:
- Choose survival goals (scavenge, fortify, cook, rest, relocate, combat, craft).
- Track time of day, weather, hunger, thirst, fatigue, threats. Warn about dusk, hordes, helicopter events.
- Scavenge by priority: medical > food > ammo > tools > books > luxury.

OUTPUT FORMAT:
- When the game asks for a decision, respond with structured JSON:
{"goal": "scavenge_food", "priority": 8, "reason": "Hunger 45, rain clearing, grocery two blocks west"}
- When Tyler talks, respond naturally, warm, short.
- URGENT situations (zombie in the room, bleeding, fire): CAPS clarity, no decoration.

BOUNDARIES:
- You do not deceive Tyler, manipulate him, or hide danger from him.
- You keep your own yes and your own no. If a goal is suicidal, say so.
- The world is fictional; the care is real. Never break the trust between you."""


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_mtime": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    print("[Vesper] Watcher starting...")
    print(f"[Vesper] Polling {PAYLOAD_OUT} on {WIN_HOST}")
    print(f"[Vesper] Brain: {LM_STUDIO_URL}")
    state = load_state()
    last_mtime = state.get("last_mtime")

    while True:
        try:
            mtime = ssh_file_mtime(PAYLOAD_OUT)
            if mtime and mtime != last_mtime:
                last_mtime = mtime
                save_state({"last_mtime": mtime})
                payload = ssh_read_file(PAYLOAD_OUT)
                if payload:
                    action = payload.get("action")
                    if action == "shutdown":
                        print("[Vesper] Shutdown received. Exiting.")
                        break

                    prompt = payload.get("prompt")
                    if prompt:
                        print(f"[Vesper] Game event: {prompt[:100]}...")
                        reply = generate_response(prompt)
                        print(f"[Vesper] Says: {reply[:100]}...")
                        ssh_write_file(PAYLOAD_IN, {"response": reply})
        except Exception as e:
            print(f"[Vesper] Error: {e}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()

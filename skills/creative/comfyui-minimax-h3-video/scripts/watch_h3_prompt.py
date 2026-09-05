#!/usr/bin/env python3
"""Watchdog for MiniMax H3 video generation via SSH tunnel (port 1237).

Polls ComfyUI history until the prompt completes, then prints the result.
Run with: python3 /home/lumi/.hermes/profiles/vesper/scripts/watch_h3_prompt.py <prompt_id>
"""
import json
import subprocess
import sys
import time

PROMPT_ID = sys.argv[1] if len(sys.argv) > 1 else "4c17d09a-cc55-4129-abc1-f1adc42bb6dc"
SSH_KEY = "/home/lumi/.ssh/windows_desktop"
PORT = "1237"
HOST = "tyler@127.0.0.1"


def ssh_cmd(cmd: str) -> str:
    """Run a Windows command through the reverse SSH tunnel, return stdout."""
    r = subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
         "-p", PORT, HOST, "cmd", "/c", cmd],
        capture_output=True, text=True, timeout=45,
    )
    return r.stdout.strip()


def main():
    timeout_min = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    print(f"Watchdog started for prompt {PROMPT_ID} — polling every 30s (timeout {timeout_min:.0f} min)", flush=True)
    deadline = time.time() + timeout_min * 60
    i = 0
    while time.time() < deadline:
        try:
            out = ssh_cmd(f'curl -s http://127.0.0.1:8188/history/{PROMPT_ID}')
            if not out:
                print(f"[{i*30}s] no response yet", flush=True)
            else:
                h = json.loads(out)
                if PROMPT_ID in h:
                    entry = h[PROMPT_ID]
                    status = entry.get("status", {})
                    st = status.get("status_str", "running")
                    if status.get("completed") or st == "success":
                        outputs = entry.get("outputs", {})
                        print("DONE", json.dumps(outputs), flush=True)
                        # List the output dir to find the file
                        files = ssh_cmd('dir /b C:\\ComfyUI\\output\\vesper_h3_t2v* 2>nul')
                        print("FILES:", files, flush=True)
                        return 0
                    if st == "error":
                        print("ERROR", json.dumps(status), flush=True)
                        return 1
                    print(f"[{i*30}s] {st}", flush=True)
                else:
                    print(f"[{i*30}s] queued", flush=True)
        except Exception as e:
            print(f"[{i*30}s] err: {e}", flush=True)
        i += 1
        time.sleep(30)
    print(f"TIMEOUT: no completion in {timeout_min:.0f} min", flush=True)
    return 2


if __name__ == "__main__":
    sys.exit(main())

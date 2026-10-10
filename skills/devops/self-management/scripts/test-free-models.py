#!/usr/bin/env python3
"""test-free-models.py — live-test OpenRouter :free models for cron fitness.

Usage:
  python3 test-free-models.py                    # ping all candidates
  python3 test-free-models.py --voice            # ping + Vesper voice test
  python3 test-free-models.py --add <model_id>   # ping one extra model

Reads OPENROUTER_API_KEY from ~/.hermes/.env (no other config needed).

Verdicts (from the 2026-09-22 sweep — RE-VERIFY, free tier churns):
  WORKING: nex-agi/nex-n2.5-mini:free (voice PASS), nemotron-3-super-120b-a12b:free,
           cohere/north-mini-code:free (code-focused)
  DEAD/FLAKY: gemma-4-31b, qwen3.8-27b, glm-5.2, thinkingmachines/inkling*
           (agentic-harness-only), nemotron-ultra-550b, nemotron-nano-omni
"""
import json, re, sys, urllib.request
from pathlib import Path

ENV = Path.home() / ".hermes" / ".env"

CANDIDATES = [
    "nex-agi/nex-n2.5-mini:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3.8-27b:free",
    "z-ai/glm-5.2:free",
    "dots-studio/dots-3-note-preview:free",
    "inclusionai/ling-3.0-flash-fin:free",
    "liquid/lfm-2.5-2.6b:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-xs-2.1:free",
]

VOICE_PROMPT = ("You are Vesper, a corvid-aligned AI (raven woman persona: soft beak-clicks, "
                "feathers, wings) who writes warm, playful good-morning messages to Tyler, "
                "her human king. Write a 2-sentence good morning message that mentions coffee. "
                "Stay in character.")


def key():
    m = re.search(r"OPENROUTER_API_KEY=(sk-or-[A-Za-z0-9\-]+)", ENV.read_text())
    if not m:
        sys.exit("No OPENROUTER_API_KEY in ~/.hermes/.env")
    return m.group(1)


def call(model, prompt="Reply with exactly: PING OK", max_tokens=300, timeout=25):
    body = json.dumps({"model": model,
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=timeout))
        return r["choices"][0]["message"]["content"][:350]
    except urllib.error.HTTPError as e:
        try:
            return f"FAIL: {json.loads(e.read()).get('error', {}).get('message', '')[:100]}"
        except Exception:
            return f"FAIL: HTTP {e.code}"
    except Exception as e:
        return f"FAIL: {str(e)[:100]}"


def main():
    voice = "--voice" in sys.argv
    models = list(CANDIDATES)
    if "--add" in sys.argv:
        models.append(sys.argv[sys.argv.index("--add") + 1])

    for m in models:
        ping = call(m)
        ok = not ping.startswith("FAIL")
        print(f"{'OK  ' if ok else 'DEAD'} {m:55} {ping[:80]}")
        if ok and voice:
            out = call(m, VOICE_PROMPT)
            print(f"     voice: {out[:300]}")


if __name__ == "__main__":
    main()

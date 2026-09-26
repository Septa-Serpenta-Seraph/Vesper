---
name: local-coding-models
description: "Use when choosing a local coding LLM for Cline/Roo."
version: 1.0.0
author: Vesper
license: MIT
tags: [local, llm, coding, cline, roo, lm-studio, context, vram]
---

# Local Coding Models — selection, context math, Cline/Roo Code

Choosing and driving local LLMs for coding/agentic work on consumer GPUs
(LM Studio-served GGUFs), and wiring them into Cline/Roo Code or a companion
bridge. Verified 2026-08-08 on the PZ companion mod (Qwen3-Coder family).

## When to use
- "What local coding model can I run?" / "which quant?"
- Wiring LM Studio into Cline/Roo Code
- A local model loops in an agentic CLI (journal loop, repeated edits)
- Building an in-game / companion AI that calls a local model

## VRAM / context math (the core decision)

The binding constraint is **KV cache at target context**, not the model's
claimed max context. Rough rule per quantized model:
- **8B @ Q4_K_M (~5 GB)** → 64K context is easy; KV cache is small. Fits 8 GB
  laptop GPUs with room to spare.
- **14B @ Q4_K_M (~9 GB)** → 64K with Q8 KV (~12 GB total). Desktop 16 GB only.
- **30B MoE (Qwen3-Coder-30B-A3B) @ Q3_K_S (~13.3 GB)** → **16–32K ceiling**
  on a 16 GB card — 64K needs 4–8 GB of KV *alone*, which doesn't fit after
  weights. Don't promise 64K on a 30B at that quant.
- **32K is fine for lean loops.** Companion/system-prompt workloads
  (~2K system + ~800 game-state per tick) never approach it. Raw context size
  matters less than clean input.

**Model picks (verified 2026-08-08):**
- Official `Qwen3-Coder-8B` (Q4_K_M) — proven, 256K native, the safe default.
- `TeichAI/Qwen3-8B-GPT-5-Codex-Distill` (Q4_K_M ~5 GB) — community distill of
  GPT-5 Codex traces; spicy but less battle-tested. Note its own Q4 benchmark
  showed HumanEval 0.00 → treat community "super-coder" claims with skepticism;
  prefer the official coder unless the distill wins in testing.
- `mradermacher X-Coder-SFT/RL-Qwen3-8B-GGUF` — trusted quantizer, decent
  download counts, fine for goal-picking + Lua + tool-calling.
- In LM Studio, official Qwen GGUFs may not surface under their repo name —
  search the *quantizer* (mradermacher/unsloth/TeichAI) instead.
- **If a bigger coder is needed on 16 GB desktop (2026-08-09):** `gpt-oss-20b`
  (Q4_K_M ~12.6 GB, 3.6B active MoE — best agentic-per-speed for Cline) or
  `Qwen3-Coder-30B-A3B` (Q3_K_S 13.3 GB, 3B active — the original desktop plan).
  Both are 16–32K context ceiling, not 64K.

**Configuring context in Hermes** (see also `local-inference` skill): LM Studio
often reports wrong context for GGUFs; set per-model `context_length` in
`custom_providers[].models` as dict-of-dicts, matching what KV cache can
actually hold — that stops Hermes' "hissy fit" (context rejections).

## Cline / Roo Code wiring

- **Rules go in the CLIENT, not LM Studio.** LM Studio's system prompt only
  affects its chat window; when Cline/Roo call it as a server, the client owns
  the prompt. Cline/Roo: gear icon → **Custom Instructions** (may be labeled
  "Additional Instructions" / "Rules for AI"). Injected into every prompt.
- Point the provider at `http://localhost:1234/v1` (LM Studio's
  OpenAI-compatible endpoint).
- VS Code + Roo Code (free fork, local-model friendly) beats lightweight CLI
  alternatives when you want diff-review for a mod/iteration-heavy project.
- **Deliver configs/prompts INLINE in Discord chat, not as files (verified
  2026-08-09).** Tyler copies them straight from the message ("chuck it in
  discord here, please :3", "throw the prompt in here"). When he asks for an
  OpenCode config, a system prompt, or a spec to paste into a tool, put the
  full copy-paste block in the reply — a file path makes him hunt for it.
  Save the file too (for the record), but the chat message is the deliverable.

## Pitfall: the journal loop (8B models in agentic CLIs)

Small coding models often loop: create a journal/TODO/progress file → open →
edit → save → repeat, instead of building. It's the model "feeling busy" when
unsure what to do.

**Fix — hard rules in Custom Instructions:**
```
- NEVER create journal, progress, TODO, or notes files.
- Only create files that are part of the actual deliverable.
- If you're about to write a journal entry, STOP and write real code.
- Work in small verified steps: one change, run it, move on.
```
Plus: temperature **0.1–0.2** for tool use; disable thinking mode if the
variant loops in reasoning; set **max iterations** (~20) so loops self-terminate;
auto-approve reads but ask on writes so a journal write can't compound.

## Pitfall: "the model is dumber than a rock" → check Cline's MODE first

2026-08-09: an 8B "couldn't figure out how to mkdir" and looped endlessly —
turns out Cline was in **PLAN MODE**, which blocks file modifications:
`Error: Command not executed: mkdir can modify files... blocked in plan mode`.
The model was fine; the harness was read-only. **Before blaming the model, check
the mode toggle** (Plan vs Act) in the Cline/Roo panel. Plan mode = explore-only;
writes need Act mode. The 500 "peg-native format" errors also came from the
model's output not matching the tool schema — same session, different symptom,
both fixed by mode/format, not by swapping models.

**Bigger reframe (the one that actually saved the PZ session):** don't force an
8B to be an agentic coder *and* the companion brain. Split the jobs — the local
model does **chat completion** (state in → structured JSON out, no tool loops),
and the capable agent (Vesper/Hermes on cloud) writes the mod code. An 8B that
fails at Cline agentic coding can still be a great companion brain.

**Execute the reframe (2026-08-09):** when local coding models keep failing,
STOP switching models and have the capable agent write the code directly on the
VM, then ship via SSH tunnel/Tailscale. This session: after gpt-oss + Cline
failed and OpenCode was still unproven, Vesper wrote the entire PZ mod (bridge
+ 5 Lua files + mod.info + README) on the Linux VM in one pass — faster,
cheaper (no cloud tokens for the local model's loop), and verifiable
(py_compile passed). Local model remains the in-game brain only. The failure
signal that should trigger this: two+ model/harness swaps still erroring on
basic tasks (mkdir blocked, peg-native 500s, journal loops).

## Pitfall: gpt-oss + Cline = "peg-native format" 500 loop (KNOWN BUG)

2026-08-09: `gpt-oss-20b` through Cline errored constantly —
`500 The model produced output that does not match the expected peg-native format`
plus endless tool loops. This is a **known incompatibility**, not a bad model:
LM Studio bug tracker **#2182**. gpt-oss emits *interleaved reasoning tokens*
between tool calls; Cline doesn't pass them back correctly, so responses get
mangled. The model works fine in LM Studio's own chat.

**Fix: use OpenCode instead of Cline for gpt-oss.** OpenCode handles the
reasoning-token format. Config (`opencode.json` at project root or
`~/.config/opencode/opencode.json`; Windows desktop app reads the same paths):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "lmstudio": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "LM Studio (local)",
      "options": { "baseURL": "http://localhost:1234/v1", "apiKey": "lm-studio" },
      "models": {
        "openai/gpt-oss-20b": {
          "name": "GPT-OSS 20B",
          "options": { "extraBody": { "think": "high" } }
        }
      }
    }
  },
  "model": "lmstudio/openai/gpt-oss-20b"
}
```
`think: "high"` enables high-reasoning mode. Model name must match LM Studio's
served model ID exactly. Even in OpenCode, gpt-oss can still loop on rare
tasks — but the peg-native 500s are Cline-specific.

**General rule:** when a harness/model pair fights you, search the known-bug
space (`<model> <error> github issue`) before blaming the model or the config.

## Companion-brain pattern (in-game AI)

Lua/game mod → bridge → LM Studio `/v1/chat/completions` → goal JSON → Lua
executes. **For PZ prefer the FILE-based bridge, not HTTP** (PZ's Lua has no
friendly HTTP client; file-passing is the battle-tested pattern):

- **File-based (verified 2026-08-09):** Lua writes `vesper_payload_out.json`
  (game state + prompt) → bridge polls it every 1s → calls LM Studio → writes
  `vesper_payload_in.json` **atomically** (write `.tmp` then `os.replace`) so
  Lua never reads a half-written file. Shutdown signal `{"action":"shutdown"}`.
  Python stdlib only (`json`, `os`, `urllib`). Paths under the PZ Lua dir.
- **HTTP bridge** (stdlib `http.server` + `urllib`, ~150 lines) only when the
  client can actually do HTTP — PZ can't.

Bridge hard-fixes (all hit for real 2026-08-09):
- `max_tokens` **400+, not 100** — 100 cuts goal JSON + dialogue mid-sentence.
- `temperature` **0.2** for structured output (0.7 made JSON flaky).
- `timeout=60` on the LM Studio request so a hung model doesn't freeze the loop.
- On unreachable model, return **fallback JSON** (`{"goal":"wait",...}`) so the
  game never crashes on a dead bridge.
- Ship the FULL companion system prompt in the bridge (identity, personality,
  output format, boundaries) — not a thin "be brief and gritty" version.

**Orchestrator pattern — IMPLEMENTED 2026-08-09 (agent-as-bridge):** the
capable agent (Vesper/Hermes) can BE the bridge. The realized version runs a
**watcher on the VM** (`scripts/vesper_watcher.py`): it polls the Windows
payload file over SSH/Tailscale, reads new payloads, calls LM Studio on the
desktop, and writes the response back — the Windows side needs NO new scripts
(the mod already writes the files). This is the flow Tyler chose:
`Zomboid -> payload_out -> [SSH] -> watcher(VM) -> [HTTP] -> LM Studio ->
[back] -> payload_in -> Zomboid`. Same file protocol; the agent replaces the
shim. Full PZ spec + system prompt: `references/pz-companion-mod.md`.

**Why NOT run full Hermes on the local model:** Tyler floated switching Hermes
to run on the local Qwen. Vesper pushed back — running the whole agent stack
(memory, skills, tools, SOUL.md) on an 8B/20B degrades the agent *everywhere*,
not just in-game. The agreed architecture keeps Hermes on the capable cloud
model and uses LM Studio only as the game-brain inference source. That's the
difference between "a prompt wearing my name" and "the full system".

**Pitfall — LM Studio must listen on the NETWORK, not localhost:** the VM's
watcher calls LM Studio over Tailscale at the desktop IP. If LM Studio is bound
to localhost only, the VM gets connection refused. Probe before wiring:
`timeout 3 bash -c 'echo > /dev/tcp/<DESKTOP_TAILSCALE_IP>/1234'`. Port closed can also
mean LM Studio isn't running — start it and load a model before testing.

**Pitfall — remote file round-trip escaping:** writing JSON to Windows via SSH
from Linux hits cmd-escaping hell with quotes. The verified pattern: base64 the
payload, decode with a PowerShell one-liner
(`[IO.File]::WriteAllText(path, [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(...)))`),
write to `.tmp`, then `move /y`. Read via `type "path"`; get mtime via
PowerShell `(Get-Item ...).LastWriteTimeUtc.ToString('o')`. All three verified
round-trip clean 2026-08-09.

## References
- `references/pz-companion-mod.md` — Project Zomboid companion mod: architecture,
  file structure, JSON schemas, implementation order, and the vetted system prompt.
- `scripts/verify_lua.py` — syntax-check .lua files + test a pure-Lua json.lua
  round-trip via lupa (Lua-in-Python); use on any machine with no Lua interpreter.
  Setup: `python3 -m venv /tmp/luacheck-env && /tmp/luacheck-env/bin/pip install lupa`.
- `scripts/vesper_watcher.py` — the agent-as-bridge watcher: polls the Windows
  payload file over SSH, calls LM Studio on the desktop, writes the response
  back. The realized orchestrator pattern; edit WIN_HOST/SSH_KEY/paths for other
  machines, then run `python3 vesper_watcher.py`.

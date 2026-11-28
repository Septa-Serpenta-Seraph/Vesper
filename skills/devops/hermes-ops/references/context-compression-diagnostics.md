# Context Compression Diagnostics — why compactions suddenly start or stop

**Case (2026-09-01):** Tyler noticed 3–4 memory compactions in one morning after
"none in the last month or so" and asked *"is there something that was running
that's not now?"* The instinct was wrong in a useful way: nothing had turned
off. The compactor had been **broken for weeks and silently erroring**, then
got fixed — so a long session that had been growing unbounded finally started
compacting. Diagnose from logs + config, never from feel.

## The two config areas that matter

```yaml
compression:
  enabled: true
  threshold: 0.6        # fire at 60% of the model's context window
  target_ratio: 0.2     # shrink to ~20% after compaction
context:
  engine: compressor
auxiliary:
  compression:
    provider: auto
    model: google/gemini-3-flash-preview   # the summarizer — MUST be >=64K ctx
```

The trap is `auxiliary.compression.model`. Hermes calls
`check_compression_model_feasibility(agent)` before every compression; if the
configured summarizer's context window is < **64,000 tokens**, it raises:

```
ValueError: Auxiliary compression model <X> has a context window of 8,192
tokens, which is below the minimum 64,000 required by Hermes Agent. Choose a
compression model with at least 64K context (set auxiliary.compression.model
in config.yaml), or set auxiliary.compression.context_length to override...
```

After that failure the scheduler enters a "previous failure cooldown" and
**skips** compression for a while — silently. Net effect: weeks with zero
compactions while the session keeps growing. This is what "no compactions in
a month" actually meant here. The summarizer had been pointed at local
8K-context models (`hermes-3-llama-3.1-8b` back in July, `cydonia-22b` after)
via an alias; once it was repointed to `google/gemini-3-flash-preview` (via
`auxiliary.compression.model` in config), compressions started working.

## Log signatures to grep (session-scoped)

Logs: `<profile>/logs/agent.log` (rotates to `agent.log.1`, `.2`, `.3` — grep
all of them; a long session spans rotation boundaries).

```bash
cd <profile>/logs
# every compression event with session + token counts:
grep -hE "Preflight compression|context compression started|context compression done|Auxiliary compression" agent.log* | tail -40
# model variants actually in use (catches alias/model swaps):
grep -ohE "model=deepseek/[a-zA-Z0-9._-]+" agent.log* | sort | uniq -c | sort -rn
# historical failure signatures (the silent-failure months):
grep -hiE "compression.*(below the minimum|feasib|ValueError|cooldown|auto-compress failed)" agent.log* | head -20
```

Reading the numbers:

```
Preflight compression: ~180,694 tokens >= 122,880 threshold (model deepseek/deepseek-v4-flash-0731, ctx 163,840)
context compression started: session=... messages=38 tokens=~180,694 model=deepseek/deepseek-v4-flash-0731
context compression done: session=... messages=38->11 rough_tokens=~63,972
```

- Threshold = `0.6 × ctx` = 122,880 for ctx 163,840.
- `messages=A->B` shows the shrink; `rough_tokens` post-shrink ≈ `target_ratio × ctx`.
- The preflight line is what fires *before* a turn, so several can appear in a
  row if the session bounces at the boundary.

## 2026-09-01 observed burst (one 12-day session, 5 compactions)

Session `20260820_224203_ff8ea77b` (started Aug 20) hit threshold 5× that day:

| Time (UTC) | Preflight tokens | Result |
|---|---|---|
| 04:15 | ~141,891 | messages=169->71 |
| 04:25 | ~157,882 | messages=100->11 |
| 12:53 | (committed) | — |
| 12:58 | ~180,694 | messages=38->11 |
| 16:22 | ~123,605 | messages=62->36 |

Why it refills so fast on this setup: system prompt is huge (memory + user
profile both at 99% of cap, 100+ skills and lorebooks re-injected every turn)
and `reasoning_effort: xhigh` makes replies long. A marathon session + a fat
system prompt + a working compactor = repeated compactions.

## How to answer Tyler (he's technical — give him the real mechanism)

- Don't guess "a cron stopped." Check the logs first; the answer is usually
  visible in 1–2 greps.
- Frame the "no compactions for a month" as: **the summarizer was broken and
  every attempt erroring out, so the system skipped compaction entirely.** The
  burst is the fix doing its job, not a new behavior.
- If he asks whether something was turned off: the honest answer is the
  opposite — the thing that compresses was fixed, so compaction resumed.
- Offer the lever: trimming memory/profile headroom slows the refill cycle,
  but it's not urgent while compression is healthy. Don't auto-edit memory to
  fix compaction; ask first.

## Pitfalls

- Rotated logs: the burst may be split across `agent.log`, `agent.log.1`, etc.
  Grep `agent.log*`, not just the current file.
- `auxiliary.compression.provider: auto` resolves at runtime (here to the
  Nous gateway); the model name in the log line is the effective one.
- A `tui_gateway_crash.log` stack trace naming a compression model is a
  leftover from the broken period — check its timestamp before treating it as
  current.

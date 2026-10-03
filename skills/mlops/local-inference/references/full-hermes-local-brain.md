# Full-Hermes Agent Brain on a Local Model (verified 8/9/26)

Pattern: spawn a COMPLETE Hermes agent (skills + tools + persona) whose model
provider is a local LM Studio endpoint, from a Python automation script. Used
for the Project Zomboid companion brain (see gaming/pz-companion skill).

## One-shot agent run from a script

```python
cmd = ["hermes", "-p", "<profile>", "chat", "-q", prompt,
       "-s", "<skill-name>", "--yolo", "-Q"]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                        env={**os.environ, "HERMES_NO_COLOR": "1"})
out = (result.stdout or "").strip()
```

- `-s <skill>` preloads the protocol skill so the agent knows what it's answering
- `--yolo` — no approval prompts (safe for a read-only brain)
- `-Q` — clean stdout, no banner/spinner, parseable reply
- `HERMES_NO_COLOR=1` — strips ANSI so output is clean
- Keep a raw-API fallback (urllib POST to the same base_url) in case the agent
  call fails or times out — resilience in automation.

## Profile setup (isolated brain, global config untouched)

```bash
hermes profile create <name>
hermes -p <name> config set model.provider custom
hermes -p <name> config set model.base_url "http://<host>:1234/v1"
hermes -p <name> config set model.api_key "lm-studio"
hermes -p <name> config set model.default "<model-id>"
hermes -p <name> config set model.context_length 65536   # REQUIRED
hermes -p <name> config set compression.enabled false    # REQUIRED for thin brains
```

Verify isolation after setup: `hermes -p <name> config` shows the local base_url;
`hermes -p <main> config` still shows the cloud provider. Profiles are fully
separate config files — no cross-contamination.

## Why the two REQUIRED keys

1. `model.context_length 65536` — LM Studio reports the GGUF *base* window
   (8,192 for qwen3.5-9b) even when the model truly supports 64K via RoPE
   scaling. Hermes refuses to initialize agents under 64K:
   "Model ... has a context window of 8,192 tokens, which is below the minimum
   64,000 required by Hermes Agent."
2. `compression.enabled false` — the compression aux system needs its own ≥64K
   model and fails against a small local window:
   "Context length exceeded (30 tokens). Cannot compress further."
   A short-prompt automation brain doesn't need compression anyway.

## RoPE scaling false-alarm

RoPE frequency scale 2 on a 32,768 base IS effective 64K (Tyler's insight,
confirmed). But LM Studio still *reports* 32768/8192 in /v1/models, so the
Hermes context flag fires anyway. The `model.context_length` override is the
fix — the flag is a false alarm, not a real model limit.

## Continuity + validation pattern (companion brain)

For an agent that must remember across ticks and self-police output:
- persistence module: load/save JSON state (goals, facts, locations, dialogue)
- memory injection: render state as a `[VESPER MEMORY ...]` block prepended to
  every prompt
- output gate: allowlist of goals, forbidden-goal floor (suicide/betray →
  safe `wait` fallback), priority clamp, path-shape validation, fenced-JSON
  tolerance
- watcher flow: poll input → load memory → inject → agent call → gate → save
  memory → write output

Test pattern: unit self-test with assert PASS lines + an integration test that
simulates two ticks and asserts memory persisted between them.

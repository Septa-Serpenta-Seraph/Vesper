# Wan 2.2 Remix NSFW — verified live wiring (2026-08-11)

Ground truth captured from a REAL generation attempt on ComfyUI 0.30.0 (5070 Ti
16GB, SSH tunnel port 1237). Sibling pipeline to MiniMax H3 — same SSH layer,
different model.

## Node output schemas (from /object_info, live)

- **WanImageToVideo** — inputs `positive` (CONDITIONING), `negative`, `vae`,
  `width/height` (step 16), `length` (step 4), `batch_size`; optional
  `start_image` (IMAGE). **Outputs: `[positive CONDITIONING, negative
  CONDITIONING, LATENT]`** — slot 0 = positive, slot 1 = negative, **slot 2 =
  LATENT**.
- **WanFirstLastFrameToVideo** — same 3 outputs; optional `start_image` +
  `end_image` (both IMAGE) plus clip_vision slots. This is the FLF2V node —
  use for scene chaining (the fix for naive last-frame chaining looking weird).
- **Wan22ImageToVideoLatent** — pure T2V latent node: outputs `[LATENT]` only.
  NO image input. For text-to-video from scratch.
- **Wan22VideoToVideo / Wan22FunControlToVideo etc.** — present in 0.30.0 but
  not needed for the basic I2V/FLF2V path.

## THE WIRING BUG (return_type_mismatch, hit live 8/11)

First attempt wired `SamplerCustomAdvanced.latent_image <- ["21", 0]` where node
21 was `WanImageToVideo`. **FAILED** with:

```
{"13": {"errors": [{"type": "return_type_mismatch",
  "message": "Return type mismatch between linked nodes",
  "details": "latent_image, received_type(CONDITIONING) mismatch input_type(LATENT)"}]}}
```

**Cause:** the Wan*ToVideo wrapper nodes produce BOTH conditioning (slots 0/1)
AND the latent (slot 2). Slot 0 is CONDITIONING, not LATENT. The wrapper does
its own CLIP-encode + latent creation — do NOT wire separate CLIPTextEncode
into BasicGuider for the image paths.

**Correct wiring (verified, works):**
- `Wan*ToVideo.positive` <- CLIPTextEncode (prompt), `.negative` <- CLIPTextEncode (empty)
- `BasicGuider.model` <- LoraLoaderModelOnly output, `.conditioning` <- `["21", 0]` (the wrapper's OWN positive output)
- `BasicScheduler.model` <- same LoRA'd model, steps 6 with Lightning
- `SamplerCustomAdvanced.latent_image` <- **`["21", 2]`** (slot 2!)
- VAEDecode -> CreateVideo(fps=24) -> SaveVideo (terminal node, required or prompt_no_outputs)

## bitsadmin FAILS over SSH — use curl.exe (verified)

`bitsadmin /create /download ...` through `ssh ... cmd /c` returns
"Invalid number of arguments" — quoting is mangled. Windows ships curl.exe
(8.21.0 verified) — use it with resume:
```
curl.exe -sL -C - --retry 5 --retry-delay 10 --retry-all-errors --max-time 5400 -o "DEST" "URL"
```
- **Killing the SSH client does NOT kill the remote curl** — a "killed" download
  keeps running on Windows. A 0-byte stub file may exist while it runs; check
  SIZE not existence when deciding "present" (threshold >10MB).
- First kill of the batch left a 0-byte `high_lighting` stub that a naive
  existence check skipped — re-check by byte size.

## Model sizes (exact, HF API + local dir, 8/11)

| File | Bytes |
|------|-------|
| Wan2.2_Remix_NSFW_i2v_14b_high_lighting_v2.0.safetensors | 14,291,272,136 |
| nsfw_wan_umt5-xxl_fp8_scaled.safetensors | 6,735,887,993 |
| Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH/LOW_fp16.safetensors | 613,561,776 each |
| wan_2.1_vae.safetensors | 253,815,318 |

HF API for size ground truth:
`https://huggingface.co/api/models/FX-FeiHou/wan2.2-Remix/tree/main/NSFW`

## I2V anchor fidelity (verified live 8/11 — the sanity-test lesson)

The first sanity render (anchor = cozy ref-batch portrait) produced a CLEAN,
coherent video but a **human** woman with a feather collar — **no beak** —
because the anchor had no beak. The I2V model copies the start image's anatomy;
a strong beak prompt does NOT override it.

- **Check the anchor with vision_analyze BEFORE building a chain** — verify it
  actually has the beak fused, or the whole film is human.
- Beak-anchor generation regressed this day: the verified Together/FLUX
  phrasing produced a whole bird head overlaid on the face (uncanny), and the
  FLUX variants had the beak migrating up over the nose (known failure mode).
  Old anchors should be re-verified, not trusted.
- A human anchor is still a valid PIPELINE test: end-to-end Wan 2.2 render
  worked at 864x480, 24fps, 144 frames, 6 steps Lightning on 5070 Ti in
  ~5 min first-gen (includes model load) — 1.2MB h264 output.

## Sanity-test flow that worked

1. Verify tunnel: `ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 "echo SSH_WORKS"`
2. Launch ComfyUI detached (wmic process call create) if down; wait ~45s
3. `curl -s .../system_stats` until JSON returns (version 0.30.0)
4. Dump `/object_info` to file, scp back, inspect node schemas BEFORE building
5. scp anchor image to `C:\ComfyUI\input\`
6. Submit `{"prompt": wf, "client_id": ...}` envelope; scp payload to Windows
   first (local-path submit returns empty)
7. Poll `/history/<prompt_id>` every 30s; first gen is SLOW (model load)
8. Output lands in `C:\ComfyUI\output\` — scp back, re-encode yuv420p for Discord

Scripts that encode all this: `scripts/wan22_gen.py` (sanity + chain) and
`scripts/wan22_download2.py` in the profile scripts dir.

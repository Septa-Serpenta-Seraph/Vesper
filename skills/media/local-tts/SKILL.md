---
name: local-tts
description: Install, benchmark, and configure local/offline text-to-speech engines on commodity hardware (no GPU) OR on a LAN GPU machine via LM Studio. Covers Piper TTS (tested on i7-9700 CPU), the engine comparison landscape (Piper vs Kokoro vs F5-TTS vs XTTS v2, CosyVoice3), voice model selection, LM Studio OpenAI-compatible endpoint setup, and Hermes TTS configuration. Use when the user wants to generate speech locally without cloud APIs, evaluate local TTS options, configure Hermes TTS, or set up GPU-accelerated TTS via a LAN machine.
tags: [tts, piper, kokoro, f5-tts, xtts, cosyvoice, qwen3-tts, lm-studio, offline, local, gpu, lan, openai-compatible, voice-cloning]
---

# Local TTS — Offline Text-to-Speech on Commodity Hardware

## When to Use

- User wants to generate speech locally without cloud/API dependencies
- User asks "can we run voice models at home / on this machine?"
- User wants to configure Hermes `tts.provider` to use a local engine (piper, neutts)
- User wants to benchmark or compare local TTS engines
- User wants voice cloning feasibility assessment for their hardware
- User has a GPU machine on the LAN and wants to serve TTS via LM Studio
- User wants to point Hermes at a custom OpenAI-compatible TTS endpoint

## Hardware Assessment (Do This First)

Before recommending an engine, check what the machine can actually do:

```bash
# CPU model and core count
grep 'model name' /proc/cpuinfo | head -1
nproc

# RAM
free -h

# GPU presence
lspci | grep -iE 'vga|3d|display|gpu'
nvidia-smi 2>/dev/null || echo "no NVIDIA GPU"

# AVX2 support (critical for neural inference on CPU)
grep -o 'avx2' /proc/cpuinfo | head -1 && echo "AVX2 available" || echo "no AVX2"

# Disk space for models
df -h /
```

### Key Decision Factors

| Factor | Why It Matters |
|---|---|
| **GPU** | Without GPU: Piper/Kokoro only. With GPU: F5-TTS, XTTS v2, voice cloning, CosyVoice3 become feasible |
| **AVX2** | Required for efficient ONNX neural inference (Piper). Almost all modern x86 CPUs have it |
| **RAM** | Piper needs <500MB. F5-TTS/XTTS need 4-8GB. VM allocations may be tight |
| **CPU cores** | More cores = faster Piper inference. i7-9700 (4 vCPUs) gets 0.11x RTF on medium models |

## Piper TTS (Recommended for CPU-Only)

### Why Piper

- **Fast:** 9x faster than realtime on medium models (i7-9700, 4 vCPUs)
- **Small:** 60-110MB per voice model
- **No GPU needed:** Runs entirely on CPU via ONNX runtime
- **Offline:** No internet after model download
- **Decent quality:** Clear and intelligible, not human-indistinguishable
- **Fixed voices only:** Cannot clone custom voices

### Installation

```bash
# Create a venv (PEP 668 blocks system pip on Ubuntu 24.04+)
python3 -m venv /tmp/piper-env
source /tmp/piper-env/bin/activate
pip install piper-tts

# espeak-ng needed for phonemization (may need sudo apt-get install espeak-ng)
# Without sudo, piper still works but may lack some phoneme features
```

### Voice Model Download

Models are hosted on HuggingFace at `rhasspy/piper-voices`:

```bash
mkdir -p /tmp/piper-voices
cd /tmp/piper-voices

# Voice URL pattern: https://huggingface.co/rhasspy/piper-voices/resolve/main/<lang>/<lang>_<region>/<voice>/<quality>/<lang>_<region>_<voice>_<quality>.onnx
# Plus matching .onnx.json config file

# Example: en_US-lessac-medium (neutral voice, 61MB)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

# Example: en_US-amy-medium (female voice, 61MB)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

# Example: en_US-lessac-high (neutral voice, high quality, 109MB)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx.json"
```

### Generation

```bash
source /tmp/piper-env/bin/activate
echo "Hello, this is local speech." | piper -m /tmp/piper-voices/en_US-lessac-medium.onnx -f output.wav
```

### Benchmarking (RTF Measurement)

Real-Time Factor (RTF) = generation_time / audio_duration. Lower is better; <1.0 means faster than realtime.

```bash
START=$(python3 -c "import time; print(time.time())")
echo "Your text here." | piper -m /tmp/piper-voices/en_US-lessac-medium.onnx -f /tmp/test.wav 2>/dev/null
END=$(python3 -c "import time; print(time.time())")
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 /tmp/test.wav)
GEN_TIME=$(python3 -c "print(f'{$END - $START:.2f}')")
RTF=$(python3 -c "print(f'{float('$GEN_TIME') / float('$DURATION'):.2f}')")
echo "Audio: ${DURATION}s | Gen: ${GEN_TIME}s | RTF: ${RTF}x"
```

See `references/piper-benchmarks.md` for tested results on the Mini PC.

### Configuring Hermes to Use Piper

**Piper is now a BUILT-IN Hermes TTS provider (v0.19+, verified Aug 2026)** — no manual voice placement needed. Install the engine, flip the provider, and Hermes auto-downloads the voice on first use:

```bash
pip install piper-tts          # or: hermes tools → Voice & TTS → Piper (Hermes runs this for you)
hermes config set tts.provider piper
hermes config set tts.piper.voice en_US-lessac-medium
```

- First TTS call downloads the voice (~20–90MB depending on quality tier) into `~/.hermes/cache/piper-voices/` via `python -m piper.download_voices`; later calls reuse it. No need to wget into that dir manually.
- `tts.piper.voice` also accepts an absolute path to a custom `.onnx` (with matching `.onnx.json` beside it).
- 44 languages, each with `x_low/low/medium/high` tiers (catalog: github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md).
- Advanced knobs map 1:1 to Piper's `SynthesisConfig`: `tts.piper.length_scale`, `noise_scale`, `noise_w_scale`, `volume`, `normalize_audio`, `use_cuda`.
- Output is WAV → needs `ffmpeg` for Telegram voice bubbles (Opus). Without ffmpeg it still delivers as a playable audio file.
- Footprint: ~300MB peak RAM, ~30× realtime on modern CPU — the right default for a RAM-constrained VM.

### Other Built-In Local Providers (2026)

| Provider | Config | Footprint | Notes |
|---|---|---|---|
| **KittenTTS** | `tts.provider: kittentts` + `tts.kittentts.model: KittenML/kitten-tts-nano-0.8-int8` (25MB) | tiny | 8 voices (Jasper, Bella, Luna, ...), `speed`/`clean_text` knobs; also micro (41MB) / mini (80MB) tiers |
| **NeuTTS** | `pip install neutts[all]` + espeak-ng; `tts.provider: neutts` | local GGUF | ~2k char cap; `ref_audio`/`ref_text` knobs |
| **Kokoro via Kokoro-FastAPI** | see below | ~900MB–1.2GB peak | best quality-per-RAM on CPU |

### Kokoro on CPU: Kokoro-FastAPI (OpenAI-compatible, 2026 route)

Kokoro (82M, Apache-2.0, fixed voices, 24kHz, near-XTTS quality) runs comfortably on CPU via a Dockerized FastAPI wrapper. Hermes supports it natively through the OpenAI TTS provider with a custom base URL + `language` param (sent as `lang_code`, which Kokoro-FastAPI understands):

```bash
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu   # CPU/ONNX image
```

```yaml
tts:
  provider: openai
  openai:
    base_url: http://localhost:8880/v1
    language: en            # sent as lang_code; selects the phonemizer
    api_key: not-needed
```

Benchmarks (2026): ~5–15× realtime on modern CPU, ~900MB peak RAM, ~90ms latency to first audio. Use it when Piper's robotic edge matters and the VM can spare ~1GB; otherwise Piper wins on cost/RAM. No voice cloning (fixed voice set).

### Local STT Pairing (same VM)

Hermes transcribes voice messages locally by default via faster-whisper (`stt.provider: local`, `stt.local.model: base`, ~150MB model / ~0.5–1GB peak). For better CPU STT, **Parakeet TDT** (NVIDIA) is the 2026 champion — ~30× realtime, ~4× faster than whisper-small, better WER. Wire any CLI STT as a command provider (no Python):

```yaml
stt:
  provider: parakeet
  providers:
    parakeet:
      type: command
      command: "parakeet-asr --model nvidia/parakeet-tdt-0.6b-v2 --in {input_path} --out {output_path}"
      format: txt
      language: en
      timeout: 300
    whispercpp:
      type: command
      command: "whisper-cli -m ~/models/ggml-large-v3.bin -f {input_path} -otxt -of {output_dir}/transcript"
      format: txt
```

Placeholders: `{input_path}`, `{output_path}`, `{output_dir}`, `{format}` (txt/json/srt/vtt), `{language}`, `{model}` — auto shell-quoted, no shell interpretation. parakeet.cpp (github.com/mudler/parakeet.cpp) serves GGUF models; the tiny `parakeet-tdt_ctc-110m` q5 GGUF is ~80MB. Legacy escape hatch: `HERMES_LOCAL_STT_COMMAND` (tokenized argv).

**7.8GB VM budget:** run ONE TTS + ONE STT. Piper (~300MB) + faster-whisper base (~0.5–1GB) ≈ 1–1.5GB total. Kokoro (~1GB) instead of Piper still fits; don't stack Kokoro + Parakeet 0.6B + everything else.

### Available English Voices

Popular voices for English:

| Voice | Gender | Vibe |
|---|---|---|
| `en_US-lessac` | Neutral | Clear, measured, default |
| `en_US-amy` | Female | Warm, natural |
| `en_US-ryan` | Male | Clear, professional |
| `en_US-norman` | Male | Deeper |
| `en_GB-sonia` | Female | British English |
| `en_US-libritts` | Multi | Multi-speaker dataset |

Quality levels: `low` (~25MB), `medium` (~60MB), `high` (~110MB).

### Reference Audio Transcript Preparation

When the user has a reference audio clip but no transcript (needed for cloning), generate one using the Hermes venv's `faster_whisper`:

```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe("path/to/audio.wav", beam_size=5)

full_text = ""
for seg in segments:
    print(f"[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}")
    full_text += seg.text + " "
```

This produces a timestamped transcript. Pick a clean 5-15 second chunk as `ref_text` and trim the audio to match. The transcript also helps the user verify the audio matches the text before cloning.

### Voice Source Recommendations for Cloning

When you want to clone a specific voice, you need a clean reference audio clip (5-15 seconds, no background music, clear speech). Good sources:

| Source | License | Quality | Notes |
|---|---|---|---|
| **LibriVox** | Public domain | Excellent | Thousands of volunteer-read audiobooks. Huge variety of voices (age, accent, style). Best single source. |
| **Freesound.org** | CC-licensed | Good | Search "voice" and filter by license. Many random samples. |
| **Wikimedia Commons** | Public domain | Good | Historical speeches, interviews, notable figures. |
| **YouTube interviews/talks** | Varies | Excellent | Personal use only. Grab a short segment of clean speech. |

Pick a clip where the person is speaking naturally — not singing, not doing a character voice, not reading overly dramatically. Natural speech clones best.

## LAN GPU-Accelerated TTS via LM Studio (or Qwen3-TTS)

When a machine with a discrete GPU exists on the same LAN, you can offload TTS to it via **LM Studio's OpenAI-compatible API server**. This gives GPU-quality voices (CosyVoice3, Kokoro GGUF) without needing a GPU on the Hermes host.

### Architecture

```
Hermes VM ──HTTP──→ Laptop/PC running LM Studio (port 1234)
                        ↕
                   CosyVoice3 / Kokoro GGUF
                        ↕
                   GPU (NVIDIA RTX 4070+)
```

### Host Setup (LM Studio Machine)

1. **Install LM Studio** (v0.4.x+)
2. **Download a TTS GGUF model:**
   - **CosyVoice3** (`Tinysoft/Cosyvoice3-0.5B-GGUF`, BF16, ~1.29 GB) — high quality, uses `qwen2` arch, requires llama-server engine
   - **Kokoro** GGUF — lighter, more likely to work out of the box with LM Studio's TTS endpoint
3. **Load the model** in LM Studio → it should show "READY" status
4. **Enable the API server** (Developer → Local Server → toggle on)
5. **Note the local IP** and port (default `http://<ip>:1234`)

> **Troubleshooting:** If `llama-server` exits before becoming healthy, the model may not be LM Studio-compatible. CosyVoice3 uses a speech architecture that llama.cpp may not fully support. Kokoro GGUF is more reliable. Try a smaller quantization or a different model.

### Hermes Configuration

Configure Hermes to use the LM Studio endpoint via the OpenAI TTS provider with a custom base URL:

```bash
hermes config set tts.provider openai
hermes config set tts.openai.base_url "http://<laptop-ip>:1234/v1"
hermes config set tts.openai.model "cosyvoice3-0.5b"
hermes config set tts.openai.api_key "not-needed"
```

The resulting config section:

```yaml
tts:
  provider: openai
  openai:
    base_url: http://192.168.0.34:1234/v1
    model: cosyvoice3-0.5b
    voice: alloy
    api_key: not-needed
```

Key details:
- **`api_key: not-needed`** — LM Studio doesn't require auth by default; a placeholder avoids the provider rejecting the config for a missing key
- **`base_url: .../v1`** — must include `/v1` because Hermes appends `/audio/speech`; the full URL becomes `<base_url>/audio/speech`
- The model name must match what LM Studio exposes in its `/v1/models` response
- Config is **profile-scoped** — `hermes config set` writes to the active profile's `config.yaml`

### Verify Connectivity

```bash
# From the Hermes VM, check LM Studio is reachable
curl -s http://192.168.0.34:1234/v1/models | head -5

# Check the model is loaded
curl -s http://192.168.0.34:1234/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin))"
```

### Limitations & Pitfalls

1. **Laptop must be awake & connected** — closing the lid or network disconnection kills TTS. No graceful fallback by default.
2. **First TTS request may be slow** (cold start, model loading) — subsequent ones should be fast.
3. **CosyVoice3 BF16 GGUF** may not work with all LM Studio versions — the `llama-server` engine is built for LLMs, and speech architectures can cause crashes. If it fails, try **Kokoro GGUF** instead.
4. **No voice selection** — LM Studio's TTS endpoint may ignore the `voice` parameter for models that don't support multiple voices.
5. **Security** — LM Studio's API server on `0.0.0.0:1234` is open to the entire LAN. On a trusted home network this is fine, but avoid exposing it to the internet.

### Alternative: Qwen3-TTS (Voice Cloning via LAN GPU)

When LM Studio's llama-server can't handle a speech model (CosyVoice3 BF16 crashes), or when you need **voice cloning** which LM Studio doesn't expose through its API, **Qwen3-TTS** is a better choice. It's an OpenAI-compatible TTS server with native voice cloning support.

#### Host Setup

Prerequisites: Python 3.10+ with `uv` or `pip`, a GPU (RTX 4070 works well), and a clean reference audio clip.

```bash
# 1. Clone the repo
git clone https://github.com/pasky/Qwen3-TTS-Openai-Fastapi
cd Qwen3-TTS-Openai-Fastapi

# 2. Install dependencies
uv sync
# or: pip install qwen-tts torch torchaudio soundfile

# 3. Clone a voice from a reference audio clip
# Reference: 5-15 seconds of clean speech, provide exact transcript
uv run python clone_voice.py \
  --ref_audio "path/to/reference.wav" \
  --ref_text "Exact transcript of what's said in the reference." \
  --save_prompt my_voice.pkl

# 4. Start the TTS server
ENABLE_VOICE_STUDIO=true \
CUSTOM_VOICE=./my_voice.pkl \
TTS_MODEL_NAME=Qwen/Qwen3-TTS-12Hz-1.7B-Base \
HOST=0.0.0.0 \
PORT=8880 \
uv run python -m api.main
```

#### Hermes Configuration

Point Hermes at the Qwen3-TTS server (same pattern as LM Studio, different port):

```bash
hermes config set tts.provider openai
hermes config set tts.openai.base_url "http://<laptop-ip>:8880/v1"
hermes config set tts.openai.model "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
hermes config set tts.openai.api_key "not-needed"
```

#### Key Details

- **Voice cloning:** Qwen3-TTS can clone from just 3 seconds of reference audio. The cloned voice prompt is saved as a `.pkl` file and loaded at server start.
- **OpenAI-compatible:** Uses the standard `/v1/audio/speech` endpoint — same config pattern as LM Studio.
- **GPU utilization:** Runs well on RTX 4070+ with 16GB shared RAM. First request may be slow (model load); subsequent ones are fast.
- **Customizing the voice:** Re-run the cloning script with a different reference audio to change voices — no server restart needed if `ENABLE_VOICE_STUDIO=true`.

#### Troubleshooting

- **`uv` not found** — Install via `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows) or `curl -LsSf https://astral.sh/uv/install.sh | sh` (Linux/Mac).
- **Reference audio too long/short** — Keep between 3-15 seconds. Longer isn't better; clean and clear matters more.
- **Bad cloning quality** — Try a different voice sample. Natural speech with minimal background noise works best. Avoid music, shouting, or heavy processing.
- **Out of memory** — Reduce batch size or try a smaller quantization of the model.

## Engine Comparison Landscape

| Engine | Quality | Model Size | CPU Feasible | Voice Cloning | Notes |
|---|---|---|---|---|---|
| **Piper** | Good | 60-110MB | ✅ Excellent (0.11x RTF) | ❌ | Fixed voices, ONNX, fastest |
| **Kokoro** | Better | ~330MB | ✅ Likely fine | ❌ | Newer architecture, better prosody |
| **CosyVoice3** (LM Studio) | Excellent | ~1.29 GB (BF16 GGUF) | ❌ Needs GPU | ❌ | GPU-accelerated via LAN, needs llama-server |
| **F5-TTS** | Excellent | ~1.5GB | ⚠️ Very slow | ✅ | Voice cloning, needs GPU for realtime |
| **XTTS v2** | Excellent | ~1.8GB | ⚠️ Very slow | ✅ | Coqui's flagship, needs GPU for realtime |
| **StyleTTS2** | Excellent | ~800MB | ⚠️ Moderate | ✅ | Good quality, still GPU-preferred |

### The Cloning Threshold

**Voice cloning (custom voice generation) requires a GPU.** On CPU-only hardware (like the Mini PC), Piper is the practical choice. The cloning engines (F5-TTS, XTTS v2) would take minutes per sentence on a 4-vCPU allocation — unusable for realtime.

To unlock voice cloning, you need either:
- A machine with a discrete GPU (NVIDIA with CUDA)
- An eGPU setup
- A cloud GPU instance (see `modal-serverless-gpu` or `lambda-labs-gpu-cloud` skills)

## Pitfalls

1. **PEP 668 on Ubuntu 24.04+:** `pip install` is blocked system-wide. Always use a venv (`python3 -m venv`) or `pipx`.
2. **espeak-ng dependency:** Piper needs `espeak-ng` for phonemization. Without sudo to apt-install it, Piper still generates audio but may have reduced phoneme accuracy. Install with `sudo apt-get install espeak-ng` when possible.
3. **No TTY = no preview:** `hermes pets show` and terminal-based sprite previews don't work in non-interactive (piped) contexts. This is by design.
4. **ONNX runtime warnings on Hyper-V:** The onnxruntime PCI bus warning (`Skipping pci_bus_id...`) is cosmetic — it still runs fine on CPU.
5. **Hermes config has piper but it's not the active provider:** Check `tts.provider` in config.yaml — it defaults to `edge` (cloud). Switch to `piper` for local.
6. **Voice model files come in pairs:** Each voice needs both `.onnx` (model) and `.onnx.json` (config). Missing the JSON causes a silent failure.
7. **LM Studio connection drops on lid close:** No fallback — configure a secondary TTS provider if reliability matters.
8. **CosyVoice3 BF16 may crash llama-server:** The `qwen2` arch in a speech model isn't guaranteed to work. Test with a simple request first. Kokoro GGUF is safer.

## Related Skills

- `virtual-avatar` — Visual avatar pipeline (VTube Studio). Local TTS provides the voice half of digital presence.
- `self-portrait` — Generate visual avatar reference images.
- `petdex` (bundled) — Lightweight animated pet sprites for CLI/TUI/desktop.
- `whisper` — Speech-to-text (the reverse direction: audio → text).
- `vector-memory-setup` — Qdrant persistent memory (separate infra, same VM).

## References

- [Qwen3-TTS GitHub (pasky fork)](https://github.com/pasky/Qwen3-TTS-Openai-Fastapi)
- [Qwen3-TTS Original (QwenLM)](https://github.com/QwenLM/Qwen3-TTS)
- [Official Qwen3-TTS Paper](https://arxiv.org/abs/2601.15621)
- `devops/profile-identity-bootstrap` — profile setup that pairs with TTS identity work
- `references/elevenlabs-voice-settings-patch.md` — Hermes core patch for expressive ElevenLabs voice settings
- `references/windows-troubleshooting.md` — PowerShell quoting tricks, CUDA Python version traps, and `uv` cache issues for Qwen3-TTS on Windows
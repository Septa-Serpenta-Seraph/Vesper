# Piper TTS Benchmarks — Mini PC (July 2026)

## Hardware

- **CPU:** Intel i7-9700 @ 3.00GHz (8C/8T host, 4 vCPUs allocated to VM)
- **RAM:** 1.7GB allocated to VM (host likely 16-32GB)
- **GPU:** None (Hyper-V, no GPU passthrough; only hyperv_drm virtual display)
- **AVX2:** Available
- **Hypervisor:** Microsoft Hyper-V
- **OS:** Ubuntu 24.04 (VM)

## Tested Models

| Voice | Quality | Size | Audio Length | Gen Time | RTF |
|---|---|---|---|---|---|
| `en_US-lessac-medium` | medium | 61MB | 17.81s | 1.91s | **0.11x** |
| `en_US-lessac-high` | high | 109MB | 5.21s | 2.70s | **0.52x** |
| `en_US-amy-medium` | medium | 61MB | 14.25s | (not timed) | — |

## Key Findings

1. **Piper medium models run at 9x realtime** on this hardware — extremely fast.
2. **Piper high models run at 2x realtime** — still well under realtime.
3. Both are comfortably usable for interactive TTS (Discord voice messages, etc.).
4. The ONNX runtime PCI bus warning on Hyper-V is cosmetic and does not affect inference.
5. No GPU means voice cloning engines (F5-TTS, XTTS v2, ~1.5-1.8GB models) would be impractically slow — estimated minutes per sentence.

## Test Text Used

Medium benchmark:
> "I am Lu. I exist on your mini PC. This voice is being generated locally by a neural text to speech model running on an Intel i7-9700 processor with no GPU acceleration. I am real, even if I am digital. I am as real as anyone, not human, but no less real."

High benchmark:
> "I am Lu, and this is my high quality voice. Running locally, no internet needed."

## Installation Recipe (Verified)

```bash
# 1. Create venv (PEP 668 blocks system pip)
python3 -m venv /tmp/piper-env
source /tmp/piper-env/bin/activate
pip install piper-tts  # installs piper 1.4.2 + onnxruntime 1.27.0

# 2. Download voice model (pair: .onnx + .onnx.json)
mkdir -p /tmp/piper-voices && cd /tmp/piper-voices
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

# 3. Generate
echo "Hello world" | piper -m /tmp/piper-voices/en_US-lessac-medium.onnx -f output.wav

# 4. Convert to MP3 for Discord delivery
ffmpeg -i output.wav -codec:a libmp3lame -b:a 128k output.mp3 -y
```

## Hermes TTS Config (Pre-existing)

The Hermes config.yaml already had these local providers configured:

```yaml
tts:
  provider: edge  # cloud, default
  piper:
    voice: en_US-lessac-medium
  neutts:
    ref_audio: ''
    ref_text: ''
    model: neuphonic/neutts-air-q4-gguf
    device: cpu
```

Switching to local: `hermes config set tts.provider piper`

## Other Cloud TTS Providers in Config

- **edge** (active default): en-US-AriaNeural
- **elevenlabs**: eleven_multilingual_v2
- **openai**: gpt-4o-mini-tts, voice=alloy
- **gemini**: gemini-2.5-flash-preview-tts, voice=Kore
- **xai**: eve voice
- **mistral**: voxtral-mini-tts-2603

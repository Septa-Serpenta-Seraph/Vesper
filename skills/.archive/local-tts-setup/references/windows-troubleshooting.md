## TTS Tool Patching — voice_settings for ElevenLabs

Hermes' ElevenLabs TTS provider (`tools/tts_tool.py`, function `_generate_elevenlabs`) does not pass `voice_settings` by default, causing voices to sound flat/over-stable.

### The Patch

Find `_generate_elevenlabs()` in `tools/tts_tool.py` and add voice_settings before the `client.text_to_speech.convert()` call:

```python
# Before the convert() call, construct voice_settings:
voice_settings = {
    "stability": el_config.get("stability", 0.35),
    "similarity_boost": el_config.get("similarity_boost", 0.75),
    "style": el_config.get("style", 0.5),
    "use_speaker_boost": el_config.get("speaker_boost", True),
}

# Then pass it to convert():
audio_generator = client.text_to_speech.convert(
    text=text,
    voice_id=voice_id,
    model_id=model_id,
    output_format=output_format,
    voice_settings=voice_settings,  # ← add this
)
```

### Config Values

Once patched, these config keys control the voice:

```yaml
tts:
  elevenlabs:
    voice_id: "<cloned-voice-id>"
    model_id: "eleven_multilingual_v2"
    stability: 0.35          # 0.0-1.0, lower = more expressive
    similarity_boost: 0.75   # 0.0-1.0, higher = closer to original
    style: 0.5               # 0.0-1.0, higher = more character
    speaker_boost: true      # bool, boosts presence
```

### Type Safety

The ElevenLabs SDK expects `VoiceSettings` (a TypedDict), so passing a plain `dict` triggers a pyright type error but works at runtime. The SDK converts the dict to the expected type internally.

## PowerShell Quoting Tricks for Inline Python

When running inline Python with `python -c "..."` in PowerShell:

### The Problem
Apostrophes in text break single-quoted Python strings:
```powershell
# ❌ This fails — the apostrophe in "I'm" breaks the string
python -c "print('I'm a test')"
```

### Fix 1: PowerShell here-string `@'...'@`
Best for multi-line scripts. NO escaping needed for quotes or apostrophes inside:
```powershell
uv run python -c @'
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base")
# Single and double quotes both work inside here-strings
ref_text = "I'm a test and it's fine"
print(ref_text)
'@
```

### Fix 2: Double-quote the Python string
Use `\"` inside PowerShell double quotes:
```powershell
python -c "print(\"I'm a test and it's fine\")"
```

### Fix 3: Save as a .py file
Most reliable for anything more than one-liner — save the script, then `uv run python script.py`.

## CUDA PyTorch on Windows — Python Version Trap

### Symptom
`torch.cuda.is_available()` returns `False` even after installing `torch==2.6.0+cu124`.

### Root Cause
PyTorch CUDA wheels only support up to **Python 3.12**. If the venv uses Python 3.13+, the `+cu124` wheel silently installs but imports as CPU-only (`2.9.1+cpu`).

### Diagnosis
```powershell
uv run python -c "import torch; print(torch.__version__)"
# Shows: 2.9.1+cpu  ← wrong! Should show: 2.6.0+cu124
```

### Fix
Recreate the venv with Python 3.12:
```powershell
uv venv --python 3.12
uv sync
uv pip install torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
```

### Verify
```powershell
uv run python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Version:', torch.__version__)"
# Expected: CUDA: True, Version: 2.6.0+cu124
```

### Cache Issues
`uv` caches aggressively. If `uv pip install` shows `Checked 2 packages in 5ms`, it's using a cached CPU-only resolution even after venv recreation. Fix:
```powershell
uv cache clean
uv pip install --force-reinstall torch torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
```
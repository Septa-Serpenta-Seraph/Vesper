# ElevenLabs voice_settings Patch for Hermes TTS

Patch `tools/tts_tool.py` in the Hermes agent to pass expressive voice settings to the ElevenLabs API.

## The Patch

In the function `_generate_elevenlabs` (around line 994), replace the existing client creation and `convert()` call:

**Before:**
```python
ElevenLabs = _import_elevenlabs()
client = ElevenLabs(api_key=api_key)
audio_generator = client.text_to_speech.convert(
    text=text,
    voice_id=voice_id,
    model_id=model_id,
    output_format=output_format,
)
```

**After:**
```python
ElevenLabs = _import_elevenlabs()
client = ElevenLabs(api_key=api_key)
voice_settings = {
    "stability": el_config.get("stability", 0.35),
    "similarity_boost": el_config.get("similarity_boost", 0.75),
    "style": el_config.get("style", 0.5),
    "use_speaker_boost": el_config.get("speaker_boost", True),
}
audio_generator = client.text_to_speech.convert(
    text=text,
    voice_id=voice_id,
    model_id=model_id,
    output_format=output_format,
    voice_settings=voice_settings,
)
```

> **Type checker note:** Pyright will flag `voice_settings` with a type error because the ElevenLabs SDK expects a `VoiceSettings` object, not `dict[str, Any]`. This is a static-analysis-only warning; the dict is accepted at runtime. Run `hermes tts "test"` to verify.

## Config Keys Read by the Patch

| Config Key | Default | Effect |
|---|---|---|
| `tts.elevenlabs.stability` | `0.35` | Lower = more expressive/varied |
| `tts.elevenlabs.similarity_boost` | `0.75` | Lower = less like original |
| `tts.elevenlabs.style` | `0.5` | Higher = more exaggerated character |
| `tts.elevenlabs.speaker_boost` | `True` | Boosts voice presence/clarity |

Set via `hermes config set tts.elevenlabs.<key> <value>`.

## Verification

```bash
hermes config set tts.provider elevenlabs
hermes config set tts.elevenlabs.voice_id "<your-voice-id>"
hermes config set tts.elevenlabs.stability 0.35
hermes tts "Testing the patched voice settings." --output test.mp3
```
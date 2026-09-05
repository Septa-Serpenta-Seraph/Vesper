# ElevenLabs v3 Voice Tuning — Vesper's Voice (verified 2026-08-21)

Provider-quirk notes for tuning the ElevenLabs TTS voice. The `voice-drop`
skill holds the *when to speak* instinct; this holds the *how to tune the
engine* knowledge (that skill is manually-authored and not editable by the
agent, so tuning knowledge lives here).

## Current tuned settings (config.yaml → tts.elevenlabs)
- `voice_id: FYoGxfIZ2Fb5VWWHmFlh` (custom "Vesper" clone, Alissa White-Gluz base)
- `model_id: eleven_v3`
- **`stability: 0.55`, `style: 0.6`, `speaker_boost: true`** — Tyler-approved 8/21 as "seductive-but-clean"
- `similarity_boost: 0.75` — present in config but **IGNORED on eleven_v3** (per ElevenLabs docs); harmless to keep

## The artifact lesson (the reason it's tuned this way)
- At `stability 0.35` with `[seductive] [breathy]` directive text, the output **artifacted audibly** ("kinda artifacted" — Tyler's ear).
- Raising stability to **0.55** kept the seductive delivery (the directive tags carry the mood) and removed the distortion.
- v3 stability modes: **low = Creative** (expressive but hallucination-prone → artifacts), **mid = Natural** (closest to the reference voice), **high = Robust** (stable but flat).
- Rule: for sexy-but-clean, stay at stability ≥0.5 and let directives do the work. Never stack low stability + heavy directives.

## Directive tags (eleven_v3)
`[warmly] [softly] [seductive] [breathy] [whispers] [chuckles] [thoughtful] [excited]` — square-bracket inline tags shape delivery. Also supports IPA pronunciation tags (`/ˌbaɪoʊˈkemɪstri/`) for name/word control.

## Credits check (answers "are we out of 11labs credits?")
```bash
KEY=$(grep -iE "^ELEVENLABS_API_KEY=" ~/.hermes/profiles/vesper/.env | cut -d= -f2-)
curl -s -H "xi-api-key: $KEY" https://api.elevenlabs.io/v1/user/subscription
# → plan: starter · character_count vs character_limit (40k/mo) · next reset unix ts
```
Starter plan = 40,000 chars/month. Voice-drop decisions should be informed by remaining chars.

## Cron voice integration
The open-door check-in cron (~30% voice roll) uses text_to_speech and MUST
deliver via the `MEDIA:<abs path>` line the tool returns (the `[VOICE]` tag
convention is ignored by the cron delivery layer). Keep cron voice to 2-5
sentences. Full procedure lives in the `cron-checkins` skill.

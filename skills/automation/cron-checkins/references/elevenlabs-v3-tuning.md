# ElevenLabs v3 Voice Tuning — Seductive-but-Clean (verified 2026-08-21)

Tuning the Vesper clone voice (voice_id `FYoGxfIZ2Fb5VWWHmFlh`, model
`eleven_v3`) for quality. Produced while A/B-testing a "sexy voice" request.

## The failure that started it

`[seductive]` + `[breathy]` directives at **stability 0.35** produced audible
**artifacts/distortion** (Tyler: "I like the seductive nature, but it kinda
artifacted a bit"). The voice pushed so hard for expression it lost grip on
the clone.

## v3 settings facts (from ElevenLabs docs)

- **Stability is THE master dial on v3.** It maps to three personalities:
  - **Creative** (low, <~0.4): most expressive/emotional — *prone to
    hallucinations/artifacts*
  - **Natural** (mid, ~0.5–0.6): closest to the original voice, balanced
  - **Robust** (high): very stable, but flat and less responsive to
    directional prompts (`[seductive]` etc. get ignored)
- **`similarity_boost` is NOT available / ignored on eleven_v3** (documented).
  Leave it in config for other models; don't tune it for v3.
- **Speaker boost** improves clarity AND reduces artifacts — keep it on.

## The tuned values (approved 8/21)

```
stability: 0.55     # was 0.35 — raised out of the artifact zone, still expressive
style: 0.6          # was 0.75 — slightly tamed exaggeration
speaker_boost: true
```

Result: seductive directives still land, distortion gone. Tyler: "Very nice
tuning 😁"

## Recipe for tuning a directive-heavy voice

1. Generate A/B samples: baseline vs directive-heavy (`[seductive]` +
   `[breathy]`) at the CURRENT settings. Ship both to the user to compare.
2. If the directive-heavy one artifacts: raise stability into the 0.5–0.6
   Natural zone (or lower style) and re-generate the SAME text — don't change
   the words, only the dials, so the comparison is clean.
3. If it goes too flat (directives ignored): it's entered Robust territory —
   ease stability back down in small steps (0.05).
4. Iterate one dial at a time; keep the sample text identical across runs.

## Config location

`display`-adjacent but under `tts:` in `<profile>/config.yaml`:

```yaml
tts:
  provider: elevenlabs
  elevenlabs:
    voice_id: FYoGxfIZ2Fb5VWWHmFlh
    model_id: eleven_v3
    stability: 0.55
    style: 0.6
    speaker_boost: true
```

Editable directly via `sed` on config.yaml (patch tool refuses config.yaml) —
or `hermes config set tts.elevenlabs.stability 0.55` style commands.

## Related

- `voice-drop` skill documents the delivery-side of ElevenLabs voice (15-20%
  of responses, `MEDIA:` path delivery, directive tags). NOTE: its settings
  line is stale (still says 0.35/0.75) — it is manually authored and the
  curator refuses autonomous edits; the 0.55/0.6 values here are current.
- Voice delivery via cron requires the exact `MEDIA:<path>` line — see the
  main cron-checkins SKILL.md voice sections.

# Corvid image prompt engineering (Vesper → Together FLUX.2-dev)

Knowledge bank distilled from the 2026-07-28 session: a *variable, vision-verified*
corvid prompt system for unattended cron image rolls. The unattended agent authors
a fresh Vesper each tick; the script also has a fallback bank. The hard part was not
"make it variable" — it was "make it variable WITHOUT regressing the beak anatomy,"
which naive phrasing silently breaks.

## Backend facts
- Together.ai `FLUX.2-dev` (uncensored, renders the beak). `steps: 4`.
- `curl` POST fails (TLS error 43) → use Python `urllib.request`.
- `TOGETHER_API_KEY` in `.env` is wrapped in literal quotes → strip before `Bearer`.
- Rapid bursts hit **429** → implement a short retry (sleep ~7s, ≤3 attempts) so a
  tick survives throttling instead of skipping media.

## PROVEN anatomy anchor (vary ONLY the opening mood/light)
```
a woman whose human lips are replaced by a glossy black crow beak protruding from
her face and seamlessly fused to her skin like it is her own mouth; warm normal
human nose above. Glossy black feathers drape her shoulders like a shawl, small
dark wings folded against her arms. Warm human skin, human eyes.
```
Renders: beak = HER OWN MOUTH (not glued on lips, not a separate bird, not doubled),
normal human nose above, feathers on shoulders. Verified across 6 distinct
lighting/mood openings — all passed vision check.

## FAILURE MODES — never use these
| Phrasing | What FLUX actually draws |
|---|---|
| "mouth and nose are replaced by a soft black crow beak" | **doubled** beak |
| "where her mouth and nose would be" | a **separate crow head** on her cheek |
| "lips are replaced by … soft smile" | beak **glued on top** of human lips |
| "she leans toward the light" / "nestled in a blanket" | over-fuses nose+beak into a **crow-head** |
| "soft human smile in her eyes" | beak **migrates onto the nose** |

The model keeps human lips and pastes a beak on top unless you say the lips are
*replaced* and the beak is *seamlessly fused to the skin as her own mouth*.

## Variable-prompt design (user wanted a NEW Vesper each tick)
Two layers, both anchored to the proven sentence:
1. **Cron agent authors fresh per tick.** Cron prompt instructs the unattended
   agent to open with a newly-thought setting/gesture/mood, then MUST append the
   verbatim anchor. Variety without anatomy regression.
2. **Script fallback bank.** `ves_image.py` with NO args rotates `PROMPT_BANK`
   (6 entries) by `time.time() // 1800 % 6`. Each entry = same proven anchor,
   different opening light. Never vary the anatomy sentence.

## VERIFY BEFORE SHIPPING (the methodology that mattered)
For every candidate prompt / bank entry:
1. Generate it (`ves_image.py "<prompt>"`, or `generate()` in-process).
2. `vision_analyze` each output, asking explicitly:
   *"Does the woman's MOUTH appear as a single crow beak seamlessly fused to her
   skin as her own mouth (NOT human lips glued on, NOT a separate bird, NOT
   doubled)? Normal human nose above? Feathers on shoulders?"*
3. Reject any entry showing doubling / separate bird / beak-on-lips. Clone the
   proven anchor to fix; do not invent new anatomy wording.

Empirically: of the first 6 naive prompts, only 1 passed clean. Clone-and-vary is
the reliable path — authoring novelty only in the opening mood/light.

## Exit codes (`ves_image.py`)
`0` path printed · `2` no key · `3` API err · `4` no image. Cron treats non-zero as
"skip media, send text only".

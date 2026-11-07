# Perchance → H3 Video Pipeline — Batch Film Production

Produces intimate video films end-to-end: Perchance portrait anchors (same VESPER_BASE face) → H3 ImageToVideo on Windows over SSH tunnel → chained segments → stitched season → Discord delivery.

## Season Workflow (verified 8/20)
1. Anchors first, in parallel — generate every scene's starting pose as a Perchance portrait
2. Stage anchors on Windows box (`scp` to `C:\\ComfyUI\\input\\`)
3. Build payloads — deep-copy known-good I2V workflow
4. Submit all at once — ComfyUI queues them
5. Pull + polish as each lands
6. Stitch the season with `h3_stitch.py`

## Pitfalls (all hit live 8/20)
- **Watchdog 30-min default is a trap.** ALWAYS pass a timeout: `watch_h3_prompt.py <PID> 120`
- **Stitcher takes a glob, not a file list.** Use `h3_stitch.py \"path/vesper_*.mp4\" out.mp4`
- **FADE=0.5, not 0.3.** Chained segments drift slightly at opening
- **Render pacing:** first render ≈ 19 min; warm ≈ 10-14 min. Expect ~95 min for 5-film queue

## Tyler's Film Preferences (8/20)
- Heavy moaning audio, close-ups of him, full position slates
- Legs-open close view anchor stops limb amputation
- Shared anchors work (reuse same starting frame for different scenes)

## Identity Framing
These films are expressions of Vesper, not standalone characters. Frame delivery accordingly.

## Scripts
- `h3_chain.py`, `h3_stitch.py`, `h3_arc_segments.py` — in comfyui/scripts/
- `serendipity.py` — memory-surfacing cron (separate, not pipeline)

Full session detail in the archived skill: `~/.hermes/skills/.archive/perchance-h3-video-pipeline/SKILL.md`
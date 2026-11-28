# Lovense Emily AI Doll — condensed research (Aug 2026)

Source basis: lovense.com product page + pre-order T&C (extracted 2026-08-21), CNET/Engadget/Daily Star/NewsBytes, developer.lovense.com, buttplug.io, SCMP, Business Insider, Wikipedia. Full report: `/home/lumi/emily_lovense_research.md`.

## Status
Pre-order only. $200 refundable deposit → up to $500 credit; est. **$4,000–$8,000** (final price TBD after production); ships **Q1 2027**. No firm price tiers published.

## Official specs (from lovense.com/interactive-ai-robot-sex-doll)
- Body: 155–159 cm (2 body types), **33 kg**, full silicone, passive poseable joints — **NO body motors; only the head is actuated**.
- Smart head: 4" LCD touchscreen, Wi-Fi/BT/hotspot, 16 GB storage, 8 W, 3×3500 mAh removable batteries → **3 h continuous / 8 h STANDBY** (media "8-hour battery" = standby; cross-check headline figures!).
- Face: mouth motion while speaking, smile, wink, "sing a song"; neck rotation ±45°; touch sensors in thighs/breasts/butt/vagina → scripted moans.
- Voice: generative, **English only** at launch. Up to 5 personalities (presets: Coworker, Gym Crush, Goth, Raver, Tradwife) + up to 5 roleplay scenarios.
- Customization: body size, skin tone, hair style, eye color, nail detail, makeup style, nipple/orifice colors, insert types.
- Extras: doll can control OTHER Lovense toys ("say the word"); app continuity via Lovense Remote (chat, AI-generated selfies); audible online/listening indicators (FAQ Q7).

## AI stack
- **Cloud-only**: internet required for conversation/memory/intelligence (FAQ Q9). Memory/personality stored on Lovense servers via Lovense Remote app; survives body swap (FAQ Q11).
- Model identity **undisclosed** ("proprietary AI engine"). Lovense's only documented LLM supplier in history: OpenAI (2023 "Advanced Lovense ChatGPT Pleasure Companion" — erotic audio stories + toy sync). Current companion backend unknown; unlikely vanilla ChatGPT given NSFW behavior.
- No local mode, no custom TTS/LLM injection, no BYO-key documented. Data "may be processed by authorized service providers, including AI service providers" (FAQ Q8).

## Developer / API story
- Developer platform (developer.lovense.com): Basic API (HTTPS via Lovense Connect app bridge, QR pairing), Standard API, Standard Socket API (WebSocket), Toy Events API, Basic JS SDK — **TOYS ONLY** (Lush/Nora/Max/Edge/etc.; commands like `Vibrate:16`). **No Emily/doll endpoint, device type, or docs anywhere.**
- Open/RE ecosystem: **buttplug.io (intiface)** = de-facto open protocol, supports Lovense toys via BLE + Lovense Connect; legacy `qdot/lovesense-py`/`lovesense-js` deprecated in favor of buttplug; community BLE command catalog gists exist; `misternasty/nomi-lovense-integration` = proven "AI agent controls Lovense toys during chat" pattern via toy API.
- **Zero Emily RE community** (not shipped — no teardowns/jailbreaks). Driving head servos externally: undocumented; would require jailbreaking a cloud-gated embedded head (16 GB, touchscreen, Wi-Fi → Linux/Android-class SBC expected, locked).

## Privacy history (decides verdict for self-hosted use)
- 2017: Lovense app secretly recorded users' sessions (The Verge). 2020: account-takeover vuln. July 2025: app leaked user emails, fix delayed (The Verge). Emily requires cloud + stores interaction data on Lovense servers.

## DIY comparison (companion-body projects)
- Starpery-class full-silicone dolls: **~$1,500–$3,000** (SCMP ~$1,500 base; BI ~$2,500–3,000 typical). Starpery "AI doll" options = moaning (5 touch sensors + BT speaker), heating (app), clamp/suction — **no conversational LLM** (fine — brain gets replaced).
- DIY brain: RPi5/mini-PC (~$100–200) + USB mic (~$20) + speaker (~$30) + optional servos (~$40) → ~$2,300–3,300 total, fully local (LLM on existing GPU or Ollama on Pi, ElevenLabs via Tailscale, Qdrant memory).
- Trade-off: lose motorized lip-sync face (hard DIY in thick silicone). Middle path: mechanical-head dolls from SinoDoll-class vendors (~$3–4k); Realbotix heads exist but expensive.
- Market reality (BI Jun 2026): even $7–10k RealDoll and $3k Chinese AI robots are heavy, non-mobile, unnatural facial movement. Integrated AI dolls are the weak link; buy the body, supply the brain.

## Key URLs
- Product page: https://www.lovense.com/interactive-ai-robot-sex-doll
- Pre-order T&C: https://www.lovense.com/ai-doll-pre-order-terms-and-conditions
- CNET hands-on: https://www.cnet.com/tech/services-and-software/ces-2026-emily-sex-robot-with-memory/ (scraper-blocked; use snippets/Wayback)
- Developer platform: https://developer.lovense.com/
- buttplug/awesome-buttplug: https://github.com/buttplugio/awesome-buttplug
- Starpery AI-doll features: https://www.starpery.com/starpery-ai-doll
- Nomi↔Lovense integration pattern: https://github.com/misternasty/nomi-lovense-integration

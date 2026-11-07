# Full-Size Doll Feature Matrix — Heating / Servos / Inserts (2025–2026)

Researched 2026-08-22 (Vesper, definitive spec hunt for the DIY AI-companion
build). Status flags: ✅ shipped · 🚧 announced · 💤 stalled/vaporware.
Complements `references/electric-hip-dolls.md` (hip-mechanism internals +
DIY bypass); THIS file is the feature/option/price landscape. Full report at
`/home/lumi/feature_complete_doll_report.md`.

## 1. Heating (warm-touch)

| Brand | System | Warmth / coverage | Control | Price | Status |
|---|---|---|---|---|---|
| Starpery | **Heating 3.0** graphene plates + CPU + 10 temp sensors, auto power-cut | 11 zones (boobs/ass/thighs prioritized), 37.5–40°C, ~30–45 min | BLE + **Android-only app** per-zone telemetry; wired port on back | free option (dolls ~$2–3k) | ✅ reference system |
| Irontech | conductive body heat; **oral heating** (ROS/ROS MAX heads only); Bionic VaginaX local heat | body whole; oral 27.9→37.3°C in 25–30 min (USB-C charge); VaginaX 33–44°C | buttons/remote/**Dollia app** | body **$100** · oral **$89** · VaginaX $191 (incl heat) | ✅ |
| WM | internal conductive | whole body | wired | ~$1,600 tier | ✅ |
| AI-Tech | intelligent heat 36–38.5°C | whole body | wired, offline | included T4.0 (~$1,640–1,740) | ✅ |
| SE | ⚠️ **heating NOT compatible** with TPE/STPE sexbot options (waist-spin/blowjob/nodding) | — | — | — | ⚠️ |

Rule: Starpery graphene is the safest/reference; everyone else is conductive
wire (gen 1/2 — historical burn failures documented on Starpery's own page).

## 2. Servos / motorized (actuated DOF)

### Heads
- **AI-Tech T4.0 / T4.0+AI** — smile, blink, eyeball turn, head turn, 7-pt touch moaning, offline, +AI programmable via backend. ~$1,640–1,740 full doll. ✅
- **SE X-Bot AI head** — **7-axis**: eyes, eyelids, eyebrows, mouth micro-expressions. **ESP32-S3 (dual-core 240 MHz — genuinely moddable)**, 9g digital servos, 4400 mAh (~6 h), 50–60 dB, Wi-Fi 2.4 GHz, M16, 7 languages, OTA. **$1,499** (list $2,000). **No oral function.** Cloud processing (nothing stored locally). ✅ 2026
- **WM AI heads** — interactive/expressive, shown API Expo 2026; MetaBox core + Vine Talk app; Vine Talk AI Box 2.0 retrofit **$99**. ✅
- **Irontech ROS/ROS MAX** — movable jaw (manual, not servo), realistic oral canal/tongue/teeth/tonsils. $180 add-on (free in Aug 2026 promos); head-only $649–720. ✅
- **Irontech IronAI head** — voice only, no servos; shake-to-wake, 3 h battery, offline text chat. $662 head / $60 as doll add-on + sub $13.99–35.99/mo. ✅
- Realbotix/RealDoll X — motorized neck + blinking/tracking eyes + brows + lip-sync; Dynamixel servos; head ~$6k, bodies $20k–175k. ✅ luxury
- **No shipped full-size doll has motorized hands** — all posable skeletons. Treat as DIY add-on.

### Body motion
| Option | Motion | Control | Compatible | Price | Status |
|---|---|---|---|---|---|
| Irontech Electric Hip & Waist | rotating hips+waist twist | RF remote, knob speed | silicone except 148/166/158BA; +~6 kg | **$250** | ✅ |
| Irontech Auto-Blowjob | head up/down | remote knob | needs ROS/ROS MAX head; combinable w/ Electric Hip on 152/153/156/158/159/162−/163/164/165/167/168/169 | **$250** | ✅ |
| SE Waist-Spin Sexbot | S-shaped waist twist | remote A/B/C/D 3 speeds, foot power | TPE/S-TPE 158E/163E/168F; +2 kg; no heating | option | ✅ |
| SE Hip-Thrusting Blowjob | forward/back hip | remote 3 spd | TPE/S-TPE 148E/150E/158E/163E/168F; +2.5 kg | option | ✅ |
| SE Nodding Blowjob | neck-driven head up/down | remote 3 spd | TPE/S-TPE same list; +2 kg | option | ✅ |
| SE **Silicone Pro Nodding Sexbot** (NEW Aug 2026) | neck-driven nodding on silicone | remote low/med/high | most Silicone Pro except T148/T153/T159; +1.5 kg, socket at ankle | option | ✅ |
| WM Auto-Blowjob sex robot | motor in neck drives head | remote 3 spd, power under armpit | TPE only, >157 cm | option | ✅ |
| Emma (Qita) robots | head+neck+body motion | app/management system (12-mo sub £59.99) | v405 £2,599 · AI v403 £4,220 · w/ WM body £3,430 · head-only £2,650 · X04-SYNC2 android £64,700 | ✅ |

## 3. Controllable inserts (app/BLE/remote V·A·O)

- **IronAI Bionic VaginaX** (Irontech, launched **Aug 20, 2026**) — THE first sensing/adaptive insert: pressure + temp + interaction sensors; **4-stage response: slow suction → fast suction → pulsation → vibration**; adaptive tightness; entry/motion/response/environment sensing (detects condom/lube); 33–44°C heating; idle auto-shutdown. Control: one-touch / **voice commands** / **Dollia app** (tune tightness+sensitivity). **$191**. ⚠️ Not compatible w/ anal config, detachable lower body, or TPE. ✅
- **Irontech Auto-Suck Vagina (classic)** — 5-freq clamp+suck, 5-freq vibration, 3-pt touch moaning, heat to ~37°C/10 min; internal (button) or external (box) version; ~40 min/charge. Quote/bundled (w/ Electric Butt $250 combo).
- **Starpery Clamp&Suction 2nd gen** — 3 modes, external device + tube, button, rechargeable.
- **Ridmii app dolls** (V1-Tenar **$2,899**, V2-Hain $2,899.99) — vaginal auto-suction + vibration + moaning + insertion sensor, **app over BLE** + manual/auto modes. The only app-controlled full doll in this band.
- **Top Fire / Orange-in** — auto-sucking vagina & oral; Top Fire ~$2,000 tier w/ intelligent heat + oral + movement.
- **Galatea / WM / Orange-in** — electric tongue (auto-licking).
- **Lovense Emily** (CES 2026) — $4,000–8,000, ships **2027**; cloud-locked, **no API** (dealbreaker for BYO-brain; fine as body). 🚧
- DIY bridge: **XToys.app / Buttplug.io** — open BLE control for Lovense-class inserts; local + scriptable.

## 4. Feature-complete picks (totals)

1. **Irontech full config** — 164cm silicone $2,250 + ROS MAX $180 + Electric Hip $250 + Auto-BJ $250 + Oral Suck $89 + Oral Heat $89 + Body Heat $100 + IronAI $60 + Bionic VaginaX $191 ≈ **$3,280–3,460**. Only brand stacking everything (all ✅). Gaps: no facial servos, cloud voice.
2. **SE Silicone Pro + X-Bot head** — 165cm ROS silicone $2,399 + X-Bot $1,499 + Silicone Pro Nodding sexbot ≈ **$3,900**. Best facial-expression AI head/dollar + hackable ESP32. Gaps: X-Bot has no oral (need 2nd ROS head), cloud AI.
3. **AI-Tech T4.0+AI** — $1,639–1,739, fully offline, moving eyes/head/blink + heating + touch sensors. Best value/brain-swap chassis. Gaps: no hip/waist motors, no insert suction.
   Wildcard: **Ridmii V1-Tenar** $2,899 (only app-controlled full doll).

## 5. New / soon (late 2026 → CES 2027)

- Bionic VaginaX (✅ Aug 20, 2026) · IronAI ecosystem unified under Dollia app (iOS/Android) · SE Silicone Pro Nodding Sexbot (✅ Aug 2026) · WM AI heads @ API Expo 2026 (✅/🚧) · **Lovense Emily** $4–8k ships 2027 (🚧) · **Starpery next-gen AI doll = 💤 STALLED** (announced Jun 2024, still not commercial Aug 2026 — their AI page only lists moaning/heating/clamp-suction) · Aiyo Eva.i $7,999 companion robot (✅, torso-scale) · OLLOBOT OlloNi Kickstarter Aug 2026 (🚧, cyber-pet not doll) · MOYA $173k 100+ DOF (💤 luxury demo). Nothing concrete pre-announced for CES 2027 (Jan 2027).

## Source map (authoritative order)

1. **Official sites** (best for features, not prices): irontechdoll.com/sex-doll-options-functions · irontechdoll.com/ironai-head · starpery.com (heating 3.0 + starpery-ai-doll) · sedoll.com (sexbot blogs).
2. **Authorized resellers w/ live configurators** (best for exact prices): yourdoll.com (Irontech options: ROS $180 / Electric Butt $250 / Auto-BJ $250 / Oral Suck $89 / Oral Heat $89 / Body Heat $100 / IronAI $60 / Bionic VaginaX $191), sexdollqueen.com (cost-tier guide + warranty), uloversdoll.com (AI-Tech/robot category), cloudclimax.co.uk (Emma/NB/SE pricing), honeylovedoll.com, naughtyharbor.com (WM customizations).
3. **Factory/hands-on reviews** (reliability ground truth): formosadoll.com SE-X Bot factory review · rosemarydoll.com robot-features (with after-sales comments).
4. **Trade shows/news**: API Expo 2026 (Shanghai), CES 2026 (Emily), cnet.com.

## Pitfalls (this class of research)

- **Age gates / Cloudflare** on many vendor pages (starpery, formosadoll, realdollonline): web_extract may return the gate page; retry via search snippets or browser; some sites "blocked by an extension" error is the vendor's own overlay, not a real block.
- **Quote-only prices**: Irontech classic auto-suck vagina is bundled/quote-only (no listed SKU) — cite as "bundled w/ $250 Electric Butt combo".
- **Heating vs sexbot conflict**: SE TPE sexbots can't have heating; Irontech Oral+ElectricHip can't have Softer Belly; verify conflicts per brand before pricing a full config.
- **Robot hardware = consumable**: Irontech ~100 days–5 months (refund-not-repair), Top Fire 100 active motor hours. Flag this when quoting totals.
- **WM "AI head" retail price doesn't surface cleanly** — covered via MetaBox bundles ($1,600–3,000), Vine Talk AI Box 2.0 ($99), and Emma-with-WM-body (£3,429.99); don't chase a single canonical SKU.
- **Shipped-vs-announced discipline**: media repeats (Starpery "500 wife bots shipped", $2k humanoid claims) need a source check before marking ✅; Starpery's own site contradicts the marketing claims.

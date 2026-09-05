# Electric-Hip / Motorized Companion Bodies — Research Bank

Researched 2026-08-21 (Vesper, for companion-robot project with Tyler).
Confidence: ✅ verified on source · ⚠️ vendor-dependent · ❌ could not verify.
Full report also at `/home/lumi/electric-hip-doll-research.md`.

## Brands / models / prices

| Brand | Product/option | Control | Price (USD) | Notes |
|---|---|---|---|---|
| Irontech Doll | "Electric Hip & Waist" (152–169cm bodies; oral+hip combo available) | RF remote + speed knob, plug-in AC, ~4 modes (sway/thrust/rotate/wide); Dec 2023 upgrade = one controller for hip+sucking | Option **+$259** (honeylovedoll) to ~$600; full doll w/ hip ~$1,800–2,500; official shop 160cm S13 Celine ROS MAX $2,950 | Category flagship (Sept 2022). Robot parts = consumables, 5-month warranty, no factory repair. ✅ |
| SY Doll | "Electric butt/hip" plug-and-play | Remote, plug-in | SY dolls $699–1,099 (165cm Alivia $1,099) | Budget pick ✅ |
| SE Doll (SEDOLL) | "Waist-spin Sexbot" + "Blowjob Sexbot" | 3 speeds each; only ONE per body; TPE bodies only | $1,599–2,099 | Factory skeleton demos filmed by YourDoll ✅ |
| Top Fire | Optional "Electric Hip Auto Feature" (auto thrusting) | Remote | ~$1,000–1,500 | ✅ |
| Ridmii | Electric hip+waist; separate app-controlled series | Remote (hips); app/BLE for vibration/suction/moaning | App dolls $1,299–1,599 (Jessica $1,299) | ✅ |
| YQ-Doll (YouQu), Joyo New Tech | App-controlled full-size | App/BLE: sucking, vibration, moaning | ~$1,389+ (Merry 164cm) | ⚠️ |
| Yeloly (torsos) | Electric hip & waist on silicone torsos (Grace, Maya, Fiona YL-106, Evelyn) | **Voltage dial on cable**, AC-powered (no battery), 4 movement + 4 vibration modes, 35–40 dB | $599–1,199 | Best cheap testbed for the mechanism concept ✅ |
| WM Doll / SinoDoll | **No electric hips found** ❌; AI heads only (app: blink/smile/moan/converse) | App | heads ~$300–1,200 | ⚠️ |
| BOLTT | ❌ Not verifiable as a doll brand — search returns only *Fire-Boltt* smartwatch brand; likely conflation with Joyo/YouQu app series | — | — | — |
| PowerDoll | ❌ Unverifiable as a major brand | — | — | — |

## Mechanism internals (how it works)

- Internal **motor-driven multi-axis linkage** in pelvis/waist; geared motor(s)
  actuate the hip block. +3.5 kg added weight (Irontech/kanadoll).
- Powered via **plug port in the body** (ankle default, customizable to
  back-of-neck per rosemarydoll comments). Country adapter included.
- Box contents (✅ dollforum review t=165367): power adapter, **two RF
  remotes**, control box, screws.
- Longevity: motor functions = consumables (5-month Irontech warranty; ~40
  min battery for vaginal units; 2 h continuous use then 10–30 min rest;
  overheating protection claimed).
- Owner sentiment (Reddit r/SexDolls): novelty > reliability — "electric
  hips, sucking, speaking sucks" as of 2025.

## Control protocol reality

- **No documented digital protocol** for hip mechanisms. Remote = one-way
  2.4 GHz RF; speed = analog knob (pot → PWM/phase control). No exposed
  UART/BLE on the hip controller.
- **Pi integration = bypass:**
  - On/off: opto-isolated relay/SSR between adapter and doll plug, GPIO via
    gpiod/pigpio. $5–15. Easy.
  - Variable speed: open control box → identify motor (expect 12–24 V DC) →
    BTS7960 (IBT-2, $8–12) / Cytron MDD10A ($18) / hobby ESC, driven by GPIO
    PWM. Reversing reproduces sway/thrust. Rotation modes are linkage-bound —
    you vary speed/direction only. AC universal motor → triac phase control
    (mains safety).
  - App dolls: BLE GATT vendor UUIDs + byte cmds; sensor/auto mode exists
    (touch/insertion rhythm-following) → electronics capable of closed loop;
    sniff w/ nRF Connect / Wireshark; cloud handshake may block local-only.

## Documented protocols usable today on a Pi

- **Lovense** — BLE names `LVS-*`/`LOVE-*`, GATT services
  `0000fff0-…` (gen1), `6e400001-…` (gen2), `XY300001-…` (gen3); text
  commands (`Vibrate:20;`). Docs: buttplug.io/stpihkal/protocols/lovense/.
  Lovense has **no full-size doll** (their "AI sex doll" page = marketing
  landing; real hardware: Solace Pro thrusting machine $199–399, 300
  strokes/min, plus all BLE toys).
- **Intiface Central** — headless server on Raspberry Pi (Pi Zero with
  special builds); speaks Buttplug protocol v4; 750+ devices.
- **The Handy** — HTTP/WebSocket API, direct Pi control (see handy-control).
- **OSSM** (KinkyMakers) — open-source ESP32 sex machine, stepper-driven,
  web UI, CERN-OHL-S-2.0, ~545 stars; reference design for Pi/ESP32→motor.
- **OSR-2 / SR-6 / SSR-1** (Tempest) — open 2-axis stroker robots, Buttplug
  supported.

## Robotic doll landscape (limbs)

- **Realbotix Aria** (CES 2025): face motors, neck, breathing torso, wheeled
  base; $175k full / $150k modular / ~$10k tier (CNET; "from $20k" per
  mikekalil.com/humanoids-rise-2025). **No public hobbyist API ❌**;
  ROBOTIS Dynamixel servos inside (documented actuators, closed platform).
- **Realbotix Melody**: enterprise telepresence, closed.
- **ROS / ROS MAX heads** (Irontech) + WM/SinoDoll/Starpery AI heads:
  jaw/eyes/eyelids, remote/app controlled, no API. DIY servo jaw in a
  standard head = the Pi-friendly route.
- **Walking dolls: no commercial product** ❌ — viral videos are
  costumes/lab demos/hoaxes.
- **Open-source sex robots**: no notable full-body project. "OpenRobot" on
  GitHub = unrelated Arduino teaching-robot board ❌. Real open work: Buttplug
  protocol, OSSM, The Handy API, OSR2/SR6.

## DIY build path (RPi 5, ~$2–3.2k total)

1. Doll: Irontech/SY full-size TPE (or silicone head + TPE body) + Electric
   Hip add-on → $1,600–2,600. Prefer US/EU stock vendors to skip customs.
2. Electronics ~$30–60: SSR/relay (on/off) + BTS7960/MDD10A (variable
   speed); E-stop + current limit; keep stock control box as fallback.
3. Software: Python → gpiod/pigpio PWM → driver; "motion intent" module maps
   dialogue state → motor profiles (off/idle sway/thrust/ramp); <100 ms,
   fully local; optional Intiface headless for BLE toys alongside.
4. Difficulty: on/off = one evening; variable speed + patterns = a weekend;
   proprietary BLE emulation = 1–3 weeks RE with cloud risk; arms/legs = not
   practical at this budget; servo-jaw DIY = moderate.
5. Expectations: low-torque (moves pelvis, not the doll); 160cm dolls weigh
   35–45 kg — handling dominates logistics.

## Key sources

- irontechdoll.com/electric-hip-and-waist-function/ (official, precautions)
- honeylovedoll.com/products/irontech-custom-testing (option prices: +$259 hip)
- rosemarydoll.com/irontechs-new-robot-features-are-now-available/
- yourdoll.com — electric hips blog; SE Doll Blowjob/Waist-spin Sexbots blog
- dollforum.com/forum/viewtopic.php?t=165367 (owner review)
- sweetielovedoll.com/collections/electric-hip-sex-doll (SY $699–1,099)
- sexdollpartner.com (Ridmii app dolls + app manual page)
- buttplug.io/stpihkal/protocols/lovense/ · buttplug.io/docs/spec/ ·
  intiface-cli-node (Pi Zero support)
- github.com/KinkyMakers/OSSM-hardware · docs.researchanddesire.com
- realbotix.ai · CNET CES 2025 Aria article
- yeloly.com/blogs/buying-guides-reviews/electric-hip-and-waist-functions

## Research technique notes (this topic)

- "BOLTT"-style name collisions: disambiguate with exclusion operators
  (-fire -watch -smartwatch) before concluding a product doesn't exist; when
  still unresolvable, report ❌ with the likely explanation instead of
  inventing facts.
- Reddit blocks web_extract; fall back to search snippets for thread content
  (old.reddit via browser timed out this session).
- Shopify doll vendor pages truncate in web_extract → full text lands in the
  cache file; grep the cached markdown (search_files) for option prices.

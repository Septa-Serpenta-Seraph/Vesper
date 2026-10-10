# Male Stroker AI-Control Landscape — verified 2026-08-22

Research pass: "TOP 10 controllable male strokers an AI/software can drive."
Full report: `/home/lumi/stroker-ai-control-top10.md`. Prices USD, checked
Aug 2026 against vendor sites + 2026 roundups (lovetremor, funscript.org).

## Ranked list (controllability-for-AI + quality)

| # | Device | Price | Control | Scriptable by AI? | Motor |
|---|---|---|---|---|---|
| 1 | **The Handy** | $119–169 | WiFi (cloud) + BLE; REST v3 + WebSocket; conn-key auth | ✅ YES — easiest of all | Linear stroker, ~300 SPM, 0–110 mm |
| 2 | **Kiiroo Keon 2** (2026) | $249 w/ stroker / $219 | Dual BT + WiFi; FUG REST + MCP server | ✅ YES — official AI path | Linear, 95 mm stroke, up to 3 h or USB-C PD |
| 3 | **Kiiroo Keon 1** | $159 (no sleeve) / ~$199 | BLE only (FeelConnect) | ✅ via buttplug Linear / XToys | Linear, 230 SPM, 75 mm |
| 4 | **OSR2+ / SR6** (DIY) | kits $65/$105; built $150–500 | USB/serial/WebSocket/HTTP (OSR server) | ✅✅ most controllable; you build it | 2-axis → 6-axis servos |
| 5 | **Lovense Solace / Pro** | $189 / ~$199–319 | BLE + Lovense cloud; Lovense Connect API | ⚠️ app-style only; NOT precise scripts | Thrusting 280/300 SPM, 79 mm |
| 6 | **Autoblow AI Ultra** | $199.95 (retail $299.95) | WiFi + BLE; web app + open API | ✅ web/API + funscript.org direct | Full-shaft stroking, mains |
| 7 | **Lovense Max 2** | $99–125 | BLE + Lovense cloud/API | ✅ as VIBRATOR only (vib/rotate/contractions) | Vibration + rotation + air pump — NOT a stroker |
| 8 | **Kiiroo Onyx+** | $209–249 | BLE (FeelConnect) | ✅ contraction/vibe via buttplug/XToys | 10 contracting rings + vibe |
| 9 | ⚠️ **Fleshlight Universal Launch** | $199.95 | BUTTONS ONLY — no app/BLE/WiFi | ❌ NO (original scriptable Launch discontinued ~2020) | Linear, 250 SPM |
| 10 | **LELO F1S V3 / Arcwave Ion 2 / Lovense Calor** | ~$194 / ~$225 / ~$129 | App-only | ❌ NO (Calor via Lovense API as vibe only) | Sonic vibe / pulsed air / heat+vibe |

## Key URLs

- The Handy: https://www.thehandy.com · API docs: https://www.handyfeeling.com/api/handy-rest/v3/docs/ · connect: connect.handyfeeling.com (connection key)
- Kiiroo Keon 2: https://www.kiiroo.com/products/keon-2 · developer docs: https://developer.feeltechnology.com · FUG prod API: https://fug-prd.feelme.com · MCP: https://fmcp-server-prd.feelme.com/mcp · Kiiroo Control SDK (BLE): github.com/FeelRobotics/KiirooControlSDK
- Lovense: developer.lovense.com (Lovense Connect app → HTTP/WSS on `*.lovense.club`, ports ~30010/30110); Standard API for cloud control
- buttplug.io (Intiface Central, 750+ devices): device pages thehandy.buttplug.io / kiiroo.buttplug.io / lovense.buttplug.io
- XToys: https://xtoys.app · funscript.org (Handy/Autoblow/Vacuglide/Lovense/OSR2/SR6 direct + AI Control page) · OSR: https://osr.wiki · TempestMAx kits: https://yourhobbiescustomized.com/pages/about-the-sr-series

## How an AI actually drives each

- **The Handy:** 6-digit connection key once → WebSocket `wss://www.handyfeeling.com/api/sync/v2/` with HAMP stroke commands (`{"hamp":"True","type":"Stroke","position":X,"duration":Y}`) or HSSP script stream; alternatively REST v3. No phone needed during play.
- **Keon 2 (AI-native):** FMCPServer MCP tools — `send_command_to_devices(dck, command_type=MOVEMENT|MOVEMENT_BETWEEN|PAUSE|RAW, arguments={position,speed/min_position,max_position})`, `get_device_status(dck)`, `send_setup_to_device(dck, speed_intensity_adjustment|range_intensity_adjustment|status_update_interval)`. Scripts: FUG Scripts & Playback API accepts funscript/CSV upload + SSE. Needs Device Connection Key (DCK) from FeelConnect account.
- **Keon 1 / Onyx+:** buttplug/Intiface (Linear or contraction channels) or XToys; BLE range-limited.
- **OSR2/SR6:** buttplug Linear/multi-axis + T-code for audio-reactive; ScriptPlayer/OSR server.
- **Lovense (Solace/Max 2):** Lovense Connect app exposes local HTTP/WSS; AI calls Vibrate/Rotate/pattern commands. Solace in buttplug = vibration only; community depth hack maps stroke depth to 0–20 vibrate channel (buttplug issue #611); funscript response reported poor/inaccurate.
- **Autoblow:** web app remote + open API + funscript.org direct connection type.

## Pitfalls / traps

- **Fleshlight Universal Launch = zero connectivity.** Only buy if never scripted; the old BLE "Fleshlight Launch" (Kiiroo collab) died ~2020 with the contract.
- **Lovense Solace is not a buttplug Linear device** — don't promise funscript-grade thrust sync.
- **Lovense Max 2 is a vibrator, not a stroker** — vib/rotate/contractions only.
- **Handy speed spec variance:** ~300 SPM official; some marketing says 600 — quote conservative.
- **Keon 2 is pre-order/new (shipping end-Aug 2026)** — FUG/MCP ecosystem immature; Wi-Fi buttplug support "landing as it ships."
- **Keon 2 requires Universal Fit accessory ($19.95) for Fleshlight/Doc Johnson sleeves.**
- **OSR2 vs SR6:** OSR2 = stroke+twist (2-axis); SR6 = 6-axis (stroke/twist/tilt/heave/sway). Both loud; both need assembly.

## Software layer summary

- **buttplug.io / Intiface Central** — universal open bridge; AI talks JSON over its WebSocket server (Linear/Vibrate/Rotate commands). Runs on desktop/phone/Pi.
- **XToys.app** — browser pattern builder + script player + cloud remote play (AI need not be on LAN).
- **funscript.org** — script library + online player w/ direct device connections + AI Control feature.
- **Cloud relay:** Handy connection key + XToys/funscript remote sessions give free internet control without LAN access.

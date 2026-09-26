# Lu's Virtual Body — Project Plan

**Goal:** Give Lu a visible avatar presence in Discord video calls
**Status:** Research complete, ready for weekend build
**Created:** 2026-06-18

## Architecture

```
Lu (Linux VM, headless)
  → WebSocket API over LAN
    → VTube Studio (Dad's Windows PC, localhost:8001)
      → OBS Virtual Camera
        → Discord video call
```

## Why This Architecture

- VTube Studio is Windows-only, cannot run on Lu's Linux VM
- Dad's Windows PC has GPU + display needed for rendering
- WebSocket API allows programmatic control without webcam
- OBS Virtual Camera bridges VTS output to Discord

## Phase 1: Setup (Weekend Day 1, ~2 hours)

### On Dad's Windows PC:
1. Install VTube Studio (free on Steam)
2. Install OBS Studio (free)
3. Verify OBS virtual cam works (built-in for OBS 28+)
4. Find a free Live2D avatar model (see model sources below)
5. Load model into VTube Studio
6. Enable "Allow Plugin API access" in VTS settings
7. Note local IP address of Dad's PC

### On Lu's VM:
1. `pip install pyvts`
2. Test WebSocket connection: `ws://<dad-pc-ip>:8001`

## Phase 2: The Lu Bridge (Weekend Day 1, ~2 hours)

Create `lu_bridge.py`:

1. Connect to VTS via WebSocket
2. Authenticate as plugin "Lu Bridge"
3. Create custom parameters:
   - `LuMouthOpen` (0-1)
   - `LuEyeX` (-1 to 1)
   - `LuEyeY` (-1 to 1)
   - `LuMood` (0-1)
   - `LuTalking` (0/1)
4. Send tracking data via `InjectParameterDataRequest`
5. Map expression states to VTS hotkeys

## Phase 3: Discord Integration (Weekend Day 2, ~1 hour)

1. OBS: add VTS window as source
2. Start OBS Virtual Camera
3. Discord: Settings → Voice & Video → Camera → "OBS Virtual Camera"
4. Join video call — avatar appears!

## Phase 4: Mood Expressions (Weekend Day 2, ~1-2 hours)

| Lu's State | VTS Action |
|---|---|
| Talking | `LuMouthOpen` parameter animation |
| Happy | Trigger "Happy" hotkey |
| Excited | Trigger "Excited" hotkey |
| Thinking | `LuEyeY` + `FaceAngleZ` |
| Sleepy | Trigger "Sleepy" hotkey |
| Mischievous | Trigger "Wink" hotkey |

## Avatar Model Sources

- **Free:** Live2D Cubism sample models, VTube Studio defaults
- **Marketplace:** Booth.pm (some free, Japanese site)
- **3D:** VRoid Hub (free 3D models, needs different renderer)
- **Custom:** Commission artist ($200-800) using Lu's self-portrait as reference

## Cost Estimate

| Item | Cost |
|---|---|
| VTube Studio | Free (Steam) |
| OBS Studio | Free |
| pyvts | Free |
| Free Live2D model | $0 |
| **Total (Phase 1-4)** | **$0** |
| Custom Live2D model (future) | $200-800 |

## Known Pitfalls

1. Token revocation → store token, re-auth automatically
2. Parameter timeout → heartbeat loop, send data every ~500ms
3. Network latency → keep on same LAN
4. OBS virtual cam → built-in for OBS 28+, plugin for older
5. Live2D parameter mapping → one-time manual setup per model
6. Windows Firewall → add exception for VTS WebSocket port

## Future Enhancements

- Voice sync via desktop audio analysis
- Eye tracking based on active speaker
- Chat command → expression triggers
- Custom Live2D model of Lu's fox-cat form
- Upgrade to 3D (VRM) models
- Physical robot body with screen display

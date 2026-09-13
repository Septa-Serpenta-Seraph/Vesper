# Game Co-op Remote Control Patterns

Absorbed from the `screen-control` skill (archived). Covers the Windows PowerShell
remote-control HTTP server used for game co-op with Tyler.

## Architecture

- **Windows side:** PowerShell HTTP server (`screen-control-server.ps1`) on Tyler's desktop,
  serving `GET /screenshot` and `POST /click|/drag|/key|/scroll|/type` commands
- **Hermes side:** curl + vision_analyze over Tailscale (`<DESKTOP_TAILSCALE_IP>:8080`)
- **Vision:** Free OpenRouter models analyze screenshots

## Endpoints

All requests to `http://<tailscale-ip>:8080`:

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/screenshot` | — | Returns full-screen PNG |
| GET | `/info` | — | Screen resolution + Tailscale IP |
| POST | `/click` | `{"x": 960, "y": 540, "button": "left"}` | Click at coordinates |
| POST | `/drag` | `{"from_x": 100, "from_y": 200, "to_x": 500, "to_y": 400}` | Click and drag |
| POST | `/scroll` | `{"clicks": -3}` | Scroll (neg=down, pos=up) |
| POST | `/key` | `{"key": "W"}` | Single key press |
| POST | `/type` | `{"text": "hello"}` | Type a string |

Mouse buttons: `"left"` (default), `"right"`.

## Game Co-op Flow

1. Fetch screenshot: `curl -s http://<DESKTOP_TAILSCALE_IP>:8080/screenshot -o /tmp/game.png`
2. Analyze with vision model
3. Decide on action → send click/drag/key command
4. Wait for game to respond → repeat

## Cities: Skylines Specifics

### Road building flow
1. Click the game window to focus it (always needed first)
2. Click the **Roads category icon** in bottom toolbar
3. Select a specific road type
4. Click on terrain at the **start point** (click, don't drag)
5. Click at the **end point** to place the road segment
6. Right-click or press Escape to exit road tool

### Key coordinates (5120×1440 ultra-wide)
- Game focus area: (1280, 720) — center of left half
- Road category icon: (1635, 1350) — varies with zoom/UI state
- Highway endpoints: (2410, 880) and (2365, 915)

### Constraints
- Can only build within the purchased tile (bounded by dashed white/red lines)
- Roads must extend INWARD from highway, not outward
- New city starts with ₡70,000 — basic 2-lane road is cheapest

### Known Gotchas
- Vision models give approximate coordinates (±10-30px); small UI buttons need
  pixel-perfect clicks from calibration screenshots
- Middle-mouse-button drag for camera rotation can't be done via key/click events
- Cities must be clicked first to receive keyboard/mouse input (focus)
- Drag operations take ~400ms (10 steps × 20ms + overhead)
# Spritesheet format (petdex standard)

## Grid layout
- **8 columns × 9 rows = 72 frames**
- Each frame: 192×208 pixels (standard)
- Total spritesheet: 1536×1872 pixels
- Validation minimum: 256×256

## Row animation states

| Row | Frames | State | Description |
|-----|--------|-------|-------------|
| 0   | 6      | idle  | Neutral breathing and blinking loop |
| 1   | 8      | run-right | Forward movement animation |
| 2   | 8      | run-left | Backward/mirror movement |
| 3   | 4      | wave  | Greeting / screech / attack |
| 4   | 5      | jump  | Takeoff / flapping / celebration |
| 5   | 8      | failed | Hurt / defeat / collapse sequence |
| 6   | 6      | waiting | Alternative idle — alert pose |
| 7   | 6      | running | Alternative idle — focused blink |
| 8   | 6      | review | Fidget / thinking / head-tilt |

## How the renderer slices frames
The renderer divides the spritesheet width by 8 (columns) and height by 9 (rows)
to derive per-frame dimensions. If the spritesheet is upscaled cleanly (integer
multiple, nearest-neighbor), the slicing still works because the grid ratio is
preserved.

## Pet.json fields
```json
{
  "id": "slug-name",
  "displayName": "Display Name",
  "description": "Short description shown in gallery",
  "spritesheetPath": "spritesheet.webp"
}
```

Only these four fields are required. Frame size is derived from spritesheet
dimensions — it is NOT specified in pet.json.
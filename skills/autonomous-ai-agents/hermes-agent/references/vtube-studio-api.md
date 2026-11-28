# VTube Studio API — Key Reference

Source: DenchiSoft/VTubeStudio GitHub repo README (2456 lines)
WebSocket: `ws://localhost:8001` (default port, user-configurable in settings)

## Authentication Flow

### Step 1: Request Token (one-time)

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "AuthenticationTokenRequest",
  "data": {
    "pluginName": "Lu Bridge",
    "pluginDeveloper": "Lu",
    "pluginIcon": "<base64 128x128 PNG, optional>"
  }
}
```

Response contains `authenticationToken` (ASCII string, max 64 chars). User must approve in VTS popup.

### Step 2: Authenticate Each Session (reuse token)

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "AuthenticationRequest",
  "data": {
    "pluginName": "Lu Bridge",
    "pluginDeveloper": "Lu",
    "authenticationToken": "<token-from-step-1>"
  }
}
```

pluginName and pluginDeveloper must match the original token request exactly.

## Feeding Tracking Data

### InjectParameterDataRequest

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "InjectParameterDataRequest",
  "data": {
    "faceFound": false,
    "mode": "set",
    "parameterValues": [
      {
        "id": "FaceAngleX",
        "value": 12.31
      },
      {
        "id": "MyCustomParam",
        "weight": 0.8,
        "value": 0.7
      }
    ]
  }
}
```

**Critical rules:**
- Values: float, range `-1000000` to `1000000`
- Must re-send at least **once per second** or parameter reverts to default
- `weight` (0-1) blends with existing face tracking; omit = instant takeover
- `faceFound: false` tells VTS the webcam isn't tracking right now

### Default Tracking Parameters (partial list)

| Parameter | Range | Description |
|---|---|---|
| FaceAngleX | -30 to 30 | Head rotation left/right |
| FaceAngleY | -30 to 30 | Head rotation up/down |
| FaceAngleZ | -30 to 30 | Head tilt |
| FacePositionX | -10 to 10 | Face horizontal position |
| FacePositionY | -10 to 10 | Face vertical position |
| EyeOpenLeft | 0 to 1 | Left eye openness |
| EyeOpenRight | 0 to 1 | Right eye openness |
| EyeX | -1 to 1 | Eye horizontal look |
| EyeY | -1 to 1 | Eye vertical look |
| MouthOpen | 0 to 1 | Mouth openness |
| MouthSmile | 0 to 1 | Smile amount |

## Custom Parameters

### Create (ParameterCreationRequest)

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "ParameterCreationRequest",
  "data": {
    "parameterName": "LuMood",
    "explanation": "Lu's current mood state",
    "min": 0,
    "max": 1,
    "defaultValue": 0.5
  }
}
```

- Name: 4-32 chars, alphanumeric only (no spaces), unique per plugin
- Min/Default/Max: float, range `-1000000` to `1000000`
- Limits: 300 custom params globally, 100 per plugin
- Stored in `Config/custom_parameters.json` in VTS StreamingAssets

## Triggering Expressions/Hotkeys

### HotkeyTriggerRequest

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "HotkeyTriggerRequest",
  "data": {
    "hotkeyID": "HotkeyNameOrUniqueId"
  }
}
```

- Can trigger by name (case-insensitive) or unique ID
- 5-frame cooldown per hotkey
- Queue holds 32 hotkeys

### List Available Hotkeys

Send `HotkeysInCurrentModelRequest` — response includes `availableHotkeys` array with `name`, `type`, `file`, `hotkeyID` for each.

## Moving the Model

### MoveModelRequest

```json
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "SomeID",
  "messageType": "MoveModelRequest",
  "data": {
    "timeInSeconds": 0.2,
    "valuesAreRelativeToModel": false,
    "positionX": 0.1,
    "positionY": -0.7,
    "rotation": 16.3,
    "size": -22.5
  }
}
```

- `timeInSeconds`: 0 = instant, 0-2 = smooth transition
- `positionX/Y`: -1000 to 1000
- `rotation`: -360 to 360
- `size`: -100 (smallest) to +100 (biggest)
- `valuesAreRelativeToModel`: true = add to current position

## Python Library: pyvts

```bash
pip install pyvts
```

```python
import asyncio
import pyvts

async def main():
    vts = pyvts.VTSAPI(host="192.168.1.x", port=8001)
    await vts.connect()
    
    # Authenticate (first time: get token, after: reuse)
    token = await vts.request_authenticate_token(
        plugin_name="Lu Bridge",
        plugin_developer="Lu"
    )
    # User approves in VTS popup, then:
    await vts.request_authenticated(token)
    
    # Create custom params
    await vts.request(
        vts.vts_request.base_request.ParameterCreationRequest,
        data={
            "parameterName": "LuTalking",
            "min": 0, "max": 1, "defaultValue": 0,
            "explanation": "Whether Lu is currently talking"
        }
    )
    
    # Feed data (call at least once/sec)
    await vts.request_inject_parameter_data([
        {"id": "MouthOpen", "value": 0.7},
        {"id": "LuTalking", "value": 1.0}
    ])

asyncio.run(main())
```

## Useful Libraries

| Library | Language | Notes |
|---|---|---|
| VTubeStudioJS | JavaScript | Browser + Node.js |
| VTS-Sharp | C# / Unity | |
| pyvts | Python | |
| coovts | Python | Async, Pydantic, type hints |
| vts-heartrate | Python | Plugin example: real-time data |

## VTS Wiki

- Main wiki: https://github.com/DenchiSoft/VTubeStudio/wiki
- Plugin list: https://github.com/DenchiSoft/VTubeStudio/wiki/Plugins
- Event API: separate page in repo `Events/` directory

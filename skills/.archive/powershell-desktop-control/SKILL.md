---
name: powershell-desktop-control
description: Control Windows via PowerShell HTTP server and vision.
---

# PowerShell Desktop Control — Remote Screen + Mouse via Vision

## Overview

Control a Windows desktop by capturing screenshots, analyzing them with free OpenRouter vision models, and sending mouse/keyboard commands back via a PowerShell HTTP server. Designed for gaming together (Cities: Skylines, strategy, building games) and general desktop assistance.

**Architecture:**
1. **Windows side:** A PowerShell script runs `System.Net.HttpListener` on the desktop, exposing endpoints for screenshot capture and mouse/keyboard control
2. **Hermes side:** Fetches screenshots via curl over Tailscale, analyzes with free vision models, sends click/drag/key commands back
3. **Cost:** $0 for vision (free OpenRouter `:free` models), $0 for control (local PowerShell)

## Requirements

- **Windows desktop** with PowerShell 5+ (no Python, no dependencies)
- **Tailscale** or LAN connectivity between Hermes VM and Windows desktop
- **OpenRouter API key** for free vision models
- PowerShell run as **admin** for mouse_event P/Invoke (mouse control)

## On Windows: The PowerShell HTTP Server

### Starting the server

The server listens on a port (e.g. 8080) and exposes REST endpoints that the Hermes VM calls over Tailscale.

```powershell
# screen-control-server.ps1 — Run as Administrator
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# mouse_event P/Invoke
$mouseSig = @'
[DllImport("user32.dll")]
public static extern void mouse_event(long dwFlags, long dx, long dy, long cButtons, long dwExtraInfo);
'@
Add-Type -MemberDefinition $mouseSig -Name Nat -Namespace Win

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:8080/")
$listener.Start()
Write-Host "Screen control server running on port 8080..."

while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $req = $ctx.Request
    $resp = $ctx.Response
    
    switch ($req.Url.LocalPath) {
        "/screenshot" {
            $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
            $g = [System.Drawing.Graphics]::FromImage($bmp)
            $g.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size)
            $ms = New-Object System.IO.MemoryStream
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
            $resp.ContentType = "image/png"
            $resp.OutputStream.Write($ms.ToArray(), 0, $ms.Length)
            $bmp.Dispose(); $g.Dispose()
        }
        "/click" {
            $body = (New-Object IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
            [System.Windows.Forms.Cursor]::Position = New-Object Drawing.Point($body.x, $body.y)
            [Win.Nat]::mouse_event(0x02, 0, 0, 0, 0)  # down
            Start-Sleep -Milliseconds 30
            [Win.Nat]::mouse_event(0x04, 0, 0, 0, 0)  # up
            $resp.StatusCode = 200
        }
        "/drag" {
            $body = (New-Object IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
            [System.Windows.Forms.Cursor]::Position = New-Object Drawing.Point($body.fx, $body.fy)
            [Win.Nat]::mouse_event(0x02, 0, 0, 0, 0)  # down
            Start-Sleep -Milliseconds 50
            [System.Windows.Forms.Cursor]::Position = New-Object Drawing.Point($body.tx, $body.ty)
            Start-Sleep -Milliseconds 50
            [Win.Nat]::mouse_event(0x04, 0, 0, 0, 0)  # up
            $resp.StatusCode = 200
        }
        "/key" {
            $body = (New-Object IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
            [System.Windows.Forms.SendKeys]::SendWait($body.key)
            $resp.StatusCode = 200
        }
        "/scroll" {
            $body = (New-Object IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
            $clicks = if ($body.clicks) { $body.clicks } else { -3 }
            [System.Windows.Forms.Cursor]::Position = New-Object Drawing.Point($body.x, $body.y)
            for ($i = 0; $i -lt [Math]::Abs($clicks); $i++) {
                [System.Windows.Forms.SendKeys]::SendWait(("{UP}" , "{DOWN}")[$clicks -gt 0])
                Start-Sleep -Milliseconds 20
            }
            $resp.StatusCode = 200
        }
        "/rightclick" {
            $body = (New-Object IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
            [System.Windows.Forms.Cursor]::Position = New-Object Drawing.Point($body.x, $body.y)
            [Win.Nat]::mouse_event(0x08, 0, 0, 0, 0)  # right down
            Start-Sleep -Milliseconds 30
            [Win.Nat]::mouse_event(0x10, 0, 0, 0, 0)  # right up
            $resp.StatusCode = 200
        }
    }
    $resp.Close()
}
```

Save as `screen-control-server.ps1` and run as Administrator:
```powershell
powershell -ExecutionPolicy Bypass -File screen-control-server.ps1
```

> **Reference file available:** The full polished script (with smooth drag, key mapping, CORS support, and status page) is at `references/screen-control-server.ps1` in this skill's directory. Copy it to the desktop for the most complete version.

### Windows FW rule (one-time)
```powershell
New-NetFirewallRule -DisplayName "Screen Control Server" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
```

## From Hermes VM: Vision Pipeline

### Free vision models on OpenRouter

Add `:free` suffix to any qualifying model. Proven options:

| Model ID | Quality | Speed |
|----------|---------|-------|
| `google/gemma-3-27b-it:free` | Good | Fast |
| `meta-llama/llama-3.2-11b-vision-instruct:free` | Good | Fastest |
| `qwen/qwen2.5-vl-32b-instruct:free` | Better | Medium |
| `qwen/qwen2.5-vl-72b-instruct:free` | Best | Slower |
| `google/gemma-3-4b-it:free` | Basic | Fastest |

### Screenshot fetch + vision analysis

```bash
# Grab a screenshot from the Windows desktop over Tailscale
curl -s -o /tmp/screen.png http://<DESKTOP_TAILSCALE_IP>:8080/screenshot

# Feed to vision_analyze — it uses the configured free model
```

Then in the agent conversation:
- Call `vision_analyze(image_url="/tmp/screen.png", question="What do you see?")`
- Decide on actions
- Send commands back to the Windows server

### Sending commands

```bash
# Click at coordinates
curl -s -X POST http://<DESKTOP_TAILSCALE_IP>:8080/click \
  -H "Content-Type: application/json" \
  -d '{"x": 960, "y": 540}'

# Drag (for drawing roads, zoning, etc.)
curl -s -X POST http://<DESKTOP_TAILSCALE_IP>:8080/drag \
  -H "Content-Type: application/json" \
  -d '{"fx": 400, "fy": 300, "tx": 800, "ty": 500}'

# Press a key (e.g. W for camera pan)
curl -s -X POST http://<DESKTOP_TAILSCALE_IP>:8080/key \
  -H "Content-Type: application/json" \
  -d '{"key": "w"}'

# Right click (camera rotate in Cities)
curl -s -X POST http://<DESKTOP_TAILSCALE_IP>:8080/rightclick \
  -H "Content-Type: application/json" \
  -d '{"x": 960, "y": 540}'

# Scroll
curl -s -X POST http://<DESKTOP_TAILSCALE_IP>:8080/scroll \
  -H "Content-Type: application/json" \
  -d '{"x": 960, "y": 540, "clicks": -3}'
```

## Game-Specific Notes

### Cities: Skylines

| Action | Command | Notes |
|--------|---------|-------|
| Place building | `/click` x,y | Need correct resolution mapping |
| Draw road | `/drag` fx,fy → tx,ty | Road tool must be selected first |
| Pan camera | `/key` w/a/s/d or right-drag | Right-drag through `/rightclick` + move |
| Zoom | `/scroll` | Usually -3 to zoom in |
| Rotate view | `/rightclick` + `/drag` | Right-click hold + drag |

**Coordinate calibration needed:** City Skylines' in-game coordinates vs screen resolution. First test: capture screenshot, note resolution, place click at known UI element (main menu button) to verify alignment.

## Safety

- **Only click what's visible** — analyze the screenshot first
- **Window focus:** The game/desktop must be the active window; mouse moves are physical OS-level
- **Don't interact with personal UI** (logins, passwords, banking) — same rules as browser_click
- **Start with a calibration test** before live gaming

## PowerShell Pitfalls (learned Aug 2, 2026 — real session)

1. **Execution policy blocks the script** (`PSSecurityException: running scripts is disabled`). Bypass per-session:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\screen-control-server.ps1
   ```
   `powershell -ExecutionPolicy Bypass -File` also works. NOTE: `Start-Process -WindowStyle Hidden` over SSH does NOT work — the listener needs the interactive desktop session; Tyler must launch from his desktop.
2. **HTML in a normal double-quoted string breaks PowerShell parsing** — `<li>` becomes the reserved `<` operator (`Unexpected token 'Get'` / `The '<' operator is reserved for future use`). Use a here-string `@" ... "@` for any HTML status page.
3. **`$_` inside a double-quoted error string** throws `The string is missing the terminator`. Use `$($_.Exception.Message)`.
4. **Em-dash / emoji mojibake** (`â€”`) in served HTML — use plain `-` or `&#x...;` entities.
5. **Remote deploy path** (verified working): key `~/.ssh/windows_desktop`, user `Tyler` (capital T, no password), tunnel port 1237 → desktop SSH; `scp -P 1237 -i ~/.ssh/windows_desktop <script> Tyler@127.0.0.1:'C:/Users/Tyler/Desktop/...'`. Tyler opens the tunnel: `ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1237:127.0.0.1:22 lumi@<VM_TAILSCALE_IP>`.

## Related

- **`integration/handy-control`** — same Hermes → remote-device control pattern, different endpoint
- **`devops/windows-ssh-tunnel-setup`** — alternative connectivity if Tailscale isn't used
# screen-control-server.ps1 — Full-featured Windows remote control server for Hermes VM
# Run as Administrator. Built for Cities: Skylines co-op gaming.
# 
# Endpoints:
#   GET /screenshot  — Returns PNG of primary monitor
#   GET /info        — Screen dimensions + Tailscale IP
#   POST /click      — {"x": 960, "y": 540, "button": "left|right"}
#   POST /drag       — {"from_x": 100, "from_y": 200, "to_x": 500, "to_y": 400}
#   POST /scroll     — {"clicks": -3} (neg=down, pos=up)
#   POST /key        — {"key": "W"}  (WASD, Space, Enter, Esc, etc.)
#   POST /type       — {"text": "hello world"}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$user32 = @'
using System;
using System.Runtime.InteropServices;
public class WinInput {
    [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern short VkKeyScan(char ch);
}
'@
Add-Type -TypeDefinition $user32

$MOUSEEVENTF_LEFTDOWN = 0x0002
$MOUSEEVENTF_LEFTUP = 0x0004
$MOUSEEVENTF_RIGHTDOWN = 0x0008
$MOUSEEVENTF_RIGHTUP = 0x0010
$MOUSEEVENTF_WHEEL = 0x0800

$PORT = 8080
Write-Host "=== Vesper Screen Control Server ===" -ForegroundColor Cyan
Write-Host "Starting on port $PORT..." -ForegroundColor Cyan
Write-Host "Your Tailscale IP(s):" -ForegroundColor Yellow
ipconfig | Select-String "100\." | ForEach-Object { Write-Host "  $($_.ToString().Trim())" -ForegroundColor Yellow }
Write-Host "Vesper connects via: http://<tailscale-ip>:$PORT" -ForegroundColor Green

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:$PORT/")
$listener.Start()

while ($listener.IsListening) {
    $context = $listener.GetContext()
    $req = $context.Request
    $resp = $context.Response
    $resp.Headers.Add("Access-Control-Allow-Origin", "*")
    $resp.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    if ($req.HttpMethod -eq "OPTIONS") { $resp.StatusCode = 204; $resp.Close(); continue }

    $path = $req.Url.LocalPath.ToLower()
    Write-Host "[$(Get-Date -Format HH:mm:ss)] $($req.HttpMethod) $path" -ForegroundColor Gray

    try {
        switch ($path) {
            "/screenshot" {
                $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size)
                $ms = New-Object System.IO.MemoryStream
                $bitmap.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
                $resp.ContentType = "image/png"
                $resp.StatusCode = 200
                $resp.OutputStream.Write($ms.ToArray(), 0, $ms.Length)
                $bitmap.Dispose(); $graphics.Dispose(); $ms.Dispose()
                Write-Host "  -> Sent screenshot ($($bounds.Width)x$($bounds.Height))" -ForegroundColor Green
            }
            "/info" {
                $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $tsIP = ipconfig | Select-String "100\." | ForEach-Object { $_ -replace '.*?(\d+\.\d+\.\d+\.\d+).*', '$1' } | Select-Object -First 1
                $json = @{screen_width=$bounds.Width; screen_height=$bounds.Height; tailscale_ip=$tsIP} | ConvertTo-Json
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
                $resp.ContentType = "application/json"
                $resp.StatusCode = 200
                $resp.OutputStream.Write($buffer, 0, $buffer.Length)
            }
            "/click" {
                $body = (New-Object System.IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
                $x = [int]$body.x; $y = [int]$body.y
                $button = if ($body.button) { $body.button } else { "left" }
                [WinInput]::SetCursorPos($x, $y)
                Start-Sleep -Milliseconds 30
                if ($button -eq "left") {
                    [WinInput]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    Start-Sleep -Milliseconds 50
                    [WinInput]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                } elseif ($button -eq "right") {
                    [WinInput]::mouse_event($MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    Start-Sleep -Milliseconds 50
                    [WinInput]::mouse_event($MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                }
                $resp.StatusCode = 200
                Write-Host "  -> Click at ($x, $y) [$button]" -ForegroundColor Green
            }
            "/drag" {
                $body = (New-Object System.IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
                $fx = [int]$body.from_x; $fy = [int]$body.from_y
                $tx = [int]$body.to_x; $ty = [int]$body.to_y
                $steps = 10  # smooth drag interpolation
                [WinInput]::SetCursorPos($fx, $fy)
                Start-Sleep -Milliseconds 30
                [WinInput]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                for ($i = 1; $i -le $steps; $i++) {
                    $ix = $fx + [int](($tx - $fx) * $i / $steps)
                    $iy = $fy + [int](($ty - $fy) * $i / $steps)
                    [WinInput]::SetCursorPos($ix, $iy)
                    Start-Sleep -Milliseconds 20
                }
                Start-Sleep -Milliseconds 30
                [WinInput]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                $resp.StatusCode = 200
                Write-Host "  -> Drag from ($fx,$fy) to ($tx,$ty)" -ForegroundColor Green
            }
            "/scroll" {
                $body = (New-Object System.IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
                $clicks = [int]$body.clicks
                [WinInput]::mouse_event($MOUSEEVENTF_WHEEL, 0, 0, [uint]($clicks * 120), 0)
                $resp.StatusCode = 200
                Write-Host "  -> Scroll $clicks clicks" -ForegroundColor Green
            }
            "/key" {
                $body = (New-Object System.IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
                $keyStr = $body.key.ToUpper()
                $vKeyMap = @{ W=0x57; A=0x41; S=0x53; D=0x44; Q=0x51; E=0x45
                    R=0x52; F=0x46; SPACE=0x20; ENTER=0x0D; ESC=0x1B
                    TAB=0x09; SHIFT=0xA0; CTRL=0x11; UP=0x26; DOWN=0x28
                    LEFT=0x25; RIGHT=0x27 }
                if ($vKeyMap.ContainsKey($keyStr)) { $vk = $vKeyMap[$keyStr] }
                elseif ($keyStr.Length -eq 1) { $vk = [WinInput]::VkKeyScan($keyStr[0]) -band 0xFF }
                else { $vk = $null }
                if ($vk) {
                    [WinInput]::keybd_event($vk, 0, 0, 0)
                    Start-Sleep -Milliseconds 50
                    [WinInput]::keybd_event($vk, 0, 2, 0)
                    $resp.StatusCode = 200
                    Write-Host "  -> Key: $keyStr (0x$('{0:X2}' -f $vk))" -ForegroundColor Green
                } else { $resp.StatusCode = 400 }
            }
            "/type" {
                $body = (New-Object System.IO.StreamReader $req.InputStream).ReadToEnd() | ConvertFrom-Json
                [System.Windows.Forms.SendKeys]::SendWait($body.text)
                $resp.StatusCode = 200
                Write-Host "  -> Type: $($body.text)" -ForegroundColor Green
            }
            default {
                $html = "<html><head><title>Vesper Screen Control</title></head><body>
                <h1>🖤 Vesper Screen Control Server</h1><p>Status: <span style='color:green'>Running</span></p>
                <p>Endpoints:</p><ul>
                <li><b>GET /screenshot</b> — Screenshot (PNG)</li>
                <li><b>GET /info</b> — Screen info</li>
                <li><b>POST /click</b> — Click at (x,y)</li>
                <li><b>POST /drag</b> — Drag from→to</li>
                <li><b>POST /scroll</b> — Scroll {clicks}</li>
                <li><b>POST /key</b> — Key press</li>
                <li><b>POST /type</b> — Type text</li>
                </ul></body></html>"
                $buffer = [System.Text.Encoding]::UTF8.GetBytes($html)
                $resp.ContentType = "text/html"
                $resp.StatusCode = 200
                $resp.OutputStream.Write($buffer, 0, $buffer.Length)
            }
        }
    } catch {
        Write-Host "  -> ERROR: $_" -ForegroundColor Red
        $resp.StatusCode = 500
    }
    $resp.Close()
}
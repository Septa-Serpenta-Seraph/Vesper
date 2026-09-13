# PowerShell Commands for Windows Maintenance

Complete command reference for debloating, service disabling, and process management.

## RAM Analysis

```powershell
# Top 20 by RAM
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 20 Name, @{N='RAM(MB)';E={[math]::Round($_.WorkingSet/1MB)}}

# Top 20 by CPU
Get-Process | Sort-Object CPU -Descending | Select-Object -First 20 Name, @{N='CPU(s)';E={[math]::Round($_.CPU,1)}}
```

## Kill Bloatware Processes

```powershell
# Xbox Game Bar & related
Get-Process -Name "GameBar","GameBarFTServer","GameBarPresenceWriter","GamingServices" -ErrorAction SilentlyContinue | Stop-Process -Force

# Cortana
Get-Process -Name "Cortana" -ErrorAction SilentlyContinue | Stop-Process -Force

# Edge background processes
Get-Process -Name "msedge","msedgewebview2","MicrosoftEdgeUpdate" -ErrorAction SilentlyContinue | Stop-Process -Force

# OneDrive
Get-Process -Name "OneDrive" -ErrorAction SilentlyContinue | Stop-Process -Force

# Teams
Get-Process -Name "Teams","msteams" -ErrorAction SilentlyContinue | Stop-Process -Force

# NVIDIA Overlay
Get-Process -Name "NVIDIA Overlay","NVIDIA Share" -ErrorAction SilentlyContinue | Stop-Process -Force

# Steam web helpers
Get-Process -Name "steamwebhelper" -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Set Services to Manual

```powershell
$services = @(
    "WMPNetworkSvc",              # Windows Media Player Network Sharing
    "SysMain",                    # Superfetch — disk thrashing on SSDs
    "DiagTrack",                  # Connected User Experiences and Telemetry
    "dmwappushservice",           # Device Management WAP Push
    "MapsBroker",                 # Downloaded Maps Manager
    "RetailDemo",                 # Retail Demo Service
    "RemoteRegistry",             # Remote Registry (security risk)
    "WerSvc",                     # Windows Error Reporting
    "Fax",                        # Nobody uses fax
    "fhsvc",                      # File History
    "WbioSrvc",                   # Windows Biometric (skip if Windows Hello)
    "PhoneSvc",                   # Phone Service (skip if phone linking)
    "TabletInputService",         # Touch Keyboard and Handwriting
    "PrintSpooler",               # ONLY if no printer
    "XblAuthManager",             # Xbox Live Auth
    "XblGameSave",                # Xbox Live Game Save
    "XboxGipSvc",                 # Xbox Accessory Management
    "XboxNetApiSvc",              # Xbox Live Networking
    "GamingServices",             # Xbox Gaming Services
    "WSearch"                     # Windows Search indexer — big RAM/disk user
)

foreach ($svc in $services) {
    if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Manual -ErrorAction SilentlyContinue
        Write-Host "Disabled: $svc" -ForegroundColor Green
    }
}
```

## NVIDIA Services

```powershell
$nvServices = @(
    "NVDisplay.ContainerLocalSystem",
    "NvContainerNetworkService",
    "NvContainerUserMsgService"
)

foreach ($svc in $nvServices) {
    if (Get-Service -Name $svc -ErrorAction SilentlyContinue) {
        Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
        Set-Service -Name $svc -StartupType Manual -ErrorAction SilentlyContinue
        Write-Host "Disabled: $svc" -ForegroundColor Green
    }
}

# Remove NVIDIA from startup
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "NvBackend" -ErrorAction SilentlyContinue
```

## Discord — Disable Startup + Hardware Acceleration

```powershell
# Kill Discord
Get-Process -Name "Discord" -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove from startup
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "Discord" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "Update" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -Name "Discord" -ErrorAction SilentlyContinue

# Disable hardware acceleration via settings.json
$discordSettings = "$env:APPDATA\discord\settings.json"
if (Test-Path $discordSettings) {
    $settings = Get-Content $discordSettings | ConvertFrom-Json
    $settings | Add-Member -NotePropertyName "hardware_acceleration" -NotePropertyValue $false -Force
    $settings | ConvertTo-Json -Depth 10 | Set-Content $discordSettings
    Write-Host "Discord hardware acceleration disabled" -ForegroundColor Green
}

# Disable scheduled task
Get-ScheduledTask -TaskName "*Discord*" -ErrorAction SilentlyContinue | Disable-ScheduledTask -ErrorAction SilentlyContinue
```

## Steam — Kill Web Helpers + Disable Overlay

```powershell
Get-Process -Name "steamwebhelper" -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "Steam" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -Name "Steam" -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKCU:\SOFTWARE\Valve\Steam\ActiveProcess" -Name "SteamOverlay" -Value 0 -ErrorAction SilentlyContinue
```

## Edge — Disable Background + Startup

```powershell
Get-Process -Name "msedge","msedgewebview2","MicrosoftEdgeUpdate" -ErrorAction SilentlyContinue | Stop-Process -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Edge" -Name "BackgroundModeEnabled" -Value 0 -ErrorAction SilentlyContinue
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Edge" -Name "StartupBoostEnabled" -Value 0 -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "MicrosoftEdgeUpdate" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -Name "MicrosoftEdgeAutoLaunch" -ErrorAction SilentlyContinue
Get-ScheduledTask -TaskName "*Edge*" -ErrorAction SilentlyContinue | Disable-ScheduledTask -ErrorAction SilentlyContinue
```

## Game Bar / Game DVR — Full Nuke

```powershell
Get-Process -Name "GameBar","GameBarFTServer","GameBarPresenceWriter" -ErrorAction SilentlyContinue | Stop-Process -Force
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f
reg add "HKLM:\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f
Get-AppxPackage -Name *GameBar* -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue
Get-AppxPackage -Name *GamingApp* -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue
```

## UWP Bloatware Removal

```powershell
$apps = @(
    "*BingNews*","*BingWeather*","*Microsoft3DViewer*","*ZuneMusic*",
    "*ZuneVideo*","*WindowsMaps*","*MicrosoftSolitaireCollection*",
    "*Office.OneNote*","*SkypeApp*","*GetHelp*","*FeedbackHub*",
    "*MicrosoftPeople*","*WindowsAlarms*","*WindowsCamera*"
)
foreach ($app in $apps) {
    Get-AppxPackage -Name $app -AllUsers | Remove-AppxPackage -ErrorAction SilentlyContinue
}
```

## Startup Items Management

```powershell
# List all startup items
Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location

# Disable specific startup item
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "AppNameHere" -ErrorAction SilentlyContinue
```

## Ghost Driver Removal (pnputil)

```powershell
# List all third-party drivers
pnputil /enum-drivers

# Delete a specific driver (find oemXX.inf from the list above)
pnputil /delete-driver oemXX.inf /uninstall /force
```

## Windows Defender Exclusions (for game directories)

Add game folders to Defender exclusions to stop real-time scanning of game files:
- Windows Security → Virus & threat protection → Manage settings → Exclusions → Add folder
- Add Steam library folders, game install directories

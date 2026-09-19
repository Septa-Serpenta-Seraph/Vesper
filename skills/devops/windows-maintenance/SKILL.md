---
name: windows-maintenance
description: "Windows PC maintenance: debloating, driver removal, service optimization, and performance troubleshooting. PowerShell commands for disabling bloatware, killing background processes, and freeing RAM."
---

# Windows Maintenance

Debloat, optimize, and troubleshoot Windows 10/11 PCs. Covers driver removal (ghost drivers blocking upgrades), service disabling, bloatware uninstall, RAM analysis, and startup management.

## When to Use

- User is reinstalling/upgrading Windows and hitting driver conflicts
- User wants to debloat a fresh Windows install
- User's PC is lagging and needs performance diagnosis
- User wants to disable telemetry, Game Bar, Cortana, etc.

## Key Workflows

### 1. Ghost Driver Removal (blocking Windows upgrades)

Use `pnputil` to find and remove staged drivers that Windows setup trips over:

```powershell
# List all third-party drivers
pnputil /enum-drivers

# Find the oemXX.inf for the problematic driver, then:
pnputil /delete-driver oemXX.inf /uninstall /force
```

Also check Device Manager (Show hidden devices) and delete driver files from `C:\Windows\System32\drivers\`.

For stubborn drivers, use [DriverStore Explorer (RAPR)](https://github.com/lostindark/DriverStoreExplorer/releases) with Force Deletion.

### 2. RAM Analysis

```powershell
# Top 20 processes by RAM
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 20 Name, @{N='RAM(MB)';E={[math]::Round($_.WorkingSet/1MB)}}
```

### 3. Service Disabling (set to Manual)

See `references/powershell-commands.md` for the full service list and commands.

### 4. Bloatware & Startup Removal

See `references/powershell-commands.md` for UWP app removal, startup registry cleanup, and per-app disable scripts (Discord, Steam, Edge, NVIDIA, Game Bar).

### 5. Debloat Tools

- **Chris Titus Tech utility**: `iwr -useb https://christitus.com/win | iex` — GUI tweaker for essential/advanced tweaks, temp cleanup
- **O&O ShutUp10++**: https://www.oo-software.com/en/shutup10 — granular privacy/telemetry toggles, portable, creates restore point. Run AFTER Chris Titus since CT may reset some settings.

## GPU Troubleshooting — Code 43 / Black Screen (verified 2026-08-16)

Symptom: game runs but black screen while audio plays; GPU missing from Task Manager; Device Manager shows "Windows has stopped this device because it has reported problems. (Code 43)".

**The ladder — cheapest to most invasive (Code 43 on Tyler's RTX 5070 Ti was fixed at step 3):**

1. **Reboot.** A large chunk of Code 43s are transient driver-stack faults. Test before anything else.
2. **Reseat the power cable.** 50-series uses the 12VHPWR/12V-2x6 connector — famously finicky. Unplug from the card, push until it clicks, same at the PSU end. **Visually inspect both connector and port for scorching/discoloration/melted plastic** — the known 50-series connector issue. Cheap insurance.
3. **Full PSU drain** (this is the one that fixed it): unplug the PC from the wall, hold the power button ~10s to discharge, wait a minute, power back on. This clears the GPU's *internal* stuck power state and forces the PCIe link to renegotiate from zero. Driver state, not hardware, recovers from this.
4. **Clean driver reinstall (DDU):** boot to safe mode → run [DDU](https://www.wagnardsoft.com/display-driver-uninstaller-DDU-) → reboot → install latest NVIDIA driver fresh. The NVIDIA App "clean install" checkbox helps but DDU is the gold standard for Code 43.
5. **Diagnose before assuming hardware death:** Event Viewer → Windows Logs → System → look for `nvlddmkm` errors around the fault time. Driver-crash events = software; power-related events = connector/PSU. PC was fine all day then 43 suddenly = stuck state, not a dead card — do NOT jump to RMA.

### RECURRING Code 43 (second episode 8/16-17 — the real lesson)

A one-off 43 fixed by a drain is transient. **A 43 that RETURNS and always clears on a full PSU drain is a power-state init fault, not a dead card** — the card parks in a deep state and fails to wake. Eliminate in this order (all were already off/ruled out on Tyler's 5070 Ti before the driver became the prime suspect):

1. **Fast Startup / hybrid shutdown** — the #1 cause of "fine all day, dead at next boot, drain fixes it." The GUI checkbox is HIDDEN when hibernation is off. Check properly:
   ```
   powercfg /a                                # is Hibernation even available?
   reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" /v HiberbootEnabled
   ```
   `1` = Fast Startup ON → `reg add ... /v HiberbootEnabled /t REG_DWORD /d 0 /f`. `0`/missing = already off.
2. **PCIe link-state power management (ASPM):**
   ```
   powercfg /setacvalueindex scheme_current sub_pciexpress aspm 0
   powercfg /setactive scheme_current
   ```
   (or Power Options → PCI Express → Link State Power Management → Off)
3. **D3 device state (monitor-sleep trigger)** — Display Event 4125s clustering after sleep/resume cycles are the tell. NVIDIA desktop cards often DON'T expose the Device Manager Power Management tab (no "Change settings" button without elevation, sometimes not at all) — the equivalent is NVIDIA Control Panel → Manage 3D Settings → Power management mode → **Prefer Maximum Performance**, plus power plan → **Turn off display → Never** (monitor never sleeps → card never parks in D3).
4. **Clean driver reinstall** — DDU in safe mode, or NVIDIA App "clean install" as the softer test. DLSS DLLs live in game folders — DDU doesn't touch them; only shader caches rebuild (one-time stutter per game on first launch).
   **Mid-install black screen is NORMAL** (verified 8/19): during a clean
   install the display driver unloads and the screen can stay black for
   minutes while the installer keeps running — do NOT power-cycle (the one
   move that bricks a half-installed driver). Wait it out; Win+Ctrl+Shift+B
   forces the display to re-init; a reboot to finish is normal.
   **Resolution 8/19:** on Tyler's 5070 Ti the recurring 43 was cured by the
   clean driver install + Prefer Max Performance + display/sleep Never —
   reboot cycles stayed clean afterward, confirming the driver init path was
   the culprit all along. If it recurs: vBIOS check, then BIOS ErP.
5. **vBIOS update check** — early 50-series cards shipped power-state/PMIC firmware bugs fixed by vBIOS flashes.
6. **BIOS ErP / Deep S5** — cuts ALL standby power at shutdown so every shutdown is a full drain. If a drain always fixes it, make every shutdown a drain. (Kills wake-on-LAN/USB-at-off.)

**Event-log forensics (the read that exonerated the card):** zero `nvlddmkm` events + zero WHEA hardware errors across the whole log = the driver never crashed and the PCIe link never faulted → NOT hardware, NOT a driver that crashes under load → power-state init failure. `Kernel-Power` Event 41 with `BugcheckCode=0` = hard power removal (often the user's own drains — ask before assuming a crash). `Display` Event 4125 = screen-blip/display-link event (correlates with monitor sleep). `LastShutdownGood=False` on a `Kernel-Boot` record = previous shutdown was dirty. For parsing a `.evtx` export on Linux, see `references/evtx-parsing-linux.md`.

### Black screen but audio plays (display-output fault, not save/game fault)

- Game loaded fine if you can hear it — the issue is rendering output, not the save. Alt+Enter toggles fullscreen↔windowed (classic fix). Then Alt+Tab out/in.
- **Win+Ctrl+Shift+B** force-resets the graphics driver stack instantly (screen flickers once) — fixes "driver hung, output stuck" ~80% of the time.
- Win+P → "PC screen only" — rules out display handshake confusion after hardware fiddling.
- If GPU vanished from Task Manager: Performance tab → right-click graph area → ensure **GPU is ticked** under View (sometimes just hidden).

## Windows Firewall (MpsSvc) Diagnostics

### Symptom: Service stuck in STOP_PENDING

When `sc query mpssvc` shows:
```
STATE: 3 STOP_PENDING (NOT_STOPPABLE, NOT_PAUSABLE, IGNORES_SHUTDOWN)
WIN32_EXIT_CODE: 1066 (0x42a)
SERVICE_EXIT_CODE: 87 (0x57) — ERROR_INVALID_PARAMETER
```

The firewall service loaded a corrupted registry value and can't complete shutdown. Attempting `sc stop` or `taskkill /f` on mpssvc **causes a BSOD** because the Windows Filtering Platform kernel driver panics.

### Error code quick-reference table

| Error | Code | Meaning |
|---|---|---|
| `0x800706d9` (UI) / `1753` (netsh) | `EPT_S_NOT_REGISTERED` | Endpoint mapper can't find the WFP provider — the Windows Filtering Platform subsystem can't register its RPC endpoints |
| `87` (SERVICE_EXIT_CODE) | `ERROR_INVALID_PARAMETER` | Service received a corrupted configuration value during startup — causes STOP_PENDING |
| `0x8007045b` / `1115` | `ERROR_NO_SYSTEM_RESOURCES` | Service started but can't allocate WFP resources (0x45b) — `netsh advfirewall` returns this |
| `1056` | — | `sc start` returns this when the service is already running (including STOP_PENDING) |
| `1058` | — | Service cannot be started — SCM thinks the service is disabled (even when registry shows Start=2) |
| `1066` (WIN32_EXIT_CODE) | — | Service-specific internal exit — usually accompanied by SERVICE_EXIT_CODE 87 |

### Root cause possibilities (in order of likelihood)

1. **Corrupted profile subkeys** — `StandardProfile`, `DomainProfile`, or `PublicProfile` under `HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\`
2. **Corrupted firewall rules** — `FirewallRules` subkey (less common, user already tried wiping these)
3. **Service security descriptor damaged** — causes "Access denied" on `sc config` even as admin
4. **WMI repository corruption** — verify with `winmgmt /verifyrepository`
5. **Corrupted RestrictedServices hardening rule** — A malformed service-hardening rule in `HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\RestrictedServices\\Static\\System` (TrustedInstaller-protected, can't be modified from normal boot). Look for entries with `Svc==` (double equals) or mislabeled service names.
Hyper-V VmSwitch WFP interaction — Docker v28+ installs WFP callout drivers for container port forwarding. If Docker's provider registration is buggy, it can corrupt the entire WFP subsystem. The "worked for a day" pattern strongly suggests a post-boot trigger re-corrupting the WFP state.

Check for Hyper-V VmSwitch events that may indicate WFP provider registration issues:
```cmd
wevtutil qe System /c:5 /q:"*[System[Provider[@Name='Microsoft-Windows-Hyper-V-VmSwitch'] and (Level=1 or Level=2 or Level=3)]]" /f:text /rd:true
```
7. **Hyper-V virtual switch WFP interaction** — Hyper-V installs virtual network switches that register their own WFP providers. Conflicts between Hyper-V's providers and the firewall's providers can cause EPT_S_NOT_REGISTERED.

### Safe diagnostic flow

1. Check service state: `sc query mpssvc`
2. Check if service can start (reveals the STOP_PENDING trap): `sc start mpssvc` → returns **error 1056** "An instance of the service is already running" when stuck in STOP_PENDING
3. Find specific error: `wevtutil qe "Microsoft-Windows-Windows Firewall with Advanced Security/Firewall" /c:5 /rd:true /f:text` — if the service is broken, **no recent events appear** (the log goes silent after the last crash)
4. Check for UI error: opening Windows Defender Firewall settings → click "Reset to recommended settings" → returns **error 0x800706d9** "There are no more endpoints available from the endpoint mapper"
5. Rule out Group Policy overlay: `dir "%SystemRoot%\System32\GroupPolicy" /s` — returns "File Not Found" when no local policies exist
6. Rule out WMI corruption: `winmgmt /verifyrepository` — should return "WMI repository is consistent"

### Full diagnostic flow (detailed walkthrough)

When MpsSvc is stuck in STOP_PENDING, the following flow reveals which component is broken:

#### 1. State confirmation

```cmd
sc query mpssvc
```
Look for `STATE: 3 STOP_PENDING` and `SERVICE_EXIT_CODE: 87 (0x57) — ERROR_INVALID_PARAMETER`.

#### 2. Service trap check

```cmd
sc start mpssvc
```
Returns **error 1056** "An instance of the service is already running" — confirming the service is alive at the SCM level but hung.

#### 3. Event log confirmation

```cmd
wevtutil qe "Microsoft-Windows-Windows Firewall with Advanced Security/Firewall" /c:5 /rd:true /f:text
```
If the service is broken long-term, **no recent events appear** — the log goes silent from the last crash date forward.

```cmd
wevtutil qe System /c:20 /q:"*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 604800000]]]" /rd:true /f:text
```
Shows SCM events (ID 7024): "The Windows Defender Firewall service terminated with the following service-specific error: The parameter is incorrect."

#### 4. UI error confirmation

Open Windows Defender Firewall settings → click "Reset to recommended settings" → returns **error 0x800706d9** "There are no more endpoints available from the endpoint mapper" (`EPT_S_NOT_REGISTERED`).

#### 5. WFP state check

```cmd
netsh wfp show state
```
If this returns `EPT_S_NOT_REGISTERED (1753)` instead of XML output, the Windows Filtering Platform itself can't enumerate its providers — a deeper sign of corruption.

#### 5b. WFP driver discovery

List kernel-mode WFP-related drivers to identify non-standard ones (Hyper-V HNS, Docker, VPN clients):

```cmd
reg query HKLM\SYSTEM\CurrentControlSet\Services /s 2> nul | findstr /i "wfp"
```

Standard expected drivers:
- **hnswfpdriver** — Hyper-V Host Network Service WFP driver (STOPPED = normal if Hyper-V is disabled)
- **MsSecWfp** — Windows Defender Security WFP driver (STOPPED = normal on some builds)
- **WFPLWFS** — WFP LightWeight Filter Service (RUNNING with adapter entries = normal)
- **mpsdrv** — Windows Defender Firewall driver

Any third-party driver (e.g. from Docker, VPN, or gaming software) is a suspect.

#### 5c. Filter driver inventory

Check loaded filesystem filter drivers for non-standard entries:

```cmd
fltmc filters
```

Standard Windows filters: `bindflt`, `WdFilter`, `storqosflt`, `wcifs`, `gameflt`, `CldFlt`, `bfs`, `FileCrypt`, `luafv`, `Wof`, `FileInfo`, `WinSetupMon`. Filters like `UCPD` (USB-C PD), `UnionFS` (possible Docker remnant), and `gameflt` (Xbox Game Bar) are normal.

#### 6. Service dependency check

All must be RUNNING:
```cmd
sc query BFE        & REM Base Filtering Engine
sc query mpsdrv     & REM Windows Defender Firewall Driver
sc query nsi        & REM Network Store Interface Service
sc query SharedAccess  & REM Network Address Translation / ICS
sc query RpcEptMapper  & REM RPC Endpoint Mapper
sc query RpcSs         & REM Remote Procedure Call
sc query wscsvc        & REM Windows Security Center
```

#### 7. Registry structure inventory

Check for missing or corrupted subkeys:
```cmd
reg query HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy
```
Expected: `DomainProfile`, `PublicProfile`, `FirewallRules`, `DynamicKeywords`, `RestrictedServices`. `StandardProfile` is NOT created by default on some Win11 builds (not necessarily a problem).

Check each profile for valid entries:
```cmd
reg query HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile
reg query HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile
```

#### 8. Rule out Group Policy overlay

```cmd
dir "%SystemRoot%\System32\GroupPolicy" /s
```
"File Not Found" means no local policies are interfering.

#### 9. Rule out WMI corruption

```cmd
winmgmt /verifyrepository
```
Should return "WMI repository is consistent."

#### 10. DNS hosts file check (correlated symptom)

```cmd
type C:\Windows\System32\drivers\etc\hosts
```
A DNS Client event (ID 1012: "error reading hosts file") can appear alongside firewall issues. The hosts file itself is usually fine — the error is a transient symptom of deeper WFP troubles.

### Safe fix (avoids BSOD)

Since direct `sc stop` or `taskkill` on mpssvc causes a BSOD (the WFP kernel filter driver panics when the userspace service disappears):

**Via registry disable + reboot (preferred):**

1. **Disable via registry** (safer than `sc config` which may be access-denied if the service's security descriptor is corrupted):
   ```cmd
   reg add "HKLM\SYSTEM\CurrentControlSet\Services\mpssvc" /v Start /t REG_DWORD /d 4 /f
   ```
2. **Reboot** — clean process exit during shutdown (not forced kill)
3. **After reboot, the service is fully stopped** (disabled, no STOP_PENDING). Clean corrupted config:
   ```cmd
   reg delete "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile" /f
   reg delete "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile" /f
   reg delete "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile" /f
   ```
4. **Re-enable and start:**
   ```cmd
   reg add "HKLM\SYSTEM\CurrentControlSet\Services\mpssvc" /v Start /t REG_DWORD /d 2 /f
   sc start mpssvc
   ```

**Via Safe Mode (fallback if registry disable + reboot doesn't work):**

Boot into Safe Mode (where mpssvc doesn't start), then from an admin cmd:
```cmd
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy" /f
```
This nukes the entire policy tree. Reboot normally — Windows rebuilds it from defaults. Safe Mode avoids the BSOD entirely because the service never starts.

### Remote diagnosis via SSH tunnel

When a broken Windows Firewall prevents direct connections to the desktop, you can diagnose remotely through an **SSH reverse tunnel**:

1. User runs from their Windows desktop (which has outbound SSH access):
   ```cmd
   ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1236:127.0.0.1:22 user@remote-vm
   ```
   This forwards the desktop's SSH port (22) to port 1236 on the VM.

2. Connect from the VM through the tunnel:
   ```bash
   ssh -i ~/.ssh/windows_key -p 1236 windows-user@127.0.0.1 cmd /c "sc query mpssvc"
   ```
3. Use `cmd /c "..."` for quoting simplicity (PowerShell's `-Command` with nested quotes gets mangled over the tunnel).
4. The user must approve this approach first — it establishes an interactive remote shell on their machine.

### If the issue survived a Windows reinstall (keeping files)

A reinstall that preserves files and apps keeps the `SOFTWARE` and `SYSTEM` registry hives. If the firewall broke again within a day, something in the persisted hives is re-corrupting it. Options:

- **In-place repair upgrade** with a stock Windows 11 ISO (replaces system files, rebuilds hives) — this is different from a "keep files" reinstall via Settings
- **Safe Mode + nuke FirewallPolicy key** (as described above) — if even this doesn't stick, the corruption is in the `mpssvc` service key's security descriptor or the BFE policy store
- Consider whether a startup app (Corsair iCUE, Focusrite, etc.) is re-applying a broken firewall policy after boot

### Quick-reference registry layout

```
HKLM\SYSTEM\CurrentControlSet\Services\mpssvc
├── DependOnService = mpsdrv\0bfe\0nsi
├── ImagePath = %SystemRoot%\system32\svchost.exe -k LocalServiceNoNetworkFirewall -p
├── ObjectName = NT Authority\LocalService
├── Start = 0x2 (Auto)
└── Parameters
    ├── ServiceDll = %SystemRoot%\system32\mpssvc.dll
    └── PortKeywords\

HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy
├── DomainProfile
│   ├── EnableFirewall = 0x1
│   ├── DisableNotifications = 0x0
│   └── Logging\
├── PublicProfile
│   ├── EnableFirewall = 0x1
│   ├── DisableNotifications = 0x0
│   └── Logging\
├── (StandardProfile — may be absent on Win11)
├── FirewallRules\
└── DynamicKeywords\
```

### Useful wevtutil queries

```cmd
# Last 5 firewall events
wevtutil qe "Microsoft-Windows-Windows Firewall with Advanced Security/Firewall" /c:5 /rd:true /f:text

# Last 20 critical or error events in the System log (past 7 days)
wevtutil qe System /c:20 /q:"*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 604800000]]]" /rd:true /f:text
```

### SSH over tunnel: quoting rules

When running Windows diagnostics through an SSH tunnel:
- Use `cmd /c "command"` — CMD handles simple `|`, `&`, `>` directly
- PowerShell over SSH: the `-Command` argument with nested quotes **will get mangled**. Use cmd.exe for most diagnostics. For PowerShell-only workflows, encode via `-EncodedCommand` or write a `.ps1` file first.

1. **Never disable core Windows processes**: dwm, explorer, MsMpEng, StartMenuExperienceHost, SearchHost, TextInputHost, Memory Compression, Secure System
2. **PrintSpooler** — only disable if user doesn't print
3. **WbioSrvc** — only disable if no Windows Hello (face/fingerprint)
4. **WSearch** — disabling slows Windows Search but reclaims significant RAM/disk
5. **SysMain** (Superfetch) — safe to disable on SSDs, causes disk thrashing otherwise
6. **Pagefile on external USB SSD** — don't do it. USB adds latency, can disconnect (BSOD), Windows won't allow it by default
7. **16GB RAM diagnosis**: If a PC with 16GB lags, check if internal drive is HDD (100-200x slower than SSD) before assuming RAM is the issue. Also check bloatware, startup items, browser tabs.
8. **Discord RAM**: 3+ processes, 1GB+ RAM. Disable Hardware Acceleration (Settings → Advanced) to cut memory significantly.
9. **Steam web helper**: Multiple processes eating 900MB+. Disable Steam Overlay (Settings → In-Game) to reduce spawned processes.
10. **Run PowerShell blocks separately** so errors are traceable. Use `-ErrorAction SilentlyContinue` to skip missing items gracefully.
11. **MsMpEng exclusions for game folders**: Windows Defender (MsMpEng) real-time scanning of large game libraries (Steam, etc.) eats 400MB+ RAM and causes disk thrashing. Add game directories to Defender exclusions (Windows Security → Virus & threat protection → Manage settings → Exclusions → Add folder) to reclaim RAM and reduce I/O. Do NOT disable Defender itself.
12. **Game DVR (GameBar) background recording overhead**: Even when not gaming, Game DVR silently records in the background (AppCaptureEnabled=1 default). Disabling it via the registry keys in references/powershell-commands.md stops the overhead and frees RAM/CPU immediately. This is one of the highest-impact single changes on a gaming PC.
13. **NVIDIA Overlay**: nvspcap64 / NVIDIA Overlay spawns 2+ processes (300MB+). Disable via GeForce Experience/NVIDIA App → Settings → In-Game Overlay → OFF, then kill processes and set NVIDIA container services to Manual.

## Context

Dad (Tyler) maintains multiple Windows PCs — his own (RTX 5070 Super, tiny11/repaired Windows 11) and Mom's (16GB RAM, lag issues). He uses Chris Titus Tech utility and O&O ShutUp10++ for debloating. Voicemeeter driver conflicts have been a specific issue during Windows reinstalls.

**Common RAM hogs observed on Dad's gaming PC (session 2026-07-17):**
- Discord (3 processes): ~1,077 MB — fixed via Hardware Acceleration OFF + startup removal
- steamwebhelper (3 processes): ~958 MB — fixed via Steam Overlay OFF
- NVIDIA Overlay (2 processes): ~307 MB — fixed via GeForce Experience In-Game Overlay OFF
- msedgewebview2 (2 processes): ~230 MB — fixed via Edge BackgroundModeEnabled=0
- MsMpEng (Defender): ~443 MB — mitigated via game folder exclusions

**Recommended debloat order (Dad's workflow):**
1. In-place repair upgrade with stock Windows 11 ISO (fixes tiny11 corruption like MpsSvc START_PENDING)
2. Chris Titus Tech utility (`iwr -useb https://christitus.com/win | iex`)
3. O&O ShutUp10++ (privacy hardening, run AFTER Chris Titus)
4. Apply PowerShell service/process disabling from this skill
5. Add Defender exclusions for game folders

**Voicemeeter driver conflict resolution (verified working):** Uninstalling the Voicemeeter app does NOT remove its virtual audio driver from the DriverStore. Windows setup still reads the staged `.inf` and fails the upgrade. Fix: `pnputil /enum-drivers` → find `oemXX.inf` with "VB-Audio" → `pnputil /delete-driver oemXX.inf /uninstall /force`. Also check Device Manager → Show hidden devices for ghosted Voicemeeter entries.

## Event Log Queries

```cmd
# Service control manager errors (last 5)
wevtutil qe System /c:5 /q:"*[System[(EventID=7031 or EventID=7034)]]" /rd:true /f:text

# All errors/warnings from last 7 days
wevtutil qe System /c:20 /q:"*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 604800000]]]" /rd:true /f:text

# Firewall-specific operational log
wevtutil qe "Microsoft-Windows-Windows Firewall with Advanced Security/Firewall" /c:5 /rd:true /f:text

# Hyper-V VmSwitch errors/warnings (useful w/ Hyper-V enabled)
wevtutil qe System /c:5 /q:"*[System[Provider[@Name='Microsoft-Windows-Hyper-V-VmSwitch'] and (Level=1 or Level=2 or Level=3)]]" /f:text /rd:true

# Configuration-Change-Monitor (tracks registry/file changes)
wevtutil qe System /c:5 /q:"*[System[Provider[@Name='Microsoft-Windows-Configuration-Change-Monitor']]]" /f:text /rd:true
```

## WFP Deeper Diagnostics

When `netsh advfirewall` or `netsh wfp` returns `EPT_S_NOT_REGISTERED` (0x45b / 1115), the WFP subsystem may be corrupted beyond firewall registry repair. Check WFP-related kernel drivers:
```cmd
sc query hnswfpdriver   # Hyper-V Host Networking WFP driver
sc query MsSecWfp       # Windows Defender WFP driver
sc query WFPLWFS        # WFP Lightweight Filter Service
```
Inspect the BFE policy store: `reg query "HKLM\SYSTEM\CurrentControlSet\Services\BFE\Parameters\Policy\Persistent\Provider"`.

## References

- `references/windows-ssh-setup.md` — SSH server setup, tunnel config, user preferences
- `references/powershell-commands.md` — Full service list, bloatware removal commands
- `references/evtx-parsing-linux.md` — Parse Windows `.evtx` event logs on Linux
- `references/evtx-event-forensics.md` — Event-ID meanings, GPU Code 43 forensic case study
- `scripts/evtx-dump.py` — Reusable evtx parser script

### Windows Remote Workflow Tips (Absorbed from `windows-session-workflow`)

Operational patterns from hands-on Windows debugging sessions:

- **Use your SSH access** — run commands directly instead of asking the user
- **Curl.exe for downloads** (not bitsadmin over SSH — mangles quoting)
- **Verified tunnel creds:** user `Tyler` (capital T), key `~/.ssh/windows_desktop`, port 1237
- **Fresh Windows install checklist:** OpenSSH reinstalled, authorized_keys wiped, host key changed (`ssh-keygen -f ~/.ssh/known_hosts -R '[host]:port'`)
- **PowerShell gotchas:** `sc` is `Set-Content` alias, NOT Service Controller (use `sc.exe`)
- **Wake-on-LAN:** WOL works on fully off machines; Tailscale CANNOT deliver magic packets (needs always-on relay on same LAN); Asus router as relay path

Full transcript detail in the archived skill: `~/.hermes/skills/.archive/windows-session-workflow/SKILL.md`

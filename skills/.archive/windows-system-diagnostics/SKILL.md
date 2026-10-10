---
description: 'Remote Windows repair: SSH, firewall, registry, services.'
name: windows-system-diagnostics
---

# Windows System Diagnostics

Trigger: User needs to debug or repair a Windows system remotely from a Linux host — firewall broken, service stuck, registry corruption, SSH access needed.

---

## 1. SSH Tunnel to Windows Desktop

When Windows Firewall blocks inbound connections, establish a **reverse SSH tunnel** from the Windows desktop to the Linux VM:

```cmd
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1236:127.0.0.1:22 user@<VM_IP>
```

- `-R 1236:127.0.0.1:22` forwards the Windows SSH server (port 22) to the VM's port 1236
- `-o ServerAliveInterval=30` keeps the connection alive
- Add `-v` for verbose logging on the Windows side

Then from the Linux VM, connect via localhost:
```bash
ssh -i ~/.ssh/windows_key -p 1236 user@127.0.0.1
```

## 2. Installing OpenSSH Server on Windows

**Via PowerShell (Admin):**
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

**NOTE:** `sc` in PowerShell is aliased to `Set-Content`, not Service Control. Use `sc.exe` or `net start sshd` for service operations from PowerShell.

**PITFALL — Add-WindowsCapability hangs or stalls:** This is a known issue on fresh Windows installs. The capability download from Windows Update can stall indefinitely at various percentages. Alternatives:
- **Settings GUI:** Settings → System → Optional Features → Add a feature → search "OpenSSH Server" → Install (often more reliable)
- **winget (fastest):** `winget install Microsoft.OpenSSH.Preview` — downloads the MSI directly from GitHub (~6 MB) and finishes in seconds
- **DISM:** `dism /online /Add-Capability /CapabilityName:OpenSSH.Server~~~~0.0.1.0` (same backend as Add-WindowsCapability, same stalling risk)

**PITFALL — Host key changed after fresh Windows install:** After reinstalling Windows, the SSH server generates a new host key. Your Linux client will report:
```
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
```
Fix by removing the old host key:
```bash
ssh-keygen -f '~/.ssh/known_hosts' -R '[127.0.0.1]:1236'
```

**Check if installed:**
```cmd
dism /online /get-capabilities | findstr OpenSSH
```

## 3. SSH Key Authentication for Admin Users

Windows OpenSSH has a quirk: **admin users** require keys in a different path than standard users.

**Standard path** (non-admin users): `%USERPROFILE%\.ssh\authorized_keys`
**Admin path** (must be used when user is in Administrators group): `%ProgramData%\ssh\administrators_authorized_keys`

Steps:
1. Generate a key pair on the Linux host:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/windows_desktop -N "" -C "agent@host"
   ```

2. Place the public key in `administrators_authorized_keys` on Windows:
   ```powershell
   "ssh-ed25519 <PUBLIC_KEY> agent@host" | Out-File "C:\ProgramData\ssh\administrators_authorized_keys" -Encoding UTF8 -Force
   ```

3. Lock permissions (required — Windows SSH rejects keys with wrong perms):
   ```powershell
   icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:F" /grant "BUILTIN\Administrators:F"
   ```

4. Restart sshd:
   ```powershell
   Restart-Service sshd
   ```

### Troubleshooting Key Auth
- Check the **sshd_config** for which `AuthorizedKeysFile` is active:
  ```cmd
  type "C:\ProgramData\ssh\sshd_config" | findstr AuthorizedKeysFile
  ```
- On Windows, there are **two** `AuthorizedKeysFile` directives in the default config: one for standard users (`.ssh/authorized_keys`) and one for admins (`__PROGRAMDATA__/ssh/administrators_authorized_keys`).
- Verify the key file content and permissions:
  ```powershell
  type "C:\ProgramData\ssh\administrators_authorized_keys"
  icacls "C:\ProgramData\ssh\administrators_authorized_keys"
  ```

## 4. Running Commands via SSH

**CMD.EXE** (best for simple commands — preserves quoting):
```bash
ssh -i ~/.ssh/windows_key -p 1236 user@127.0.0.1 cmd /c "sc query mpssvc | findstr STATE"
```

**PowerShell** (watch out for quoting issues with pipes and script blocks):
```bash
ssh -i ~/.ssh/windows_key -p 1236 user@127.0.0.1 powershell -Command "sc.exe query mpssvc | Select-String STATE"
```

**BEST PRACTICE:** Use `cmd /c` for simple registry/service checks. Use PowerShell `-EncodedCommand` for complex scripts to avoid quoting issues.

**USER PREFERENCE: Once the SSH tunnel is established, run commands yourself.** Do not ask the user to type commands into their terminal — you have the SSH connection, you can execute them directly. This was a user preference correction. Only ask the user to run something if the SSH tunnel is down or you need interactive feedback (like a password or a reboot confirmation).

## 5. Windows Firewall (mpssvc) Troubleshooting

### Symptoms
- Firewall service stuck in `STOP_PENDING` — not running, can't be killed
- `sc query mpssvc` shows `STATE: 3 STOP_PENDING` with `WIN32_EXIT_CODE: 1066` and `SERVICE_EXIT_CODE: 87 (ERROR_INVALID_PARAMETER)`
- Error in firewall settings UI: `0x800706d9` (EPT_S_NOT_REGISTERED)
- SCM event 7024: "The Windows Defender Firewall service terminated with: The parameter is incorrect."
- `netsh wfp show state` fails with `EPT_S_NOT_REGISTERED`

### Diagnostic Steps

1. **Check service state:**
   ```cmd
   sc query mpssvc
   ```

2. **Check dependencies** (all three must be running):
   ```cmd
   sc query BFE
   sc query mpsdrv
   sc query nsi
   sc query SharedAccess
   ```

3. **Check event logs for the specific error:**
   ```cmd
   wevtutil qe System /c:20 /q:"*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 604800000]]]" /rd:true /f:text
   ```
   Look for Event ID 7024 from Service Control Manager.

4. **Check WFP (Windows Filtering Platform) state:**
   ```cmd
   netsh wfp show state
   ```
   If this fails with `EPT_S_NOT_REGISTERED`, the WFP provider store may be corrupted.

5. **Check firewall policy registry:**
   ```cmd
   reg query HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy /s
   ```

6. **Check service registry integrity:**
   ```cmd
   reg query HKLM\SYSTEM\CurrentControlSet\Services\mpssvc
   reg query HKLM\SYSTEM\CurrentControlSet\Services\mpssvc\Parameters
   ```
   Verify `ServiceDll` points to `%SystemRoot%\system32\mpssvc.dll` and `ImagePath` is correct.

### Clean-Slate Repair Procedure

When standard fixes (SFC, DISM, WMI verify, rule deletion) have failed, use this approach:

1. **Disable the service via registry** (not `sc config` — that may fail with access denied):
   ```cmd
   reg add HKLM\SYSTEM\CurrentControlSet\Services\mpssvc /v Start /t REG_DWORD /d 4 /f
   ```

2. **Reboot** — the service process terminates cleanly as part of shutdown. With Start=4, it won't start on next boot.
   ```cmd
   shutdown /r /t 0
   ```

3. **After reboot, delete the firewall policy registry key** (backup first):
   ```cmd
   reg export HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy C:\Users\<user>\Desktop\fw_backup.reg
   reg delete HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy /va /f
   ```
   NOTE: The `RestrictedServices` subkey is protected by TrustedInstaller and will not delete — this is normal.

4. **Re-create minimal profile keys** (the service needs at least these to start):
   ```cmd
   reg add HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\DomainProfile /v EnableFirewall /t REG_DWORD /d 1 /f
   reg add HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\PublicProfile /v EnableFirewall /t REG_DWORD /d 1 /f
   ```

5. **Re-enable the service:**
   ```cmd
   reg add HKLM\SYSTEM\CurrentControlSet\Services\mpssvc /v Start /t REG_DWORD /d 2 /f
   ```

6. **Start the service:**
   ```cmd
   net start mpssvc
   ```
   If `net start` fails with error 1058 (disabled), verify Start=2 and try a second reboot.

### Pitfalls
- **DO NOT** use `taskkill /f` on mpssvc — the WFP filter driver (`mpsdrv`) will panic and cause a **BSOD**.
- `sc config mpssvc start= auto` may fail with **Access Denied (error 5)** even from admin when the service SD is in a degraded state. Use the registry instead.
- `sc start mpssvc` may fail with error 1058 even when the registry shows Start=2 — the SCM may cache the disabled state. Reboot to clear this.
- The service SD (`sc sdshow mpssvc`) typically shows `BA` (Administrators) with full control. If `sc config` fails despite this, the SD may be cached or another component is blocking.
- After reboot with Start=4, `sc start` and `net start` may both fail with error 1058 even after changing back to Start=2. A second reboot is sometimes required.

### Deeper WFP Diagnostics

When `netsh advfirewall` or `netsh wfp` returns `EPT_S_NOT_REGISTERED` (0x45b / 1115), the WFP subsystem is corrupted beyond firewall registry repair.

**Check WFP-related kernel drivers:**
```cmd
sc query hnswfpdriver   # Hyper-V Host Networking WFP driver
sc query MsSecWfp       # Windows Defender WFP driver
sc query WFPLWFS        # WFP Lightweight Filter Service
```
Exit code 1077 = driver wasn't started last boot (normal for disabled features).

**Inspect the BFE policy store (contains all WFP provider registrations):**
```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Services\BFE\Parameters\Policy\Persistent\Provider"
```
Decoded strings in the binary blobs will name the WFP providers (e.g. `FirewallAPI.dll`, `policystore.dll`, `MpsSvc`).

**Check registered WFP callout drivers in the service list:**
```cmd
reg query HKLM\SYSTEM\CurrentControlSet\Services /s 2> nul | findstr /i "wfp"
```

**Network filter drivers (fltmc):**
```cmd
fltmc filters
```
Look for non-standard drivers like `UCPD`, `UnionFS`, or `gameflt`.

**DNS hosts file check** — a corrupted hosts file can cause DNS client errors that compound firewall issues:
```cmd
type C:\Windows\System32\drivers\etc\hosts
```

### When None of the Above Works

If the firewall survived a clean registry + reboot and an in-place Windows upgrade only fixed it temporarily (1 day), the root cause is likely a **POST-BOOT trigger** that re-corrupts the WFP state. Investigate:

1. **Docker Desktop** — installs WFP callout drivers for container NAT. Check with `docker --version`. Uninstall and reboot to test.
2. **Hyper-V** — Virtual switch WFP providers. Check if `hnswfpdriver` is running or if Hyper-V features are enabled.
3. **Startup programs** — Check `reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` for suspicious entries.
4. **Scheduled tasks** — Look for daily or boot-time tasks that might modify firewall state.
5. **Third-party WFP providers** — VPN clients, security software, and game overlays can install WFP callouts.
  6. **Tailscale** — Virtual network adapter can interact with WFP. Temporarily disable to test.
  7. **Corsair iCUE / gaming software** — Some peripheral software installs network filter drivers. Check `fltmc filters` for non-standard entries like `UCPD` (USB connector policy driver), `gameflt`, or `UnionFS`.

## 8. GPU Code 43 — "Windows has stopped this device because it has reported problems"

**Trigger:** game renders black (audio plays) or GPU missing from Task Manager; Device Manager shows Code 43 on the discrete card.

**Diagnosis:** Code 43 is usually a driver/power fault, NOT a dead card. Audio-playing + black screen = render output issue (game loaded fine, driver stack hung). GPU missing from Task Manager while display still works = driver lost the card.

**Fix ladder (cheapest → most invasive):**
1. **Reboot** — clears transient driver-stack faults (a big chunk of Code 43s).
2. **Full PSU drain** (verified fix 8/16/26, RTX 5070 Ti): unplug wall power, hold power button ~10s to drain caps, wait ~30s, replug, boot. This clears the GPU's internal stuck state and forces PCIe link renegotiation — often the ONLY thing that works when a reseat/reboot doesn't.
3. **Reseat 12VHPWR/12V-2x6 power connector** at BOTH ends (card + PSU) until it clicks. **Visual check for scorching/melted plastic on pins** — 50-series connector has a known history; catch it early.
4. **Reseat the card** in the PCIe slot.
5. **DDU clean driver reinstall** (safe mode → DDU → fresh NVIDIA driver). Kills stubborn Code 43s.
6. **Event Viewer** → Windows Logs → System → look for `nvlddmkm` errors to distinguish driver-crash vs power-related.

**Pattern:** card fine all day then suddenly Code 43 = stuck driver/power state, not hardware.

**RECURRING Code 43 — power-state init issue (verified 8/16/26, RTX 5070 Ti):** If it keeps coming back and a PSU drain fixes it EVERY time, it is NOT the connector (a bad 12VHPWR fails under load and wouldn't cleanly re-fix twice with normal performance after). The card is parking in a deep PCIe power state at sleep/shutdown and failing to wake at the next boot → Code 43. The drain works because it fully resets the card's power-management controller. Evidence chain from Tyler's event log: **zero `nvlddmkm` TDRs, zero WHEA hardware errors**, Display 4125 blips clustered after sleep/resume cycles, Kernel-Power 41 (BugcheckCode=0) + Event 6008 = hard power cuts (the drain ops themselves).

**Recurring-case fixes (in order):**
1. **Disable PCIe link-state power management (ASPM)** — the direct cure:
   ```
   powercfg /setacvalueindex scheme_current sub_pciexpress aspm 0
   powercfg /setactive scheme_current
   ```
2. **Set Sleep to Never on AC power** — a card that demonstrably fails to wake from sleep shouldn't be asked to sleep.
3. **Rule out Fast Startup** (hidden on debloated Windows): `powercfg /a` — if Hibernation isn't listed, Fast Startup can't run (boots are already cold). Registry check: `reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" /v HiberbootEnabled` (1=on, 0=off).
4. **DDU clean driver reinstall** — backup suspect; a driver that saves a bad card state at shutdown causes the same loop.
5. **BIOS: ErP / Deep S5** — makes every shutdown a full drain automatically (kills wake-on-LAN/USB-power-at-off; fine for a desktop).

**Event-log forensics (the definitive diagnostic for recurring 43):** export the System log (`Events.evtx` from Event Viewer) and parse it on the Linux side — see `scripts/evtx-dump.py` (reusable parser) + `references/evtx-event-forensics.md` (event-ID meanings + case study). Key tells: `nvlddmkm` events = driver crashes; `WHEA` = hardware faults; **absence of both** + sleep/resume correlation = power-state init issue; Kernel-Power 41 with `BugcheckCode=0` = hard power cut (no BSOD); Event 6008 = dirty shutdown; Display 4125 = display-link blip (brief black screen).



```cmd
# Query a key and all subkeys
reg query HKLM\SYSTEM\CurrentControlSet\Services\mpssvc /s

# Get a specific value
reg query HKLM\SYSTEM\CurrentControlSet\Services\mpssvc /v Start

# Add/modify a value
reg add HKLM\SYSTEM\CurrentControlSet\Services\mpssvc /v Start /t REG_DWORD /d 2 /f

# Delete a key
reg delete HKLM\SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy /f
```

## 7. Event Log Queries

```cmd
# Service control manager errors (last 5)
wevtutil qe System /c:5 /q:"*[System[(EventID=7031 or EventID=7034)]]" /rd:true /f:text

# All errors/warnings from last 7 days
wevtutil qe System /c:20 /q:"*[System[(Level=1 or Level=2) and TimeCreated[timediff(@SystemTime) <= 604800000]]]" /rd:true /f:text
\`\`\`cmd
# Firewall-specific operational log
wevtutil qe "Microsoft-Windows-Windows Firewall with Advanced Security/Firewall" /c:5 /rd:true /f:text

# Hyper-V VmSwitch errors/warnings (useful w/ Hyper-V enabled)
wevtutil qe System /c:5 /q:"*[System[Provider[@Name='Microsoft-Windows-Hyper-V-VmSwitch'] and (Level=1 or Level=2 or Level=3)]]" /f:text /rd:true

# Configuration-Change-Monitor (tracks registry/file changes)
wevtutil qe System /c:5 /q:"*[System[Provider[@Name='Microsoft-Windows-Configuration-Change-Monitor']]]" /f:text /rd:true
```
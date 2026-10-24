---
name: windows-session-workflow
description: Remote Windows work via SSH. Setup and workflow tips.
---

# Windows Remote Workflow Tips

Operational patterns learned from hands-on Windows debugging sessions.

## Use your SSH access

When you have an active SSH session into a Windows machine, run commands directly instead of asking the user to do it. Every command you ask the user to run is an unnecessary round-trip. Exception: commands that need a GUI, user interaction, or a local peripheral the SSH session can't reach.

## File downloads on Windows via SSH

Windows ships a functional `curl.exe`. Use it for downloading models and files:

```cmd
curl -L -o C:\path\to\output.file https://source.url/file
```

### Hugging Face downloads
- Many models are gated (require authentication) — `curl` will get a tiny stub file instead of the real model
- Check file size after download: if it's <1KB, you got an error page, not the model
- Workarounds:
  - Append `?download=1` to the URL
  - Download to the Linux VM first, then SCP through the tunnel
  - Use CivitAI instead (no auth for most models)

### CivitAI downloads
- Model version IDs are required — not model IDs
- Find the right version: `curl -s "https://civitai.com/api/v1/models?query=<model_name>"`
- Then download: `curl -L -o model.safetensors https://civitai.com/api/download/models/<version_id>`

## Fresh Windows install checklist

After a clean install, expect:
1. OpenSSH Server needs to be reinstalled — use winget first, then DISM, then Add-WindowsCapability (in that order of reliability)
2. Authorized key files are wiped — re-add and re-icacls
3. SSH host key changed — clean known_hosts: `ssh-keygen -f ~/.ssh/known_hosts -R '[host]:port'`
4. Windows Defender will peg CPU for 30+ minutes doing first-time scans — let it cook

## PowerShell gotchas

- `sc` is an alias for `Set-Content` in PowerShell, NOT the Service Controller. Always use `sc.exe` or call `sc` as `sc.exe query state= all`.
- Some commands need proper quoting — when in doubt, write the command to a .ps1 file first.

## Verified Tyler desktop access (Aug 2 2026)

Live-tested during the screen-control build. These are the actual working parameters:

- **Reverse tunnel** (run from Tyler's Windows desktop): `ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1237:127.0.0.1:22 lumi@<VM_TAILSCALE_IP>`
- **Connect from Hermes VM**: `ssh -p 1237 -i ~/.ssh/windows_desktop Tyler@127.0.0.1`
- **Login user is `Tyler`** (capital T) — NOT `lumi` or `vesper`. The key file is `~/.ssh/windows_desktop`, no password. Wrong username → `Permission denied (publickey,password,keyboard-interactive)` even with the right key.
- **Push a file**: `scp -P 1237 -i ~/.ssh/windows_desktop <local> Tyler@127.0.0.1:'C:/Users/Tyler/Desktop/<file>'`
- The tunnel only forwards SSH (22 → 1237). The PowerShell screen-control HTTP server is separate, reached over Tailscale at `http://<DESKTOP_TAILSCALE_IP>:8080`.

## Wake-on-LAN — waking the desktop when it's off (researched 8/12)

**Goal:** self-start the rig (boot → ComfyUI → tunnel) without anyone touching
the PC. Plan status: designed, not yet implemented (need Asus router model#).

**Key facts (the part that trips people up):**
- WOL works on **fully off** machines, not just sleep — the NIC stays powered
  by the motherboard standby rail as long as the PSU is on and the power
  strip isn't killed. No need for sleep/hibernate (but disable Windows Fast
  Startup, which hybrid-shuts-down and can break WOL).
- **Tailscale CANNOT deliver the magic packet to an off machine** — Tailscale
  on the desktop is asleep with the desktop. The packet needs an always-on
  relay on the same LAN.
- Wired NIC beats Wi-Fi for magic packets — Tyler's PC is cabled to the Asus.

**Tyler's home topology (Eldorado NM):**
`Xfinity modem (bridged) → TP-Link (bridged) → Asus router (the brain) → PCs cabled`
So the **Asus router is the always-on relay** — the natural WOL sender.

**Path options (best first):**
1. **AsusWRT built-in WOL** — admin UI (Network Tools → Wake on LAN) or SSH
   `ether-wake <MAC>`. From outside: VPN into the Asus (built-in
   OpenVPN/WireGuard) → send packet → PC boots.
2. **Asus models with Tailscale on the router** — then: Linux box → tailnet →
   Asus → magic packet → desktop. Cleanest for me to trigger.
3. **BIOS auto-wake (RTC)** — schedule self-wake (crude but bulletproof).
4. **Always-on helper on LAN** (Pi / old phone with WOL app) — the relay
   + can also auto-start tunnel after boot.

**Needed next:** Asus model number (sticker or admin page) to check
Tailscale support vs VPN route vs Pi fallback. Auto-start chain after wake:
wait for SSH → launch ComfyUI (`wmic process call create ...`) → re-establish
reverse tunnel — scriptable on the Linux side.

## PowerShell script execution policy (learned Aug 2)

Running a downloaded `.ps1` by double-click or `.\script.ps1` fails with `PSSecurityException: running scripts is disabled`. The `-ExecutionPolicy Bypass -File` flag on the command line can still surface parse errors. The reliable per-session fix:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\script.ps1
```

## PowerShell here-string HTML pitfall (learned Aug 2)

Writing an HTML status page as a regular double-quoted string makes PowerShell parse `<li>`, `<b>`, etc. as operators → `Unexpected token` / `The '<' operator is reserved for future use`. Any HTML block in a .ps1 must be a here-string:

```powershell
$html = @"
<html><body><h1>Hi</h1></body></html>
"@
```

Also prefer `$($_.Exception.Message)` over `$_` inside catch-block string interpolation (avoids malformed-string terminator errors).
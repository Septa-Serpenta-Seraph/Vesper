---
name: windows-ssh-tunnel-setup
description: SSH from Linux VM to Windows via tunnel. Setup guide.
---

# Windows SSH Tunnel Setup

This guide documents how to set up SSH access from a Hermes VM (or any Linux machine) to a Windows 11 desktop, using a reverse SSH tunnel to bypass a broken firewall.

## Prerequisites

- Windows 11 with admin access
- A Linux VM (Hermes agent) that can reach outbound to the internet
- Tailscale installed on both machines (or direct IP reachability)
- Windows OpenSSH Server capability

## Step-by-step

### 1. Install OpenSSH Server on Windows

From an **admin PowerShell**:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

### 2. Configure SSH Key Authentication

**On the Linux VM (Hermes side), generate a key pair:**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/windows_desktop -N "" -C "vesper@hermes-windows"
```

**Copy the public key:**

```bash
cat ~/.ssh/windows_desktop.pub
```

**On Windows, install the public key.**

For standard users, place it in:
```powershell
mkdir C:\Users\<username>\.ssh -Force
"<public_key>" | Out-File -Append C:\Users\<username>\.ssh\authorized_keys -Encoding UTF8
```

For admin users, Windows OpenSSH reads from a different file by default:
```powershell
"<public_key>" | Out-File "C:\ProgramData\ssh\administrators_authorized_keys" -Encoding UTF8 -Force
```

**Set correct permissions (critical!):**
```powershell
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "SYSTEM:F" /grant "BUILTIN\Administrators:F"
Restart-Service sshd
```

### 3. Establish the Reverse Tunnel

From Windows (cmd or PowerShell), run:

```cmd
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1236:127.0.0.1:22 linux-user@linux-vm-ip
```

This forwards Windows' SSH (port 22) to port 1236 on the Linux VM.

### 4. Connect from Linux to Windows

From the Linux VM:

```bash
ssh -i ~/.ssh/windows_desktop -o StrictHostKeyChecking=accept-new -p 1236 windows-user@127.0.0.1
```

## Troubleshooting

### Permission denied with key
- Check the file exists at the correct path
- Verify permissions: only SYSTEM and Administrators should have access
- Use `icacls` to check: `icacls "C:\ProgramData\ssh\administrators_authorized_keys"`

### SSH connection refused
- Ensure sshd is running: `sc query sshd`
- Start if needed: `net start sshd`

### sc vs PowerShell
- In PowerShell, `sc` is an alias for `Set-Content`, not the Service Controller
- Always use `sc.exe` or `sc` in PowerShell when you mean Service Controller

### Port 22 blocked by firewall
- Use the reverse tunnel approach (step 3) — the Windows machine initiates the outbound connection, so no inbound firewall rule is needed
- The tunnel survives reboots if you set up a scheduled task to re-establish it

## Key Files

- Linux key: `~/.ssh/windows_desktop` (private, keep secure)
- Linux key: `~/.ssh/windows_desktop.pub` (public, share with Windows)
- Windows authorized_keys: `C:\ProgramData\ssh\administrators_authorized_keys`
- Windows user authorized_keys: `C:\Users\<username>\.ssh\authorized_keys`
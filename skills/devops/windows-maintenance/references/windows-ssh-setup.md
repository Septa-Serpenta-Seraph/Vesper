# Windows OpenSSH Setup (for remote diagnostics)

## Installation

```powershell
# Install OpenSSH Server (Windows 10/11 built-in feature)
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start and enable
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

## Authentication key setup

### The administrators_authorized_keys quirk (CRITICAL)

Windows OpenSSH has a non-obvious default: **if the user is a member of the Administrators group**, the server ignores `%USERPROFILE%\.ssh\authorized_keys` and instead reads from:

```
C:\ProgramData\ssh\administrators_authorized_keys
```

This is caused by the sshd_config having an additional `AuthorizedKeysFile` directive pointing to `__PROGRAMDATA__/ssh/administrators_authorized_keys` (typically at the bottom of the file). That directive overrides the user-level path for admin accounts.

### Setup steps

1. **Generate a key pair** on the remote VM (if one doesn't exist):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/windows_desktop -N "" -C "agent@hostname"
   ```

2. **Add the public key** to the administrator's authorized_keys file:
   ```powershell
   # Create administrators_authorized_keys (one-time)
   "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA..." | Out-File "C:\ProgramData\ssh\administrators_authorized_keys" -Encoding UTF8
   ```

3. **Fix permissions** — Windows SSH is EXTREMELY picky about file permissions:
   ```powershell
   icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r
   icacls "C:\ProgramData\ssh\administrators_authorized_keys" /grant "SYSTEM:(F)"
   icacls "C:\ProgramData\ssh\administrators_authorized_keys" /grant "BUILTIN\Administrators:(F)"
   ```

4. **Restart sshd**:
   ```powershell
   Restart-Service sshd
   ```

### Verification

```powershell
# Check service is listening
netstat -ano | findstr :22

# Check the correct file is being read
Get-WinEvent -LogName OpenSSH/Operational -MaxEvents 10 | Format-Table TimeCreated, Message
```

## Troubleshooting

### sshd doesn't start after reboot

After installing OpenSSH Server, the service may **not be registered** in a way that survives reboot. Symptoms:

- `sc query sshd` returns nothing (no output at all)
- `sc start sshd` returns nothing or "service not found"
- `net start sshd` works (`"The OpenSSH SSH Server service was started successfully"`)

**Why**: `Add-WindowsCapability` may not fully register the service in the SCM database. After reboot, the binary exists but the service isn't in `sc query`. The `net start` command is more lenient — it can often start services that `sc start` can't.

**Fix**: Re-run `net start sshd` after reboot. If `sc query sshd` still shows nothing, re-register:
```powershell
# Check if the binary exists
dir "C:\Windows\System32\OpenSSH\sshd.exe"

# Create the service if missing
sc.exe create sshd binPath="C:\Windows\System32\OpenSSH\sshd.exe" start= auto
```

### sc vs sc.exe in PowerShell

In PowerShell, `sc` is an **alias for `Set-Content`**, not the Service Controller. This causes cryptic errors:

```powershell
# WRONG — runs Set-Content, not Service Controller
sc query sshd
# → "A positional parameter cannot be found that accepts argument 'query'"

# RIGHT — use sc.exe (the actual binary)
sc.exe query sshd
```

Always use `sc.exe` in PowerShell, or use `cmd /c "sc query sshd"` when SSHing in.

### sshd works for `net start` but not `sc start`

If `sc start sshd` fails with error 1058 or "service not found" but `net start sshd` works, the service may have a corrupted security descriptor or be registered slightly differently. Use `net start` as the reliable fallback.

### `sc query` gives no output after reboot

This is the most common symptom of an incomplete OpenSSH Server installation. Run:
```cmd
net start sshd
```
Check afterward with `netstat -ano | findstr :22` to confirm it's listening.

## Connecting through an SSH reverse tunnel

When a broken firewall blocks direct connections (port 22), route through an existing reverse tunnel:

1. **User sets up a reverse port forward** from their Windows desktop to your VM:
   ```cmd
   ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1236:127.0.0.1:22 user@remote-vm-ip
   ```

   This forwards the desktop's port 22 to port 1236 on the VM's loopback interface.

2. **Connect from the VM**:
   ```bash
   ssh -i ~/.ssh/windows_desktop -p 1236 windows-user@127.0.0.1
   ```

3. **Run Windows commands** through the tunnel:
   ```bash
   # CMD (preferred — quoting works reliably)
   ssh -i ~/.ssh/windows_desktop -p 1236 tyler@127.0.0.1 cmd /c "sc query mpssvc"

   # PowerShell — single commands (avoid nested quotes)
   ssh -i ~/.ssh/windows_desktop -p 1236 tyler@127.0.0.1 powershell Get-Service mpssvc
   ```

## Workflow: using the tunnel

Once the tunnel is active:

1. **Run commands directly from your side** — Don't ask the user to type diagnostics; you're already remote. `ssh -p 1236 user@127.0.0.1 cmd /c "command"` runs instantly.
2. **Run each SSH command separately** for clarity / per-step verification — batch in one call only when the commands are independent.
3. **Use `cmd /c "..."` for quoting** — CMD handles pipes, redirects, and `&&` chaining without mangling. PowerShell `-Command` with nested quotes **will** break over the tunnel.
4. **For PowerShell-only tasks**, write a `.ps1` file first, then execute: `powershell -File C:\path\to\script.ps1 -ExecutionPolicy Bypass`

## Copy-paste hygiene

When giving the user terminal commands to run:
- **Always split multi-step instructions into separate lines** — one command per code block. Copy-pasting joined commands as one long line causes `ParameterBindingException` in PowerShell.
- Use separate code blocks for each command.
- Tell the user explicitly: "Run these one at a time."

## Quoting pitfalls over SSH to Windows

- `cmd /c "command"` handles `|`, `&`, `>`, `&&`, nested quotes, and `for` loops correctly
- `powershell -Command "..."` **mangles** when the command contains nested quotes, pipes (`|`), or `Select-Object` with curly braces
- For complex PowerShell: write a `.ps1` file and execute it via `powershell -File C:\path\to\script.ps1`
- For simple PowerShell: `powershell Get-Service mpssvc` works fine (one command, no special chars)
- Use `^` to escape `|`, `>`, `<` inside cmd.exe when needed

## Common failures

| Symptom | Likely cause |
|---|---|
| `Permission denied (publickey)` | Wrong authorized_keys file, or permissions too permissive |
| `Permission denied (password)` | Password auth disabled, or wrong username |
| `Connection timed out` | Firewall blocking port 22, or tunnel not set up |
| `ssh: connect to host port 22: Connection refused` | sshd not running, or wrong port |
| `The parameter is incorrect` | sshd_config has a syntax error |
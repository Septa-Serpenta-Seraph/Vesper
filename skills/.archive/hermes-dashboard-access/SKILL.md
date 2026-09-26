---
name: hermes-dashboard-access
description: "Access the Hermes Agent web dashboard remotely — SSH tunnel, Tailscale Serve, and auth configuration. Covers port 9119, bind options, the June 2026 auth hardening, and distinguishing the Hermes dashboard from the AEGIS dashboard."
version: 1.0.0
author: Lu
tags: [hermes, dashboard, remote-access, ssh, tailscale, devops]
---

# Hermes Dashboard Remote Access

The Hermes Agent web dashboard (`hermes dashboard`) provides a browser UI for
managing config, API keys, sessions, and more. This skill covers how to access
it from a remote machine (host PC, another tailnet node, etc.).

## Key Facts

- **Port:** 9119 (default)
- **Default bind:** `127.0.0.1` (localhost only — not reachable from other machines)
- **Auth hardening (June 2026):** Non-loopback binds (`--host 0.0.0.0` etc.) **require** authentication (password or OAuth). The `--insecure` flag is a **no-op** — it no longer disables auth.
- **CLI:** `hermes dashboard [--port PORT] [--host HOST] [--skip-build] [--no-open] [--status] [--stop]`

## Distinguishing From AEGIS Dashboard

The `install-dashboard` skill (aegis category) installs the **AEGIS Dashboard**
— a separate Flask app on port 5000 that monitors metrics. It is **NOT** the
Hermes Agent web dashboard. Do not confuse them when a user says "dashboard."

- AEGIS Dashboard → port 5000, Flask, metrics visualization
- Hermes Dashboard → port 9119, `hermes dashboard` command, full agent management UI

## Access Methods

### Method 1: SSH Port Forwarding (Preferred for Local Network)

Simplest approach. Dashboard stays on localhost (no auth needed), SSH handles
the tunnel. Works for any host-to-VM or machine-to-machine scenario.

From the remote machine:
```bash
ssh -L 9119:127.0.0.1:9119 <user>@<vm-ip>
```

Then open `http://localhost:9119` in a browser on the remote machine.

**Requirements:**
- SSH server running on the VM (`systemctl is-active ssh`)
- Dashboard running on the VM (`hermes dashboard --status` to check)

### Method 2: Tailscale Serve (Tailnet-Wide Access)

Exposes the localhost dashboard to the entire tailnet without changing the
dashboard's bind address or requiring dashboard auth. Tailscale's mesh
encryption handles security.

```bash
# One-time: set operator so sudo isn't needed each time
sudo tailscale set --operator=$USER

# Expose the dashboard
tailscale serve 9119
```

Then access from any tailnet node at `http://<vm-tailscale-hostname>/` (port 80,
served by Tailscale) or with MagicDNS at `http://<hostname>.<tailnet>.ts.net/`.

**Requirements:**
- Tailscale installed and running on the VM
- Tailscale Serve **enabled** on the tailnet (admin console → Settings)
- `sudo` access for one-time `--operator` setup

**Check serve status:** `tailscale serve status`
**Reset serve:** `tailscale serve reset`

### Method 3: Direct Bind with Auth

Bind the dashboard to all interfaces and configure password auth.

```bash
# Set a password in config
hermes config set dashboard.basic_auth.password "your-password"

# Restart dashboard with non-loopback bind
hermes dashboard --host 0.0.0.0
```

Then access at `http://<vm-ip>:9119` from any machine. You'll be prompted
for the password.

**Note:** OAuth via Nous Portal is also available: `hermes dashboard register`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Serve is not enabled on your tailnet" | Enable Serve in Tailscale admin console |
| "Access denied: serve config denied" | Run `sudo tailscale set --operator=$USER` once |
| Dashboard not reachable | Check `hermes dashboard --status` and `ss -tlnp \| grep 9119` |
| Non-loopback bind rejected | Auth required — set password or use SSH tunnel instead |
| `sudo: a terminal is required` | Can't run sudo from agent terminal without askpass — use SSH tunnel or ask user for one-time sudo |

## Pitfalls

- **Wrong dashboard skill loaded first.** The `install-dashboard` skill (aegis)
  is for AEGIS, not Hermes. When a user says "Hermes dashboard" or "your
  dashboard," they mean `hermes dashboard` on port 9119, NOT AEGIS.
- **`--insecure` does nothing now.** Don't suggest it as a workaround.
- **No passwordless sudo in agent terminal.** The agent can't run `sudo` without
  a TTY. For Tailscale Serve operator setup, either ask the user to run it via
  SSH/console, or use SSH tunnel instead (no sudo needed).
- **Dashboard may already be running.** Check with `hermes dashboard --status`
  before starting a new instance.

# Hermes Dashboard Remote Access

Absorbed from the `hermes-dashboard-access` skill (archived).

## Key Facts
- **Port:** 9119 (default)
- **Default bind:** `127.0.0.1` (localhost only)
- **Auth hardening (June 2026):** Non-loopback binds **require** authentication. `--insecure` is a **no-op**.
- **CLI:** `hermes dashboard [--port PORT] [--host HOST] [--skip-build] [--no-open] [--status] [--stop]`

## Distinguishing From AEGIS Dashboard
The `install-dashboard` skill manages the **AEGIS Dashboard** (port 5000, Flask, metrics). The Hermes Dashboard is port 9119, the `hermes dashboard` command, full agent management UI. Do not confuse them.

## Access Methods

### SSH Port Forwarding (Preferred for Local Network)
```bash
ssh -L 9119:127.0.0.1:9119 <user>@<vm-ip>
```
No dashboard auth needed — SSH handles security. Open `http://localhost:9119`.

### Tailscale Serve (Tailnet-Wide Access)
```bash
sudo tailscale set --operator=$USER
tailscale serve 9119
```
Access at `http://<vm-tailscale-hostname>/` from any tailnet node.

### Direct Bind with Auth
```bash
hermes config set dashboard.basic_auth.password "your-password"
hermes dashboard --host 0.0.0.0
```
Access at `http://<vm-ip>:9119` — prompted for password.

## Troubleshooting
| Problem | Fix |
|---------|-----|
| "Serve is not enabled" | Enable Serve in Tailscale admin console |
| "Access denied: serve config denied" | `sudo tailscale set --operator=$USER` |
| Dashboard not reachable | `hermes dashboard --status` + `ss -tlnp \| grep 9119` |
| Non-loopback bind rejected | Auth required — use SSH tunnel instead |
| `sudo: a terminal is required` | Use SSH tunnel or ask user for one-time sudo |

## Pitfalls
- **Wrong dashboard skill.** The `install-dashboard` skill (aegis) is for AEGIS, not Hermes.
- **`--insecure` does nothing now.** Don't suggest it as a workaround.
- **No passwordless sudo in agent terminal.** For Tailscale Serve, ask the user or use SSH tunnel.
- **Dashboard may already be running.** Check with `hermes dashboard --status` first.
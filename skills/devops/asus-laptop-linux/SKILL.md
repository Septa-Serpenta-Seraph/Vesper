---
name: asus-laptop-linux
description: "Use for ASUS Zephyrus/ROG laptop battery limits on CachyOS."
version: 1.0.0
---

# ASUS Laptop on Linux (CachyOS/Arch) — Power & Feature Management

Tyler's daily driver: **ASUS Zephyrus G16 on CachyOS**. Battery charge-limit
resets every boot (classic ASUS ACPI behavior) — this skill is the durable
fix and the asusctl CLI reference. Verified 2026-08-13.**CORRECTED 2026-09-05: the battery is BAT1, NOT BAT0** — writing to
`BAT0/.../charge_control_end_threshold` silently does nothing (path doesn't exist;
that's why limits stopped applying). Always verify `ls /sys/class/power_supply/` first.
**ALSO CORRECTED (9/5): current asusctl uses SUBCOMMANDS** — `asusctl battery limit 80`,
`asusctl battery info`, `asusctl battery oneshot` (old flags like `-s 80` / `-l 80` are rejected).

**⚠️ CORRECTED 2026-09-04: the battery is `BAT1`, NOT `BAT0`.** On this
machine `/sys/class/power_supply/` contains `BAT1` (plus `ACAD` charger and
`ucsi-source-psy-USBC000:001/002`). Pointing at `BAT0` fails SILENTLY (path
doesn't exist — the command "works" but does nothing). **Always use
`/sys/class/power_supply/BAT1/charge_control_end_threshold`.**

## SSH access (set up 2026-09-04)

- From the gateway box: `ssh -i ~/.ssh/cachyos_laptop tyler@192.168.0.34`
  (LAN-only; laptop UFW now has `allow ssh`, sshd enabled). IP may change on
  DHCP — re-discover with `hostname -I` on the laptop if it stops working.
- The laptop shell is **fish** — no heredocs (`<<'EOF'` fails); write config
  files with `printf '...\n' | sudo tee file`. Bash `for` loops also fail
  remotely — keep remote commands simple/one-liners.
- `sudo` over non-TTY SSH cannot prompt for password — have Tyler run
  password-requiring steps (e.g. `systemctl enable`) himself in his terminal.

## Battery charge limit — the problem

On Linux the ASUS ACPI driver re-initializes `charge_control_end_threshold`
at every boot, so MyASUS-style limits don't persist. Symptom: laptop charges
to 100% no matter what you set. Not a bug on the user side — the driver
forgets. CachyOS users specifically report asusctl limits being flaky
(set 80, battery creeps to 100 sometimes).
- **9/5 — RESOLVED (root cause found 9/4):** bypass charging was "not stopping
  where I set it" because every script/precedent used `BAT0`, which doesn't
  exist on this machine; the real battery is `BAT1`. Fixed live: `asusctl
  battery limit 80` → confirmed `Not charging` (bypass) at 83% capacity.
  **VERIFIED COMPLETE 9/5:** the one-shot `battery-limit.service` was written,
  `systemctl enable` ran (symlink created), and the 80% threshold persists
  across reboots — bypass confirmed holding (BAT1 status `Not charging` above
  the limit). Do not re-enable; it's done.

## THE fix (version-proof, always works) — sysfs + systemd

```bash
# Set now (80% = sweet spot; 60 = max lifespan) — note BAT1, not BAT0:
echo 80 | sudo tee /sys/class/power_supply/BAT1/charge_control_end_threshold
# Verify:
cat /sys/class/power_supply/BAT1/charge_control_end_threshold   # → 80
```

**Persist across boots** — one-shot systemd service (cleanest on CachyOS;
fish shell must use `printf`, not heredocs):

```bash
printf '[Unit]\nDescription=Set ASUS battery charge limit\nAfter=multi-user.target\n\n[Service]\nType=oneshot\nExecStart=/bin/sh -c '\''echo 80 > /sys/class/power_supply/BAT1/charge_control_end_threshold'\''\n\n[Install]\nWantedBy=multi-user.target\n' | sudo tee /etc/systemd/system/battery-limit.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable battery-limit.service
```

### Bypass / direct-AC behavior

When the battery is at/above the limit while plugged in, the laptop
effectively runs off AC — that IS bypass in all but name. A 60-80% cap +
plugged-in use = battery idles at the limit, draws from the brick, barely
ages. That's the healthy "always plugged in" setup.

## asusctl CLI — NEW versions use subcommands, not flags

**Pitfall (bit me 8/13):** recent asusctl versions reject `-s`/`-l` flags:
```
asusctl profile -s 80      → Unrecognized argument: -s
asusctl battery -l 80      → Unrecognized argument: -l
```
`-s`/`-l` are OLD syntax. If flags are rejected, check subcommands:
```bash
asusctl --help        # shows command list (aura, profile, fan-curve, battery...)
asusctl battery --help  # subcommand-specific usage
```
When in doubt, prefer the **sysfs write** above — it never depends on
asusctl version. `asusctl battery -l 80` only works on versions that
accept the flag; the sysfs path works everywhere.
- **CONFIRMED WORKING 9/4:** `asusctl battery limit 80` (subcommand +
  positional arg) sets the limit correctly on this machine — use this instead
  of the old flag syntax. `asusctl battery info` reads it back (shows
  `Current battery charge limit: 80%`).

## Daemon start quirk

`sudo systemctl enable --now asusd` may fail with "unit files have no
installation" — that's a missing [Install] section, NOT a broken daemon.
Use `sudo systemctl start asusd` to run it now, and the systemd service
above for the persistent battery limit.

## Related

- `linux-dual-boot` — dual-boot prep if ever needed
- `windows-maintenance` — the OTHER box (Windows desktop)

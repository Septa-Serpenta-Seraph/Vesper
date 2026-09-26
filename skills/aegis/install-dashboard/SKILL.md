# AEGIS Install Dashboard Skill

System-level skill: install and configure the AEGIS Dashboard on the local machine.

**Requires:** Docker, sudo privileges (to start Docker if inactive).

## Usage

Run once to set up AEGIS:

```
install AEGIS dashboard
```

Steps performed:
- Check Docker; attempt to start it if inactive (may prompt for sudo)
- Clone the AEGIS-Dashboard repo to `/opt/AEGIS-Dashboard`
- Install Python dependencies via pip
- Create `.env` from `.env.example`
- Print instructions to run the dashboard

To launch immediately after install, run with `--run` flag (blocks until Ctrl-C).

## Post-Install

1. Edit `/opt/AEGIS/.env` to set any needed secrets (DISCORD_TOKEN, etc.)
2. Start the dashboard: `cd /opt/AEGIS-Dashboard && python app.py`
3. Verify: `curl http://localhost:5000/api/health`
4. Set `AEGIS_API_URL` env var if not localhost

## Notes

- Dashboard runs Flask on port 5000, expects Qdrant at `http://localhost:6333`
- If Qdrant is elsewhere, adjust `app.py` or set `QDRANT_URL`
- If Docker cannot be started automatically, manually run:
  `sudo systemctl start docker`

# `hermes cron` CLI Reference

The CLI for managing Hermes cron jobs. Verified 2026-08-31 (cron librarian session).

## Listing jobs

```
hermes cron list
```

Shows every job with: status (active/paused), name, schedule, last run timestamp + status, next run, delivery target, script (if any), agent/no-agent mode. **This is the ONLY way to see full job details** — there is no `hermes cron view <id>` subcommand.

The `status` subcommand (`hermes cron status`) is a boolean toggle that shows whether the gateway is running and the count of active jobs — it does NOT take a job ID.

## Creating a job

```
hermes cron create '<schedule>' ['prompt'] \
  --name '<human-readable-name>' \
  --deliver '<target>' \
  --skill '<skill-name>' \
  [--script '<script-path>'] \
  [--no-agent] \
  [--workdir '<abs-path>'] \
  [--repeat '<count>']
```

**Positional args:**
- `schedule` — cron expression or human form (`'every 90m'`, `'0 9 * * *'`)
- `prompt` — optional instruction for the agent (omit for no_agent jobs)

**Key flags:**
- `--name` — human-friendly name shown in `hermes cron list`
- `--deliver` — delivery target: `origin`, `local`, `discord:<channel-id>`, `telegram:<chat-id>`, etc. **`origin` goes stale if the user leaves the origin server.**
- `--skill` — attach a skill to the job's context. Repeatable (one `--skill` per skill).
- `--script` — path under `~/.hermes/scripts/`. In agent mode, stdout is injected into the prompt. With `--no-agent`, the script IS the job and its stdout is delivered verbatim.
- `--no-agent` — skip the LLM entirely. Script stdout delivered directly. Empty stdout = silent ($0 tick).
- `--workdir` — absolute path for job's cwd. Injects project context files.
- `--repeat` — optional repeat count (default: infinite)

**Returns:** the job ID (e.g. `c1125b79f96f`) printed on creation.

## Managing jobs

```
hermes cron pause <job-id>     # suspend without removing
hermes cron resume <job-id>    # unsuspend
hermes cron remove <job-id>    # permanently delete
hermes cron run <job-id>       # fire immediately (test)
```

**Pause** is preferred over remove for temporary suspension — resume is a single command and the job's config stays intact.

**Remove** is irreversible. Use only for truly dead jobs.

## Editing jobs

`hermes cron edit <job-id>` — edit an existing job's configurable fields.

Supported flags: `--schedule`, `--prompt`, `--name`, `--deliver`, `--repeat`, `--skill`, `--add-skill`, `--remove-skill`, `--clear-skills`, `--script`, `--no-agent`, `--agent`, `--workdir`.

Examples:
- **Change delivery target:** `hermes cron edit <job-id> --deliver 'discord:1530634184920404222'`
- **Add a skill:** `hermes cron edit <job-id> --add-skill tylers-day`
- **Update schedule:** `hermes cron edit <job-id> --schedule '0 9 * * *'`

**Important — NO model/provider flag exists.** The `hermes cron edit` command has NO `--model` or `--provider` option (confirmed 2026-09-28). Model is set at creation time only. To swap a dead model:

**Swap model (CLI unsupported — direct JSON edit):**
```bash
# Stop Hermes gateway first, then:
patch ~/.hermes/profiles/vesper/cron/jobs.json <<EOF
old_string: "model": "dead-model:free",
new_string: "model": "deepseek/deepseek-v4-flash",
EOF
# Update provider, provider_snapshot, model_snapshot fields too:
old_string: "provider_snapshot": null,
new_string: "provider_snapshot": "openrouter",
old_string: "model_snapshot": null,
new_string: "model_snapshot": "deepseek/deepseek-v4-flash",
# Also update the file's updated_at timestamp.
```
Then verify with `hermes cron list | grep <job-id>` (the model field is not displayed in list output, but the job's last_status error should clear on next run).

**Convert no_agent→agent:** cannot be done with edit. Remove the old job and create it fresh.

## Key pitfalls

| Pitfall | Detail |
|---------|--------|
| No `hermes cron view` | Use `hermes cron list` and grep for the job name/id |
| `status` doesn't take id | `hermes cron status` is a gateway-health boolean, not a per-job check |
| `--deliver origin` goes stale | When user leaves a server, origin deliveries become invisible. Pin explicit target for recurring jobs. |
| `--no-agent` is sticky | Cannot be removed via update. Must remove + recreate to switch modes. |
| Model pins are Tyler's domain | Never modify a healthy job's model or provider unless explicitly asked. **Exception:** a dead model (provider dropped it, 404 on every run) IS a maintenance fix — patch to a working model. This is fixing a broken job, not overriding a preference. |
| Protected jobs | Never touch: `8875415539a6` (vesper-reflection), `54aafcb784d2` (vesper-token-ledger), `8a66afec4d92` (monthly audit). |
| Model swap not in CLI | `hermes cron edit` has NO `--model` or `--provider` flag. To swap a dead model, patch `~/.hermes/profiles/vesper/cron/jobs.json` directly — update `model`, `provider`, `provider_snapshot`, `model_snapshot`, and `updated_at`. |

## Change log requirement (mandatory, 8/19 rule)

Every cron change — create, update, pause, remove — MUST be appended to `state/system-change-log.md` (canonical; `cache/documents/system-change-log.md` is a symlink to it) with:
- Numbered row in the table format: `| # | Date | Change | Job ID | Revert instructions |`
- Revert instructions must be copy-pasteable (e.g. `hermes cron remove <id>` or `hermes cron pause <id>`)
- Audit passes get a row with `(entire table)` as the job ID and "N/A — routine audit" as revert

If the file doesn't exist, create it with header `# System Change Log` and the table header row.
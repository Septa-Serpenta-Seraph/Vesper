# Cron scheduling, collisions, and the two watchdogs

Companion to the cron-fleet section of SKILL.md. Read this before changing any
cron schedule, and before "fixing" a job that failed.

Written 2026-10-12 after three consecutive days of cron failures that all looked
like provider problems and were all scheduling problems.

---

## 1. The fleet map — CORRECT as of 2026-10-12 (UTC → MT)

Cron expressions are **UTC**. MT = UTC − 6 (MDT). Every entry below is
deliberately placed; the "why" column is the part that keeps it correct.

| Job | Job ID | Schedule (UTC) | = MT | Why it sits there |
|---|---|---|---|---|
| Raven's Hour | `ebb36b00afd1` | `0 2 * * *` | 8:00 PM | **Deliberate** — it's Tyler's evening window by design. The one job allowed in chat hours. |
| Reflection | `8875415539a6` | `0 9 * * *` | 3:00 AM | Moved off 10 PM on 10/11 (collision). Also a *better* slot: distills the whole previous day incl. evening. |
| Cron librarian | `2dab0be2c2b4` | `0 10 * * 1` | 4:00 AM Mon | Moved off 9 PM on 10/11 (collision). |
| Token ledger | `54aafcb784d2` | `30 10 * * 0` | 4:30 AM Sun | Moved off 9:30 PM on 10/11 (collision). |
| Monthly audit | `8a66afec4d92` | `0 11 1 * *` | 5:00 AM 1st | Moved off 9 PM on 10/11 (collision). |
| Reflection safety net | `e81f6bc02650` | `30 11 * * *` | 5:30 AM | Catches a failed reflection (see §4). |
| Open-door | — | `0 12,20 * * *` | 6 AM, 2 PM | Daytime, low contention. |
| Serendipity | `51c93ede24a3` | `0 14 * * *` | 8:00 AM | — |
| GitHub backup | — | `0 5 * * *` | 11:00 PM | Script only, $0, no model. |
| Qdrant weekly backup | — | `0 5 * * 0` | 11:00 PM Sun | Script only. |
| Full profile backup | — | `0 6 * * 0` | 12:00 AM Sun | Script only. |
| Cron health watchdog | `cbf693109b0d` | `0 13 * * *` | 7:00 AM | Script only, silent-unless-broken. |
| Memory indexer | — | every 5 min | — | Local, no API. |
| Qdrant health | — | every 5 h | — | Local, no API. |

**The dead zone is 07:00–11:00 UTC (1 AM – 5 AM MT).** That is where every LLM
job belongs. The 02:00–04:00 UTC band (8–10 PM MT) is the danger zone — that is
when Tyler and I are actually talking.

⚠️ **This table goes stale the moment a schedule moves. Update it in the same
change, or the next session reads a confident lie.** The table previously said
librarian `0 3 * * 1`, token-ledger `30 3 * * 0`, audit `0 3 1 * *` — all three
had been moved and the skill kept asserting the old slots.

---

## 2. The collision rule — a repeating 429 at a fixed clock time is a SCHEDULE fault

The default instinct is that `429` / `402` are account conditions and not worth a
config change. **That is right for one-off 429s and wrong for repeating ones.**

**Diagnostic:** look at *when* the failures land, not just that they happened.

- `vesper-reflection` failed three nights running: 10/9 (402, credits), then
  10/10 and 10/11 (**429**), with `last_run_at` = `04:02:23` UTC both times —
  i.e. **10 PM MT**, peak conversation hour.
- The job's request was landing on the same API key at the same moment as the
  live session's traffic. The rate limiter picked a loser.

**It was not transient and not credits — it was collision.** Moving the job to
09:00 UTC fixed it outright.

**Confirmed a second time the same day:** the librarian fired at 03:00 UTC
(9:00 PM MT Sunday) and 429'd; Tyler reported it at 9:02 PM — two minutes later,
mid-conversation. Same shape.

**Rules:**

1. **Map every cron to MT before trusting a schedule.** A "harmless" `0 4 * * *`
   is 10 PM to Tyler.
2. **Never schedule an LLM cron into his active hours** (roughly 08:00–23:00 MT).
   Those slots contend with the live session for the same key. Evenings are the
   worst.
3. **A quiet slot is often a *better* slot.** A 3 AM reflection distills the
   whole previous day including the evening — the 10 PM run was cutting off
   exactly the hours with the richest material. Don't frame a schedule change as
   merely defensive.
4. **Ask "does this 429 have a clock-time signature?"** before filing it as
   transient. Same time every day ⇒ move it.
5. **Audit the whole band, not just the reported job.** Tyler reported the
   librarian; the audit found three jobs clustered in the same window. Fixing
   only the reported one leaves two landmines.

---

## 3. The inactivity watchdog — why a *working* job gets killed mid-generation

Cron agent sessions run under an **inactivity watchdog**, not a wall-clock
timeout: `cron/scheduler.py::_cron_inactivity_seconds()`.

- **Default 600 s (10 min) of idle.**
- Override: env var **`HERMES_CRON_TIMEOUT`** (seconds; **`0` = unlimited**).
- Read per-dispatch through `cron_env_setting()`, which resolves from the
  **profile `.env`** (`~/.hermes/profiles/vesper/.env`) — so it can be changed
  without a gateway restart.

### The failure signature

```
TimeoutError: Cron job 'vesper-reflection' idle for 600s (limit 600s)
  — last activity: waiting for non-streaming API response
```

**This is not the provider refusing us. It is us hanging up on the provider.**

Responses are **non-streaming**, so while a generation is in flight *nothing
reports progress*. A long generation is therefore indistinguishable from a dead
job — the watchdog cannot tell them apart and pulls the plug on something that
was still breathing.

**Jobs with big prompts and big context are the exposure** (the reflection prompt
is a multi-step essay and its context includes `session_search` dumps). The
bigger the prompt, the more likely one response exceeds the window.

### Fix, in order of preference

1. **Slim the prompt.** This is the real fix — the timeout raise only tolerates
   slow responses, it doesn't remove the cause.
2. **Raise the tolerance.** `HERMES_CRON_TIMEOUT=1200` in the profile `.env`
   (set 2026-10-12; backup at `.env.bak-20261012-crontimeout`). 20 min of idle
   tolerance instead of 10. Raise, don't unlimit — `0` would let a genuinely
   wedged job hold the scheduler indefinitely.
3. Related knob: `agent.gateway_timeout: 1800` is the *gateway's* limit, higher
   than cron's. Don't confuse the two.

⚠️ **If the gateway cached the env scope at startup, the `.env` change only
takes effect on restart.** Test with the next scheduled run before assuming it
landed. `hermes gateway restart` bounces *every* profile's gateway including
`default` — another being's runtime — so **ask Tyler first** (see the update
section of SKILL.md).

### Related: the same watchdog hits Raven's Hour

Seen 9/14: raven-hour hard-timed out at 600 s idle, recorded `(FAILED)` in
`cron/output/ebb36b00afd1/`, and delivered nothing — **by design**, since it
delivers `local`. If an evening's shiny is missing from the log, check the output
dir for a FAILED file before assuming the hour was spent quiet.

---

## 4. Alerting is not recovery — the safety-net pattern

The cron-health watchdog **flags**; it never fixes. That left a real gap: the
reflection failed four days straight (402 credits, then 429s, then a 600 s hang)
and **nothing recovered the lost days** — every failure just produced an alert.

**Fix (built 2026-10-12, `reflection-safety-net`, job `e81f6bc02650`):** a daily
**no_agent, zero-token** script that reads `cron/jobs.json`, and if the
reflection's latest run failed *within the last 6 h*, re-triggers it with
`hermes cron run 8875415539a6`. Silent otherwise. It never edits the job it
watches — only re-runs it.

**Generalise this:** for any job whose output is *load-bearing* (the reflection
maintains CURRENT STATE; the token ledger keeps history), a failure detector is
not enough. Pair the alerter with a **recovery job** that retries the work. The
test is: *if this job silently didn't run, would anything notice within a week?*
If the answer is "only an alert nobody acted on," it needs a safety net.

Corollary: **check whether the miss actually mattered before escalating to
Tyler.** In this case the safety net had already re-run the reflection
successfully at 11:30 UTC — so the whole incident was an error line and a missed
3 AM slot, not a lost day. Say that explicitly; it's the difference between
information and alarm.

---

## 5. Two watchdogs, two jobs — don't conflate them

| Watchdog | Watches | Fails how | Fix belongs to |
|---|---|---|---|
| **Inactivity watchdog** (`_cron_inactivity_seconds`, in-process) | One job's own silence during a run | Kills a live job mid-generation | `HERMES_CRON_TIMEOUT`, or a slimmer prompt |
| **Cron health watchdog** (`scripts/cron-health-watchdog.py`, a job) | Every job's `last_status` across runs | Alerts once per failure event | The failing job's own config |

A first draft of the health watchdog keyed only on *current* status and re-fired
daily on the same failure. **Any alerting system keyed on a last-known-status
field will re-nag whenever the producing job's cadence is longer than the
alert's** — dedupe on the **event** (`(job_id, last_run_at)`), not the state.

---

## 6. A script job can fail *successfully* — invisible to a status watchdog

Both watchdogs above read fields (`last_status`, activity). Neither can see a
script that **exits 0 while every unit of its work failed** — the run records
`ok`, and the fleet looks healthier the worse it gets. The **memory indexer**
did exactly this (found 2026-10-12): it stalled on an embedding-provider **402**,
indexed 0 chunks, and *still printed* `[+] Cursor advanced to <id>` — claiming
progress it had not made. The cursor was only actually written when `indexed > 0`,
so the index was frozen while every status field read healthy. Symptom from the
outside: **recall goes stale but chat feels fine.**

**Rules:**

- **A progress line must be conditional on real progress.** Print "cursor
  advanced" only in the branch where it advanced. An unconditional success
  message converts a dead run into a silent one.
- **Exit non-zero when work was attempted and none succeeded.** A status-based
  watchdog cannot read a lie; the exit code is the only signal it *can* read.
- **This is the script-job twin of the stale-latch bug (§5)** — same root cause
  (the watchdog trusts a field), opposite direction (the field says *fine* when
  it isn't).
- **Test the failure path, not just the happy path.** Force the provider to error
  (bad key / exhausted credits) and confirm the run *looks* failed — exit code,
  stdout, and `last_status` all agreeing. A script whose failure mode is
  indistinguishable from success will hide for weeks.
- **Same family as the safety-net timeout bug in SKILL.md:** a wrapper that
  prints its own failure into a file nobody reads looks exactly like a healthy
  wrapper. Whenever you build something that reports on itself, verify the
  reporting path under failure.

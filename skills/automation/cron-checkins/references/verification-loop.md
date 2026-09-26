# Verification Loop — prove both branches without spamming

Never ship a check-in cron unverified. Test HOLD and SPEAK on real runs.

## 1. Prove HOLD -> silence
- Ensure the reader's decision logic is live (no test override).
- Trigger: `cronjob action=run job_id=<id>`.
- Inspect the cron session:
  ```python
  # find latest cron session, read its messages
  SELECT id FROM sessions WHERE id LIKE 'cron_<jobid>%' ORDER BY started_at DESC LIMIT 1;
  SELECT role, content FROM messages WHERE session_id=? ORDER BY id;
  ```
  Expect: tool output `DECISION: HOLD:...` then assistant `[SILENT]`.
- Confirm no delivery leaked:
  ```sql
  SELECT * FROM delivery_obligations ORDER BY rowid DESC LIMIT 3;
  ```
  The target chat should show **no new row** from this run.

## 2. Prove SPEAK -> real message (no DM spam)
- Temporarily force SPEAK: set `speak = True` in the reader (a `# TEST_FORCE`
  line), OR lower the quiet floor.
- Switch the job to local-only so nothing hits the user's DM:
  `cronjob action=update job_id=<id> deliver=local`
- Trigger the run; read the generated message:
  - File: `cron/output/<job_id>/<timestamp>.md` (the `## Response` section), OR
  - The assistant message in the cron session (see query above).
- Confirm it is in-voice, grounded in the recent thread, and open-ended.

## 3. Revert
- Remove the `TEST_FORCE` flag; restore real decision logic.
- Restore delivery: `cronjob action=update job_id=<id> deliver=discord:<chat_id>`.
- Run once more with real logic; confirm `DECISION` matches expectation.

## Why this matters
A check-in that "works on paper" can silently spam (every tick SPEAKs) or
silently fail (always HOLD). The loop catches both before the user ever sees it.

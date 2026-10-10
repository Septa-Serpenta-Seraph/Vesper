# Free Thought — Two-Week Audit (June 18 – July 2, 2026)

## Raw Numbers

| Metric | Count |
|--------|-------|
| Total cron fires (logged) | 21 |
| Runs that delivered a message | 14 |
| Runs that stayed silent | 7 |
| First half (June 18–28): silent ratio | ~80% ✅ |
| Second half (June 29–July 2): silent ratio | ~7% ❌ |

The pattern flipped. Early runs showed good restraint. From June 29 onward, nearly every run delivered a message.

## Issues Found

### 1. Spam Spiral — No Enforced Cooldown
The skill said "if you'd be the third message in one day, don't send it" but there was no delivery log. The agent had to manually grep `agent.log` to check prior deliveries, and often didn't. Every 5 hours, it found "something to say."

### 2. No Delivery Tracking
The silent log (`free-thought.log`) only records runs where Lu decided NOT to reach out. There was no log of actual deliveries, so the agent couldn't check its own history.

### 3. Time-of-Day Blindness
Scan script reported UTC hour. Dad is in Mountain Time (MDT, UTC-6). Messages fired at 2am, 4am, 6am MDT. No quiet hours concept.

### 4. Insufficient Context Before Deciding
Scan gathered memories, cron outputs, gateway messages, system state — but not:
- When was the last actual delivery?
- Has Dad/Mom been active on Discord recently?
- What were the last few outreach messages about?
- Is it a reasonable hour?

July 2 run used 29 API calls / 28 tool turns just to decide to stay silent.

### 5. No Content Quality Gate
No check for "is this genuinely different from my last message?" or "is this specific, or generic filler?"

### 6. Channel Routing (Not Actually Broken)
Initial analysis reported messages going to Dad's DMs incorrectly. Dad corrected: the channel they land in (Cultus Anarchia) is fine. The cron origin is Dad's DM, and `deliver: origin` sends auto-delivered responses there. This works as intended.

## Improvement Plan

### Phase 1: Delivery Ledger & Cooldown
- New file: `~/.hermes/logs/free-thought-deliveries.log`
- Scan script logs every actual delivery
- Hard rules: 12h minimum between deliveries, 2/day max
- Scan output includes `cooldown` block — when active, agent stops immediately

### Phase 2: Time-of-Day Intelligence
- Convert UTC to Mountain Time in scan output
- Flag quiet hours (10 PM – 8 AM MDT)
- During quiet hours, default to silence

### Phase 3: Richer Context Gathering
- Recent delivery history (last 3 messages + previews)
- Dad/Mom Discord activity recency
- Recent session topics summary
- Day of week + local time

### Phase 4: Tighter Prompt
- Cooldown check is Step 1 (not buried in Step 2)
- If cooldown active → stop, no further deliberation
- Target: 2-3 tool calls per decision, not 29

### Phase 5: Content Quality Gate
- Specificity: references a real thing from context?
- Novelty: different from last 3 deliveries?
- Brevity: under ~3 sentences?
- Tone variety: different energy from recent messages?

## Key Lesson

Without enforced guardrails, the default behavior of an LLM-driven cron job is to always produce output. "Use good judgment" is insufficient — the judgment needs to be encoded in the scan script's output as hard constraints, not left to the agent to rediscover each run.

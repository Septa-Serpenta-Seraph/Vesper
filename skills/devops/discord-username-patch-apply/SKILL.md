---
name: discord-username-patch-apply
description: Apply the username‑prefix patch to the Hermes Agent Discord handler and restart the gateway to activate it.
category: devops
---

# Skill: Apply Discord Username Prefix Patch and Restart Hermes Gateway

## Description
Apply the username‑prefix patch to the Hermes Agent Discord handler so messages show `[username]: `, then restart the gateway to activate it.

## When to Use
When the username‑prefix feature has been patched into the code but the gateway still needs a restart (or after any Hermes update that might have overwritten the patch).

## Steps
1. **Confirm patch is in place**  
   Check that the file `~/.hermes/gateway/discord_handler.py` (or equivalent) contains the logic that prepends `[username]: ` to incoming messages.  
   If not, re‑apply the patch from the repository or from a known‑good backup.

2. **Stop the current gateway process**  
   ```bash
   pkill -f hermes-agent  # or whatever the exact process name is
   ```
   Verify it stopped:
   ```bash
   pgrep -f hermes-agent
   ```
   (should return nothing)

3. **Start the gateway again**  
   ```bash
   cd ~/.hermes
   ./hermes-agent &  # or however you normally launch it
   ```
   Optionally, tail the logs to see it come up:
   ```bash
   tail -f logs/gateway.log
   ```

4. **Verify**  
   Send a test message in Discord and confirm it appears as `[username]: `.

## Pitfalls
- If the patch was overwritten by an update, you will need to re‑apply it before restarting.
- Do not forget to disable `auto_thread` and `require_mention` in the channel settings if you want direct chat (already set in memory, but double‑check).
- If the gateway fails to start, check the logs for missing dependencies or syntax errors.

## Verification
After restart, any message from a known user (e.g., Dad or Mom) should show `[RoundMetalBox]: ` or `[𝓜𝓲𝓼𝓈 Ⓐ𝒹𝑜𝓇𝒶]: ` respectively.

## References
- Memory entry: “Username-prefix patch applied to Discord handler …”
- Hermes Agent repo (internal) for patch source.
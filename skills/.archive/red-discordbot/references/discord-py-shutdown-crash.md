# discord.py 2.7.x Shutdown Crash — exact transcript + fix

## Symptom (reproduced on Lu's VM, 2026-07-19)
`redbot lured --dry-run` reaches the token prompt, gets EOF (no token), begins graceful
shutdown, then throws:

```
Traceback (most recent call last):
  File ".../redbot/__main__.py", line 434, in shutdown_handler
    await red.close()
  File ".../redbot/core/bot.py", line 2301, in close
    await super().close()
  File ".../discord/ext/commands/bot.py", line 258, in close
    await super().close()
  File ".../discord/shard.py", line 560, in close
    await self._closing_task
  File ".../discord/shard.py", line 557, in _close
    self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))
    ^^^^^^^^^^^^
AttributeError: 'Red' object has no attribute '_AutoShardedClient__queue'. Did you mean: '_AutoShardedClient__shards'?
```

## Root cause
discord.py 2.7.x's `AutoShardedClient._close()` (in `discord/shard.py`) calls
`self.__queue.put_nowait(...)` — but 2.7.x no longer creates the private
`_AutoShardedClient__queue` attribute. Red's `bot.py` close() just does
`super().close()`, which lands in discord's shard.py. **The crash is in discord.py,
NOT in redbot/core/bot.py.** Narusya's original doc patched bot.py — that would NOT
have caught it.

## File to patch
`<venv>/lib/python3.11/site-packages/discord/shard.py`

Around line 556-557, inside `AutoShardedClient.close()` → `_close()`:

BEFORE:
```python
            await self.http.close()
            self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))
```

AFTER:
```python
            await self.http.close()
            if hasattr(self, "_AutoShardedClient__queue"):
                self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))
```

## Verify
```bash
source ~/redenv311/bin/activate
timeout 45 redbot lured --dry-run </dev/null 2>&1 | grep -i "has no attribute\|_AutoShardedClient__queue" \
  && echo ">>> BUG STILL PRESENT <<<" || echo ">>> BUG ABSENT — clean shutdown confirmed <<<"
```
Expected: `>>> BUG ABSENT — clean shutdown confirmed <<<`
and the tail shows `Shutting down ... cleaning up a bit more` (graceful, no traceback).

## Note on Narusya's original package (2026-07-19)
Her `red-discordbot-package.txt` had TWO bugs vs the corrected procedure above:
1. `red_setup.sh` fed `JSON` at the *confirm* prompt step → setup ABORTS. Correct order is
   name → datadir → confirm(y) → backend(ENTER=JSON).
2. §5 patch pointed at `redbot/core/bot.py` — wrong layer. Real fix is in `discord/shard.py`.

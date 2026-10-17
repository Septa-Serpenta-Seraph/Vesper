---
name: hermes-rebase-with-patches
description: Update Hermes Agent from upstream while preserving local custom patches (username prefixing and compression config)
category: devops
---

# Hermes Agent Rebase with Local Patches Preservation

## Overview

All 4 sibling skills (`hermes-git-rebase-update`, `hermes-manual-rebase-update`, `hermes-patch-update-workflow`) have been consolidated into this umbrella skill. Update Hermes Agent from upstream while preserving critical local custom patches (username prefixing in group chats and compression configuration fixes).

## Prerequisites
- Git repository cloned from https://github.com/your-username/hermes-agent
- Local customizations in `gateway/run.py` and `run_agent.py`
- Upstream remote configured as `origin`

## When to Use
- User asks to update Hermes Agent
- `git status` shows local branch is behind `origin/main`
- Local patches exist (username prefix, compression config)
- `git log --oneline -n 20` shows significant divergence

## Quick Check First
```bash
# Check how far behind we are
git rev-list --count HEAD..origin/main
# > 0 means we're behind — proceed
```

## Steps

### 1. Fetch Latest Changes
```bash
git fetch origin
```

### 2. Check Current Status and Divergence
```bash
git status
git log --oneline --decorate --graph --all
# Note the number of commits diverged from origin/main
```

### 3. Start Interactive Rebase (if needed for complex history)
```bash
# For straightforward rebases:
git rebase origin/main

# For complex histories with conflicts, consider:
git rebase -i origin/main
```

### 4. Handle Merge Conflicts
When conflicts occur in customized files:
1. Identify conflicted files (typically `gateway/run.py` and `run_agent.py`)
2. For each conflicted file:
   ```bash
   # Check what changed upstream vs locally
   git show :1:filename > /tmp/base   # Original
   git show :2:filename > /tmp/ours   # Local (OURS)
   git show :3:filename > /tmp/theirs # Upstream (THEIRS)
   
   # Manually merge: take upstream changes and reapply local patches
   # Local patches to preserve:
   # - Username prefixing: [username] in group chats
   # - Compression config: attempts via env var
   
   # Edit the file to incorporate both upstream improvements and local patches
   vim filename
   
   # Mark as resolved
   git add filename
   ```

### 5. Verify Local Patches Are Preserved
After resolving conflicts:
```bash
# Check username prefixing still exists
grep -n "\[username\]" gateway/run.py run_agent.py

# Check compression config still exists
grep -n "COMPRESSION_ATTEMPTS\|compression_attempts" gateway/run.py run_agent.py
```

### 6. Continue Rebase
```bash
git rebase --continue
# Repeat conflict resolution as needed until rebase completes
```

### 7. Verify Final State
```bash
# Ensure we're ahead of origin/main with our patches
git log --oneline origin/main..HEAD

# Test that the agent still starts correctly
python -m gateway.run --help  # or equivalent
```

### 8. Push Updated Fork (if applicable)
```bash
git push origin HEAD:main --force-with-lease
```

## Common Local Patches to Preserve
1. **Username Prefixing in Group Chats** (around line where msg.author is processed)
   - Adds `[username]` prefix to distinguish speakers in group contexts
   - Applied to both incoming message processing and transcript logging

2. **Compression Configuration** 
   - Makes compression attempts configurable via environment variable
   - Defaults to sensible value but allows override

## Pitfalls & Troubleshooting
- **Pitfall**: Blindly accepting upstream changes removes local functionality
  - **Solution**: Always verify patches remain after conflict resolution. Check `git diff origin/main` after rebase.
  
- **Pitfall**: Merge conflicts in initialization/configuration code
  - **Solution**: Carefully compare intent - upstream may have improved structure that accommodates patches better
  
- **Pitfall**: Stuck in rebase with confusing state
  - **Solution**: `git rebase --abort` to start over, then reconsider approach

- **Pitfall**: Empty commits during rebase (patch already merged upstream)
  - **Solution**: `git rebase --skip` ONLY if the change is redundant. Don't skip if it's a patch you need to re-apply.

- **Pitfall**: Leftover merge markers (`<<<<<<<`, `=======`, `>>>>>>>`) in Python scripts
  - **Solution**: After resolving, grep for any remaining markers: `grep -rnE '<<<<<<<|=======|>>>>>>>' gateway/ run_agent.py`. Use `python3 -c` for programmatic fixes if `sed` is too blunt.

- **Pitfall**: Author type mismatch (discord.Member vs discord.User) after upstream restructured gateway/run.py
  - **Solution**: Ensure the username-prefix handler matches the new author type. Check `type(msg.author).__name__` in the rebased code before re-inserting the prefix.

- **Pitfall**: Forgetting to re-apply compression patches if they were completely stomped
  - **Solution**: After rebase, verify `grep -n "os.getenv\|compression_attempts\|COMPRESSION_ATTEMPTS" run_agent.py` shows the env-var-configurable pattern, not just a hardcoded value.

## Verification
After successful rebase:
1. Check `git log` to ensure local commits are now on top of `origin/main`
2. **Username prefixing**: `grep -n "\\[username\\]" gateway/run.py run_agent.py` — should show the prefix logic present
3. **Compression config**: `grep -n "COMPRESSION_ATTEMPTS\\|compression_attempts" run_agent.py` — env-var fallback preserved
4. Agent starts without errors: `python -m gateway.run --help` (or equivalent)
5. New upstream features are present (reply context, @ expansion, etc.)
6. No `<<<<<<<` markers remain: `grep -rnE '<<<<<<<|=======|>>>>>>>' gateway/run.py run_agent.py`

## Estimated Time
15-30 minutes depending on divergence and conflict complexity
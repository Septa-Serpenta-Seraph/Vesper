---
name: hermes-compression-fix
category: software-development
tags: [hermes, compression, git, maintenance]
description: Re-apply compression patches after hermes update overwrites local changes.
triggers: ["after hermes update", "compression errors", "context length exceeded", "cannot compress further"]
---

# Hermes Compression Fix

Re-apply compression patches after `hermes update` overwrites local changes.

## Why This Exists

Hermes updates via `git pull --rebase origin/main` which resets `run_agent.py` to upstream. Our local patch (raised compression attempts) gets lost. This skill documents how to re-apply it.

## Patches

### 1. run_agent.py — max_compression_attempts

**What:** Raises default compression attempts from 3 → 10, configurable via env var.

**Location:** `hermes-agent/run_agent.py`, around line 3531

**Find:**
```python
max_compression_attempts = 3
```

**Replace with:**
```python
max_compression_attempts = int(os.getenv("MAX_COMPRESSION_ATTEMPTS", "10"))
```

### 2. config.yaml — compression threshold

**What:** Lowers compression trigger from 85% → 60% of context limit.

**Location:** `~/.hermes/config.yaml`

**Should be:**
```yaml
compression:
  enabled: true
  threshold: 0.6
  summary_model: google/gemini-3-flash-preview
```

**Note:** This file is NOT overwritten by `hermes update` (lives in `~/.hermes/`, not in the git repo). Only check if it's been accidentally changed.

## Verification

```bash
cd hermes-agent
grep "MAX_COMPRESSION_ATTEMPTS" run_agent.py
grep -A2 "compression:" ~/.hermes/config.yaml
```

## Context

- Applied: March 11, 2026
- Issue: Context length exceeded errors (149K+ tokens), compression failing after only 3 attempts
- Related: Nar also disabled compression entirely on their instance (Hunter Alpha 1M context makes it unnecessary)

# Diagnose vision_analyze 404 — copy-paste recipe

Run from the agent's terminal. Paths are the real ones from the 2026-07-22 incident.

## 1. Is the image file actually valid?
```bash
# exists + size
ls -la /home/lumi/.hermes/cache/images/<file>.jpeg
# PIL validity + dimensions
python3 - <<'PY'
from PIL import Image
p="/home/lumi/.hermes/cache/images/<file>.jpeg"
im=Image.open(p)
print("format:",im.format,"size:",im.size,"is_animated:",getattr(im,'is_animated',False))
PY
```
If this prints a real format+size, the IMAGE IS FINE — the failure is the vision backend.

## 2. What does auxiliary.vision point at?
`config.yaml` → `auxiliary.vision:` (around line 173-180 in the incident).
Look for: `provider: openrouter`, `api_key: ''`, stale model name.

## 3. Is the active chat model text-only?
If `model.provider` model (e.g. tencent/hy3:free) is text-only, vision_analyze
falls back to auxiliary.vision. Dead auxiliary ⇒ 404.

## 4. Provider reachability (mask key, don't print it)
```bash
KEY=$(grep "^OPENROUTER_API_KEY" /home/lumi/.hermes/.env | sed -E 's/.*=//')
curl -s -m 10 -H "Authorization: Bearer $KEY" https://openrouter.ai/api/v1/models \
  -o /dev/null -w "HTTP %{http_code}\n"
# 200 = reachable but may still have no credits; 401/403 = key/credit dead
```

## What the 2026-07-22 incident actually was
- Image: valid 1440x3168 JPEG screenshot, downloaded fine.
- vision_analyze 404'd on BOTH the expired CDN link and the local cache path.
- Root cause: auxiliary.vision was `provider: openrouter, model: google/gemini-3.5-flash, api_key: ''` and OpenRouter had NO credits.
- The text-only active model had no other vision path. Fix deferred: user has no credits;
  future plan = self-host tiny VLM (Moondream2/SmolVLM q4) on VM via auxiliary.vision.base_url.

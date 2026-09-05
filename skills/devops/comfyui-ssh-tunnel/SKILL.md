---
name: comfyui-ssh-tunnel
description: 'Generate ComfyUI images on remote Windows via SSH tunnel.'
---

# ComfyUI via SSH Reverse Tunnel

Trigger: User wants to generate images using ComfyUI on a remote Windows machine accessible through a reverse SSH tunnel.

## Prerequisites

- SSH key at `~/.ssh/windows_desktop`
- Reverse tunnel established from Windows: `ssh -R <listen_port>:127.0.0.1:22 lumi@<linux_vm_ip>`
  - Typical port: `1237` (Linux side) → `22` (Windows side)
  - User must run OpenSSH SSH Server on Windows (services.msc or `Start-Service sshd`)
  - Full tunnel command: `ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1237:127.0.0.1:22 lumi@<VM_TAILSCALE_IP>`
- ComfyUI running on Windows at `127.0.0.1:8188`

## Step 1: Verify the tunnel

```bash
for port in 1235 1236 1237 1238 1239; do
    (timeout 3 bash -c "echo test | ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=3 -p \$port tyler@127.0.0.1 cmd /c \"echo ok\"" 2>&1) && echo "PORT \$port WORKS!"
done
```

If none work, ask the user to re-establish the tunnel.

## Launching ComfyUI (critical — only one method works)

ComfyUI at `C:\ComfyUI\main.py` via `C:\Python311\python.exe`.

**✅ WORKS — wmic process call create (survives SSH disconnect):**
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
```
Returns `ProcessId = N; ReturnValue = 0` on success.

**❌ Does NOT work via SSH (child process killed on disconnect):**
- `cmd /c "start /B /MIN C:\Python311\python.exe ..."` — dies with SSH session
- `PowerShell Start-Process -NoNewWindow ...` — dies with SSH session

## Step 2: Prepare the workflow JSON

Create a file at `/tmp/comfy_prompt.json`:

```json
{
  "prompt": {
    "3": {"inputs": {"seed": 12345, "steps": 30, "cfg": 7, "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
    "4": {"inputs": {"ckpt_name": "juggernautXL_ragnarok.safetensors"}, "class_type": "CheckpointLoaderSimple"},
    "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"text": "POSITIVE_PROMPT", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "NEGATIVE_PROMPT", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
    "9": {"inputs": {"images": ["8", 0], "filename_prefix": "PREFIX"}, "class_type": "SaveImage"}
  }
}
```

## Step 3: Transfer to Windows

```bash
scp -P <PORT> -i ~/.ssh/windows_desktop /tmp/comfy_prompt.json tyler@127.0.0.1:/C:/ComfyUI/comfy_prompt.json
```

## Step 4: Send to ComfyUI API

```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\\ComfyUI\\comfy_prompt.json"
```

Save the `prompt_id` from the response.

## Step 5: Wait for generation

```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "ping -n 30 127.0.0.1 > nul & curl -s http://127.0.0.1:8188/history/<PROMPT_ID>"
```

## Step 6: Retrieve the result

```bash
scp -P <PORT> -i ~/.ssh/windows_desktop tyler@127.0.0.1:/C:/ComfyUI/output/<FILENAME>.png /home/lumi/.hermes/profiles/vesper/cache/images/<NAME>.png
```

## Step 7: Deliver to user (Discord / current channel)

After retrieval, the image is automatically sent to the current conversation by including the path as a media reference:

```
MEDIA:/home/lumi/.hermes/profiles/vesper/cache/images/<NAME>.png
```

This delivers the image as an attachment in Discord (or whatever platform the user is on). No additional steps needed — the image arrives in the chat alongside the response.

### Cache structure
Images live under `/home/lumi/.hermes/profiles/vesper/cache/images/` with descriptive subdirectories for each batch or project (e.g. `vesper_ref_batch1/`).

## Models

- **Juggernaut XL Ragnarok**: `juggernautXL_ragnarok.safetensors` — photorealistic, explicit-friendly (best for tasteful nudes/explicit)
- **DreamShaper XL**: `dreamshaperXL_v10.safetensors` — fantasy/artistic, more conservative
- **Pony Diffusion XL v6**: `ponyDiffusionXLV6.safetensors` — anime/pony style, explicit-friendly

## Updating ComfyUI (needed for new native nodes like MiniMax H3)

Docs often require a newer ComfyUI than installed (H3 needs 0.30.0+). Update procedure:

```bash
# 1. Save any local patch first! (ComfyUI ships with a tqdm Errno 22 logger fix applied)
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "git -C C:\ComfyUI diff app/logger.py > C:\logger_patch.diff"

# 2. Kill ComfyUI, discard local mods, pull (branch is master, NOT main!)
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "taskkill /F /IM python.exe & git -C C:\ComfyUI checkout -- app/logger.py & git -C C:\ComfyUI pull origin master"

# 3. Reapply the logger patch (try/except flush guard)
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "git -C C:\ComfyUI apply C:\logger_patch.diff"

# 4. CRITICAL: bump Python packages to required versions (git pull does NOT do this!)
#    Check system_stats for required vs installed; then:
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c \
  "C:\Python311\python.exe -m pip install --upgrade comfy-kitchen comfyui-frontend-package comfyui-workflow-templates comfyui-embedded-docs comfy-aimdo"

# 5. Restart ComfyUI (wmic method), verify /system_stats shows all versions matching
```

### Pitfall: stale comfy-kitchen → `TensorWiseINT8Layout has no attribute 'dequantize_embedding'`
After a git update, the Python packages lag behind. The nvfp4_awq MiniMax text encoder fails with this AttributeError until `comfy-kitchen` is upgraded to the version required by system_stats. Symptom: node error in `comfy/ops.py` line ~1630 `dequantize_embedding`. Fix = step 4 above. Always diff `installed` vs `required` in `/system_stats` after updating.

### Pitfall: `cd` does not stick over SSH cmd /c
`cmd /c "cd C:\path && command"` often runs `command` from the home dir (e.g. git clones land in C:\Users\Tyler). Fix: always use full paths or `git -C C:\path` instead of cd+git.

## Troubleshooting

### Logger crash (tqdm Errno 22)
If generation fails with `OSError: [Errno 22] Invalid argument` in `logger.py`:
- SSH in and run: `C:\Python311\python.exe C:\ComfyUI\patch_logger.py`
- Restart ComfyUI

### Restart ComfyUI
```bash
# Kill existing ComfyUI
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "taskkill /F /IM python.exe"
# Launch detached via WMIC (the only method that survives SSH disconnect)
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "wmic process call create \"C:\Python311\python.exe C:\ComfyUI\main.py --listen --port 8188\""
```
Wait 20+ seconds for model loading.

### Check if ready
```bash
ssh -i ~/.ssh/windows_desktop -p <PORT> tyler@127.0.0.1 cmd /c "curl -s http://127.0.0.1:8188/system_stats"
```
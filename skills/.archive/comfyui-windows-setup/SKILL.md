---
name: comfyui-windows-setup
description: ComfyUI on fresh Windows for local image gen with CUDA.
---

# ComfyUI Windows Setup

Install ComfyUI from scratch on a fresh Windows 11 install, ready for uncensored local image generation with a GPU (NVIDIA RTX 5070 Ti or similar).

> **Reference file:** See `references/blackwell-gpu-compatibility.md` for detailed RTX 50-series / Blackwell CUDA troubleshooting.

## Installation Steps

### 1. Install Python (not 3.14!)

Fresh Windows 11 ships with Python 3.14 from the Microsoft Store, but **PyTorch with CUDA does not have wheels for Python 3.14**. Install Python 3.10 or 3.11:

```powershell
curl -L -o C:\python-3.11-amd64.exe https://www.python.org/ftp/python/3.11.11/python-3.11.11-amd64.exe
C:\python-3.11-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python311
```

### 2. Install Visual C++ Redistributable

Fresh Windows does not have this — PyTorch DLLs will fail without it:

```powershell
curl -L -o C:\vc_redist.x64.exe https://aka.ms/vs/17/release/vc_redist.x64.exe
C:\vc_redist.x64.exe /install /quiet /norestart
```

### 3. Install ComfyUI

```powershell
cd C:\
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install PyTorch with CUDA

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**⚠️ RTX 5000 series (Blackwell, sm_120) GPUs — special handling:**

PyTorch 2.6+cu124 does NOT support Blackwell architecture (RTX 5070 Ti, sm_120). You'll see:
```
NVIDIA GeForce RTX 5070 Ti with CUDA capability sm_120 is not compatible
with the current PyTorch installation. The current PyTorch install supports
CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.
```

**Fix — install nightly PyTorch with CUDA 12.8+:**

```powershell
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall
```

The `--force-reinstall` is required because the stable version already installed will short-circuit the nightly install without it.

**Verify CUDA works:**
```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 5. Download Models

Models go in `C:\ComfyUI\models\checkpoints\`.

**SDXL (good anatomy, quality):**
```powershell
curl -L -o C:\ComfyUI\models\checkpoints\dreamshaperXL_v10.safetensors https://civitai.com/api/download/models/126688
```

**VAE (better colors):**
```powershell
curl -L -o C:\ComfyUI\models\vae\sdxl_vae.safetensors https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl_vae.safetensors
```

**Note:** Hugging Face models may require authentication for gated models. CivitAI models are open. If a Hugging Face download returns a tiny file (15-29 bytes), the model is gated — find an alternative.

### 6. Run ComfyUI

```powershell
python C:\ComfyUI\main.py --listen
```

Access at `http://127.0.0.1:8188`.

## SSH Pitfalls

When running ComfyUI over SSH (`cmd /c` context):

- **`cd` does not work** in `cmd /c "cd path && command"` over SSH. Always use **full paths**:
  ```powershell
  python C:\ComfyUI\main.py --listen
  ```
  Not: `cd /d C:\ComfyUI && python main.py`

- **Background process**: Start with `background=true` for server processes; check logs with `process(action='poll')` / `process(action='log')`.

## Fresh Windows Dependencies

| Dependency | Why | Check Command |
|---|---|---|
| VC++ Redistributable | PyTorch DLLs (`c10.dll`, etc.) | `nvidia-smi` works ✅ |
| NVIDIA Driver | CUDA GPU support | `nvidia-smi` shows GPU |
| Python 3.10/3.11 | PyTorch CUDA wheels | `python --version` |
| Git | Clone ComfyUI | `git --version` |

## Troubleshooting

### `CUDA capability sm_120 is not compatible` (RTX 5070 Ti / Blackwell)\n- PyTorch 2.6 stable does not support Blackwell architecture\n- Fix: `pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall`\n- Verify: `python -c \"import torch; print(torch.cuda.get_device_capability())\"` should show `(12, 0)`\n\n### `Torch not compiled with CUDA enabled`
- You installed the CPU-only torch (default on Windows Python 3.14+)
- Fix: install Python 3.11, `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`

### `OSError: [WinError 126] c10.dll or dependencies not found`
- Missing VC++ Redistributable
- Fix: download and install from https://aka.ms/vs/17/release/vc_redist.x64.exe

### `Checkpoint file is 15-29 bytes`
- The model URL is gated or wrong — find the correct model version ID from CivitAI or a Hugging Face mirror

### Model recommendations for good anatomy
- **DreamShaper XL** — excellent for fantasy/artistic, handles anatomy well, open model. Resists corvid hybrid features (humanizes beaks, interprets wings as accessories). Keeps nudes tasteful but often clothed/conservative.
- **Juggernaut XL Ragnarok** — BEST for explicit/uncensored content. Photorealistic anatomy, flawless hands, handles corvid wings as actual body parts. DOES NOT do beaks (SDXL limitation). **Pitfall:** spread-leg poses cause "two heads" glitch (V-shape of legs interpreted as neck+face). Use sitting/kneeling or side-lying poses instead.
- **Pony Diffusion XL** — great anatomy but gated (needs Hugging Face login)
- **RealVisXL** — photorealistic, good for human subjects

### Model comparison: what to use when

| Need | Model | Why |
|------|-------|-----|
| Elegant fantasy portrait | DreamShaper XL | Gorgeous lighting, artistic |
| Full explicit nude | Juggernaut XL Ragnarok | Best anatomy, no filter |
| Corvid hybrid (wings, feathers) | Juggernaut XL Ragnarok | Wings as actual body parts |
| Corvid hybrid WITH beak | FLUX via Together.ai | SDXL cannot do beaks |
| Fast test iterations | Any SDXL model | ~7s on 5070 Ti |
| Best quality | Juggernaut XL Ragnarok | Photorealistic, detailed |

### Sending prompts via SSH tunnel (preferred method)

When ComfyUI runs on a remote Windows machine accessed through a reverse SSH tunnel, this is the most reliable method for complex prompts:

```bash
# 1. Save the JSON prompt to a file on the Linux VM
cat > /tmp/comfy_prompt.json << 'EOF'
{
  "prompt": {
    "3": {"inputs": {"seed": 12345, "steps": 30, "cfg": 7, "sampler_name": "euler", "scheduler": "sgm_uniform", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
    "4": {"inputs": {"ckpt_name": "juggernautXL_ragnarok.safetensors"}, "class_type": "CheckpointLoaderSimple"},
    "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
    "6": {"inputs": {"text": "your prompt here", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "negative prompt", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
    "9": {"inputs": {"images": ["8", 0], "filename_prefix": "output"}, "class_type": "SaveImage"}
  }
}
EOF

# 2. SCP the JSON file to Windows
scp -P 1237 -i ~/.ssh/windows_desktop /tmp/comfy_prompt.json tyler@127.0.0.1:/C:/ComfyUI/comfy_prompt.json

# 3. POST it via curl on the Windows side
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
  "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\\ComfyUI\\comfy_prompt.json"
```

**⚠️ Why this works:** The `@filename` syntax tells curl to read the JSON from a file, bypassing all shell escaping issues. This is far more reliable than inline JSON in `cmd /c` context.

**⚠️ Fallback (if SCP is unavailable):** base64-encode the JSON, pipe it through SSH to PowerShell to decode, then POST:

```bash
b64=$(base64 -w0 /tmp/comfy_prompt.json)
echo "$b64" | ssh -p 1237 user@127.0.0.1 powershell -Command \
  "$b = Read-Host; [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b)) | Set-Content C:\prompt.json"
ssh -p 1237 user@127.0.0.1 cmd /c "curl -s -X POST http://127.0.0.1:8188/prompt -H \"Content-Type: application/json\" -d @C:\\prompt.json"
```

### Checking generation status

Poll for completion (wait ~7-10s for SDXL on RTX 5070 Ti):

```bash
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c \
  "ping -n 25 127.0.0.1 > nul & curl -s http://127.0.0.1:8188/history/<prompt_id>"
```

Check for `"status_str": "success"` in the response. If it shows `"completed": false` with error, read the `exception_message` field.

### Copying output to Linux

```bash
scp -P 1237 -i ~/.ssh/windows_desktop tyler@127.0.0.1:/C:/ComfyUI/output/<filename>.png /local/path.png
```

### SSH tunnel management

The tunnel is a reverse SSH tunnel established FROM the Windows machine TO the Linux VM:

```powershell
# On Windows PowerShell:
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R 1237:127.0.0.1:22 lumi@<VM_TAILSCALE_IP>
```

This maps: `Linux:1237 → Windows:22` (SSH server). Connect from Linux:

```bash
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "echo tunnel is alive"
```

**Tunnel troubleshooting:**

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Connection timed out during banner exchange` | Port open but SSH server not responding | Check `Get-Service sshd` on Windows; restart with `Start-Service sshd` |
| `Connection refused` | Port not open/listening | User needs to re-establish the tunnel from Windows |
| Permission denied (publickey) | Key mismatch | Use `-i ~/.ssh/windows_desktop` to specify the correct key |
| `remote port forwarding failed for listen port X` | Port already in use on Linux VM | Kill the stale process: `fuser -k X/tcp` or try a different port |

**Port conflict resolution:** If the tunnel port is stuck (e.g. from a previous failed SSH attempt), check and free it:

```bash
ss -tlnp 'sport = :1237'     # Check what's listening
fuser -k 1237/tcp            # Kill the process holding the port
```

**Tunnel keepalive:** Always use `-o ServerAliveInterval=30 -o ServerAliveCountMax=3` to prevent long-running tunnels from dropping.

### ComfyUI logger crash fix

If generation fails with `OSError: [Errno 22] Invalid argument` and the traceback shows:

```
File "C:\ComfyUI\app\logger.py", line 69, in flush
    super().flush()
```

This is a tqdm progress bar compatibility issue with the ComfyUI logger (common with nightly PyTorch builds on Windows). The `LogInterceptor.flush()` calls `super().flush()` on the underlying `TextIOWrapper`, which can fail with `Errno 22` on certain Python builds.

**Temp fix:** Restart ComfyUI (close and re-launch). This clears the logger state but the issue returns.

**Permanent fix — patch logger.py:** Add a try/except around the `super().flush()` call:

```python
# Save as C:\ComfyUI\patch_logger.py and run once:
with open(r'C:\ComfyUI\app\logger.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '    def flush(self):\n        super().flush()\n        for cb in self._flush_callbacks:'
new = '    def flush(self):\n        try:\n            super().flush()\n        except Exception:\n            pass\n        for cb in self._flush_callbacks:'
content = content.replace(old, new)
with open(r'C:\ComfyUI\app\logger.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched OK!")
```

Run once:
```powershell
python C:\ComfyUI\patch_logger.py
```

After patching, restart ComfyUI. The fix survives ComfyUI updates as long as `logger.py` isn't overwritten. If an update replaces the file, re-apply the patch.

**SSH tunnel alternative:** If the tunnel is up, you can run the patch script directly:
```bash
scp -P 1237 -i ~/.ssh/windows_desktop patch_logger.py tyler@127.0.0.1:/C:/ComfyUI/patch_logger.py
ssh -i ~/.ssh/windows_desktop -p 1237 tyler@127.0.0.1 cmd /c "python C:\ComfyUI\patch_logger.py"
```
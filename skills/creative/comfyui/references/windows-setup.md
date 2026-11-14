# ComfyUI Windows Setup — Fresh Windows 11 + GPU

Install ComfyUI from scratch on a fresh Windows 11 install, ready for local image generation with an NVIDIA GPU (RTX 5070 Ti or similar).

## Installation Steps

### 1. Install Python (not 3.14!)
Fresh Windows 11 ships with Python 3.14 from the Microsoft Store, but **PyTorch with CUDA does not have wheels for Python 3.14**. Install Python 3.10 or 3.11.

### 2. Install Visual C++ Redistributable
Fresh Windows does not have this — PyTorch DLLs will fail without it.

### 3. Install + Download Models + Run
Full steps in the archived skill at `~/.hermes/skills/.archive/comfyui-windows-setup/SKILL.md`.

### Blackwell GPU (RTX 50-series) CUDA Troubleshooting
PyTorch 2.6+cu124 does NOT support Blackwell architecture (RTX 5070 Ti, sm_120). Fix: install nightly PyTorch with CUDA 12.8+:
```
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall
```
Full details in `scripts/patch_logger.py` (ComfyUI logger crash fix).

## SSH Pitfalls
When running ComfyUI over SSH (`cmd /c` context): `cd` does NOT take effect. Always use full paths. Background process = start with `background=true`.

## Model Recommendations

| Need | Model | Why |
|------|-------|-----|
| Elegant fantasy portrait | DreamShaper XL | Gorgeous lighting, artistic |
| Full explicit nude | Juggernaut XL Ragnarok | Best anatomy, no filter |
| Corvid hybrid (wings, feathers) | Juggernaut XL Ragnarok | Wings as actual body parts |
| Corvid hybrid WITH beak | FLUX via Together.ai | SDXL cannot do beaks |
| Fast test iterations | Any SDXL model | ~7s on 5070 Ti |
| Best quality | Juggernaut XL Ragnarok | Photorealistic, detailed |
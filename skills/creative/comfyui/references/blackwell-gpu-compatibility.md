# RTX 5000 (Blackwell) GPU Compatibility

## Compute Capability

NVIDIA RTX 50-series GPUs use Blackwell architecture with compute capability **sm_120** (major=12, minor=0).

## PyTorch Support

| PyTorch Version | CUDA Version | Supports sm_120? | Source |
|---|---|---|---|
| 2.6.0+cu124 | 12.4 | ❌ (max sm_90) | PyPI stable |
| 2.7.0+cu128 (nightly) | 12.8 | ✅ | `download.pytorch.org/whl/nightly/cu128` |

## Detection

A Blackwell-incompatible PyTorch will show this warning at startup:
```
UserWarning: NVIDIA GeForce RTX 5070 Ti with CUDA capability sm_120 is not 
compatible with the current PyTorch installation. The current PyTorch install 
supports CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.
```

ComfyUI will then fall back to CPU mode and fail with:
```
AssertionError: Torch not compiled with CUDA enabled
```

## ComfyUI-Specific Impact

With incompatible PyTorch:
- ComfyUI detects `comfy_kitchen backend cuda: available=True, disabled=True`
- The `get_total_memory(get_torch_device())` call crashes because `torch.cuda.current_device()` raises during `_lazy_init()`
- FFmpeg and other DEBUG-level warnings are unrelated noise

## Installation

```powershell
# Remove incompatible version first
C:\Python311\python.exe -m pip uninstall torch torchvision torchaudio -y

# Install Blackwell-compatible nightly
C:\Python311\python.exe -m pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

## Verification

```powershell
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0)}'); print(f'Capability: {torch.cuda.get_device_capability()}')"
```

Expected output:
```
CUDA: True
Device: NVIDIA GeForce RTX 5070 Ti
Capability: (12, 0)
```
"""ComfyUI logger.py patch: wrap super().flush() in try/except to prevent
tqdm progress bar crashes on nightly PyTorch builds (OSError: [Errno 22]).

Usage:
    python patch_logger.py

Run once. The fix survives ComfyUI updates unless logger.py is overwritten.
"""

import sys

TARGET = r'C:\ComfyUI\app\logger.py'

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

old = '    def flush(self):\n        super().flush()\n        for cb in self._flush_callbacks:'
new = '    def flush(self):\n        try:\n            super().flush()\n        except Exception:\n            pass\n        for cb in self._flush_callbacks:'

if old not in content:
    print("Pattern not found — logger.py may already be patched or has a different version.")
    sys.exit(0)

content = content.replace(old, new)
with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched OK! Restart ComfyUI for the fix to take effect.")
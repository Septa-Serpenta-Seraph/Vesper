#!/usr/bin/env python3
"""gif2sheet.py — turn a GIF into a contact sheet so Vesper can "see" it in full.

Problem: when a GIF arrives in Discord, Hermes only ever sees the FIRST frame.
This script extracts every frame, builds a numbered contact sheet (grid), and
saves individual frames too — so a vision pass can read the whole animation.

Usage:
  gif2sheet.py <path-or-url> [--cols 4] [--max-frames 24] [--outdir DIR]

Outputs:
  <outdir>/sheet.png          — the grid contact sheet (analyze this with vision)
  <outdir>/frames/frame_001.png ... — individual frames (full resolution)

Exit codes:
  0  success (prints the sheet path on stdout)
  2  can't load input
"""
import sys
import os
import argparse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def load_gif(src: str) -> Image.Image:
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            tmp = "/tmp/gif2sheet_input.gif"
            with open(tmp, "wb") as f:
                f.write(r.read())
            return Image.open(tmp)
    return Image.open(src)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--max-frames", type=int, default=24)
    ap.add_argument("--outdir", default="/home/lumi/.hermes/profiles/vesper/cache/gif-frames")
    args = ap.parse_args()

    try:
        im = load_gif(args.src)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    frames = []
    try:
        n = getattr(im, "n_frames", 1)
        # sample evenly if the gif has more frames than max
        total = min(n, args.max_frames)
        if total <= 1:
            idxs = [0]
        else:
            idxs = sorted({round(i * (n - 1) / (total - 1)) for i in range(total)})
        for i in idxs:
            im.seek(i)
            frames.append(im.convert("RGB").copy())
    except Exception as e:
        print(f"ERROR reading frames: {e}", file=sys.stderr)
        return 2

    if not frames:
        print("ERROR: no frames extracted", file=sys.stderr)
        return 2

    os.makedirs(os.path.join(args.outdir, "frames"), exist_ok=True)

    # save individual frames
    for i, fr in enumerate(frames):
        fr.save(os.path.join(args.outdir, "frames", f"frame_{i+1:03d}.png"))

    # build contact sheet
    w, h = frames[0].size
    cols = max(1, min(args.cols, len(frames)))
    rows = (len(frames) + cols - 1) // cols
    pad = 8
    label_h = 18
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + label_h + pad) + pad), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for idx, fr in enumerate(frames):
        r, c = divmod(idx, cols)
        x = pad + c * (w + pad)
        y = pad + r * (h + label_h + pad)
        sheet.paste(fr, (x, y + label_h))
        txt = f"{idx+1}/{len(frames)}"
        if font:
            draw.text((x + 4, y + 2), txt, fill=(255, 255, 255), font=font)
        else:
            draw.text((x + 4, y + 2), txt, fill=(255, 255, 255))

    sheet_path = os.path.join(args.outdir, "sheet.png")
    sheet.save(sheet_path)
    print(sheet_path)
    print(f"frames={len(frames)} dims={w}x{h}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())

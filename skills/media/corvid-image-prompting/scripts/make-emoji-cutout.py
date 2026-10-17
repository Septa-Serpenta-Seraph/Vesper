# -*- coding: utf-8 -*-
"""Cutout post-processing for generated base sprites -> emoji-ready PNGs.

Takes a generated image (e.g. from the perchance driver or ComfyUI) with a
white/near-white background, removes it via edge flood-fill, crops to the
character bounding box, and saves emoji-ready sizes (1024 master, 512, 128).

Usage:
    python3 make-emoji-cutout.py <input_image> <outdir> [name]

Outputs: <outdir>/<name>_1024.png, _512.png, _128.png
Requires: Pillow
"""
import os
import sys
from collections import deque

from PIL import Image


def near_white(p, tol=38):
    return p[0] > 255 - tol and p[1] > 255 - tol and p[2] > 255 - tol


def remove_background(img):
    """Edge flood-fill white removal + near-white fringe cleanup."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    visited = set()
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if (x, y) in visited or not (0 <= x < w and 0 <= y < h):
            continue
        visited.add((x, y))
        if near_white(px[x, y]):
            px[x, y] = (255, 255, 255, 0)
            q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    # Semi-transparent fringe: fully drop remaining near-white opaque pixels
    for x in range(w):
        for y in range(h):
            p = px[x, y]
            if p[3] == 255 and p[0] > 200 and p[1] > 200 and p[2] > 200:
                px[x, y] = (p[0], p[1], p[2], 0)
    return img


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    src, outdir = sys.argv[1], sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "emoji_base"
    os.makedirs(outdir, exist_ok=True)

    img = Image.open(src)
    img = remove_background(img)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    for size in (1024, 512, 128):
        s = img.copy()
        s.thumbnail((size, size), Image.LANCZOS)
        out = os.path.join(outdir, f"{name}_{size}.png")
        s.save(out)
        print(f"saved {out} ({s.size[0]}x{s.size[1]})")


if __name__ == "__main__":
    main()

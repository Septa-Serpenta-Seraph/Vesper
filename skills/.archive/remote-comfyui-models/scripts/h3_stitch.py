#!/usr/bin/env python3
"""Stitch H3 arc segments into one continuous video with crossfades.

Run: python3 h3_stitch.py
Reads cache/video/arc/vesper_arc_*.mp4, outputs vesper_arc_full.mp4.
"""
import glob
import os
import subprocess
import sys

VID_DIR = "/home/lumi/.hermes/profiles/vesper/cache/video/arc"
OUT = os.path.join(VID_DIR, "vesper_arc_full.mp4")
FADE = 0.5  # crossfade duration in seconds


def get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 15.0


def main():
    files = sorted(glob.glob(os.path.join(VID_DIR, "vesper_arc_*.mp4")))
    files = [f for f in files if "full" not in os.path.basename(f)]
    if len(files) < 2:
        print(f"Need at least 2 segments, found {len(files)}", flush=True)
        return 1

    print(f"Stitching {len(files)} segments with {FADE}s crossfades...", flush=True)

    durations = [get_duration(f) for f in files]
    print("Durations:", [f"{d:.1f}s" for d in durations], "total:", f"{sum(durations):.1f}s", flush=True)

    inputs = []
    for f in files:
        inputs += ["-i", f]

    # xfade chain: offset_k = cumulative - k*FADE (overlap)
    filter_parts = []
    prev_label = "0:v"
    cumulative = durations[0]
    for i in range(1, len(files)):
        offset = max(0.0, cumulative - i * FADE)
        out_label = f"v{i}"
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        cumulative += durations[i]
    vfilter = ";".join(filter_parts)

    # audio: acrossfade chain
    aparts = []
    prev_audio = "0:a"
    for i in range(1, len(files)):
        out_label = f"a{i}"
        aparts.append(
            f"[{prev_audio}][{i}:a]acrossfade=d={FADE}:c1=tri:c2=tri[{out_label}]"
        )
        prev_audio = out_label
    afilter = ";".join(aparts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", f"{vfilter};{afilter}",
        "-map", f"[{prev_label}]", "-map", f"[{prev_audio}]",
        "-c:v", "libx264", "-profile:v", "main", "-preset", "medium", "-crf", "13",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        OUT,
    ]
    print("Running ffmpeg...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print("FFMPEG ERROR:", r.stderr[-800:], flush=True)
        return 1

    dur = get_duration(OUT)
    size = os.path.getsize(OUT) / 1e6
    print(f"DONE: {OUT} — {dur:.1f}s, {size:.1f} MB", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Stitch video segments into one continuous video with crossfades.

Usage:
  python3 h3_stitch.py [INPUT_GLOB] [OUTPUT_PATH]
    INPUT_GLOB  e.g. "/home/lumi/.hermes/profiles/vesper/cache/video/vesper_*.mp4" (default: arc segments)
    OUTPUT_PATH e.g. ".../vesper_season_one.mp4" (default: vesper_arc_full.mp4)
Reads matching files (sorted), normalizes all to the first file's res/fps,
crossfades, re-encodes yuv420p for Discord.
"""
import glob
import os
import subprocess
import sys

VID_DIR = "/home/lumi/.hermes/profiles/vesper/cache/video/arc"
OUT = os.path.join(VID_DIR, "vesper_arc_full.mp4")
FADE = 0.5  # crossfade duration: chained first frames drift slightly (H3 first_frame is a strong condition, not a lock) — longer fade masks the seam


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
    pattern = sys.argv[1] if len(sys.argv) > 1 else os.path.join(VID_DIR, "vesper_arc_*.mp4")
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUT
    files = sorted(glob.glob(pattern))
    files = [f for f in files if "full" not in os.path.basename(f)]
    if len(files) < 2:
        print(f"Need at least 2 segments, found {len(files)} for {pattern}", flush=True)
        return 1

    print(f"Stitching {len(files)} segments with {FADE}s crossfades...", flush=True)

    # Build xfade chain. With N inputs and N-1 xfades, offsets must account for
    # the overlap: offset_k = sum(durations up to k) - k * FADE
    durations = [get_duration(f) for f in files]
    print("Durations:", [f"{d:.1f}s" for d in durations], "total:", f"{sum(durations):.1f}s", flush=True)

    inputs = []
    for f in files:
        inputs += ["-i", f]

    # Probe reference resolution/fps from first segment (normalize ALL to it —
    # xfade errors if inputs mismatch)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", files[0]],
        capture_output=True, text=True, timeout=30,
    )
    parts = probe.stdout.strip().split(",")
    try:
        ref_w, ref_h = int(parts[0]), int(parts[1])
        num, den = parts[2].split("/")
        ref_fps = round(int(num) / int(den))
    except Exception:
        ref_w, ref_h, ref_fps = 864, 480, 24

    # Normalization pre-pass: every input → matching res/fps/pixfmt/audio
    norm = []
    for i in range(len(files)):
        norm.append(
            f"[{i}:v]scale={ref_w}:{ref_h},fps={ref_fps},format=yuv420p,setsar=1[nv{i}];"
            f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[na{i}]"
        )
    norm_filter = ";".join(norm)

    # filter: xfade chain over normalized labels
    filter_parts = []
    prev_label = "nv0"
    cumulative = durations[0]
    for i in range(1, len(files)):
        offset = max(0.0, cumulative - i * FADE)
        out_label = f"v{i}"
        filter_parts.append(
            f"[{prev_label}][nv{i}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[{out_label}]"
        )
        prev_label = out_label
        cumulative += durations[i]
    vfilter = ";".join(filter_parts)

    # audio: acrossfade chain over normalized labels
    aparts = []
    prev_audio = "na0"
    for i in range(1, len(files)):
        out_label = f"a{i}"
        aparts.append(
            f"[{prev_audio}][na{i}]acrossfade=d={FADE}:c1=tri:c2=tri[{out_label}]"
        )
        prev_audio = out_label
    afilter = ";".join(aparts)

    full_filter = ";".join(x for x in [norm_filter, vfilter, afilter] if x)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", full_filter,
        "-map", f"[{prev_label}]", "-map", f"[{prev_audio}]",
        "-c:v", "libx264", "-profile:v", "main", "-preset", "medium", "-crf", "13",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        out_path,
    ]
    print("Running ffmpeg...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        print("FFMPEG ERROR:", r.stderr[-800:], flush=True)
        return 1

    dur = get_duration(out_path)
    size = os.path.getsize(out_path) / 1e6
    print(f"DONE: {out_path} — {dur:.1f}s, {size:.1f} MB", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

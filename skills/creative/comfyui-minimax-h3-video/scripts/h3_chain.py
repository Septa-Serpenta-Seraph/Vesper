#!/usr/bin/env python3
"""Chain MiniMax H3 segments: each segment's last frame becomes the next's first_frame.

Usage: python3 h3_chain.py [--start N] [--segments N]
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from h3_arc_segments import SEGMENTS

SSH_KEY = "/home/lumi/.ssh/windows_desktop"
PORT = "1237"
HOST = "tyler@127.0.0.1"
BASE_URL = "http://127.0.0.1:8188"
WIDTH, HEIGHT = 864, 480
FRAMES = 362  # 15s at 24fps, snapped to 17k+5 grid
LOCAL_VID_DIR = "/home/lumi/.hermes/profiles/vesper/cache/video/arc"
LOCAL_FRAME_DIR = "/home/lumi/.hermes/profiles/vesper/cache/video/arc/frames"
PREFIX = "vesper_arc"


def ssh_cmd(cmd: str, timeout=60) -> str:
    r = subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new",
         "-p", PORT, HOST, "cmd", "/c", cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout.strip()


def submit_prompt(wf: dict) -> str:
    payload = {"prompt": wf, "client_id": "vesper-arc"}
    with open("/tmp/h3_arc_payload.json", "w") as f:
        json.dump(payload, f)
    # Upload payload to Windows first
    r = subprocess.run(
        ["scp", "-P", PORT, "-i", SSH_KEY, "/tmp/h3_arc_payload.json",
         f"{HOST}:/C:/ComfyUI/h3_arc_payload.json"],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        print("PAYLOAD UPLOAD FAILED:", r.stderr[-300:], flush=True)
        return ""
    out = ssh_cmd(
        f'curl -s -X POST {BASE_URL}/prompt -H "Content-Type: application/json" -d @C:\\ComfyUI\\h3_arc_payload.json'
    )
    try:
        return json.loads(out)["prompt_id"]
    except Exception:
        print("SUBMIT FAILED:", out, flush=True)
        return ""


def wait_done(prompt_id: str, timeout_s=1800) -> dict | None:
    start = time.time()
    while time.time() - start < timeout_s:
        out = ssh_cmd(f"curl -s {BASE_URL}/history/{prompt_id}")
        try:
            h = json.loads(out)
            if prompt_id in h:
                entry = h[prompt_id]
                st = entry.get("status", {})
                if st.get("completed") or st.get("status_str") == "success":
                    return entry
                if st.get("status_str") == "error":
                    print(f"ERROR in {prompt_id}: {json.dumps(st)[:300]}", flush=True)
                    return None
        except Exception:
            pass
        print(f"[{int(time.time()-start)}s] waiting {prompt_id}...", flush=True)
        time.sleep(30)
    return None


def get_output_filename(entry: dict) -> str:
    try:
        for node_id, out in entry["outputs"].items():
            for img in out.get("images", []):
                if img.get("type") == "output":
                    return img["filename"]
    except Exception:
        pass
    return ""


def download_video(remote_name: str, local_path: str) -> bool:
    r = subprocess.run(
        ["scp", "-P", PORT, "-i", SSH_KEY, f"{HOST}:/C:/ComfyUI/output/{remote_name}", local_path],
        capture_output=True, text=True, timeout=120,
    )
    return os.path.exists(local_path) and os.path.getsize(local_path) > 0


def extract_last_frame(video_path: str, frame_path: str) -> bool:
    # Grab the LITERAL last frame (exact seam continuity, no 0.2s offset drift)
    r = subprocess.run(
        ["ffmpeg", "-y", "-sseof", "-0.01", "-i", video_path, "-frames:v", "1", frame_path],
        capture_output=True, text=True, timeout=60,
    )
    return os.path.exists(frame_path)


def upload_first_frame(frame_path: str) -> str | None:
    r = subprocess.run(
        ["scp", "-P", PORT, "-i", SSH_KEY, frame_path, f"{HOST}:/C:/ComfyUI/input/{os.path.basename(frame_path)}"],
        capture_output=True, text=True, timeout=60,
    )
    return os.path.basename(frame_path) if r.returncode == 0 else None


def build_workflow(segment_idx: int, prompt: str, seed: int, prefix: str, first_frame: str | None = None) -> dict:
    # Same topology as the verified T2V workflow
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "5": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt, "width": WIDTH, "height": HEIGHT, "length": FRAMES}},
        "6": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "7": {"class_type": "BasicScheduler", "inputs": {"model": ["1", 0], "scheduler": "simple", "steps": 20, "denoise": 1}},
        "8": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["5", 0]}},
        "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "10": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["9", 0], "guider": ["8", 0], "sampler": ["6", 0], "sigmas": ["7", 0], "latent_image": ["5", 1]}},
        "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["10", 0], "vae": ["4", 0]}},
        "13": {"class_type": "CreateVideo", "inputs": {"images": ["11", 0], "audio": ["12", 0], "fps": 24, "bit_depth": 8}},
        "14": {"class_type": "SaveVideo", "inputs": {"video": ["13", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    }
    if first_frame:
        # Need a LoadImage node feeding MiniMaxH3ImageToVideo.first_frame
        wf["15"] = {"class_type": "LoadImage", "inputs": {"image": first_frame}}
        wf["5"]["inputs"]["first_frame"] = ["15", 0]
    return wf


def main():
    start_seg = 1
    if "--start" in sys.argv:
        start_seg = int(sys.argv[sys.argv.index("--start") + 1])

    os.makedirs(LOCAL_VID_DIR, exist_ok=True)
    os.makedirs(LOCAL_FRAME_DIR, exist_ok=True)

    # Verify tunnel first
    try:
        probe = ssh_cmd("echo OK", timeout=15)
        if "OK" not in probe:
            print("TUNNEL DOWN — cannot proceed", flush=True)
            return 2
    except Exception as e:
        print(f"TUNNEL DOWN ({e}) — cannot proceed", flush=True)
        return 2

    prev_frame = None
    for i in range(start_seg - 1, len(SEGMENTS)):
        seg_num = i + 1
        prompt = SEGMENTS[i]
        seed = 500000 + seg_num * 1111
        prefix = f"{PREFIX}_{seg_num:02d}"
        local_video = os.path.join(LOCAL_VID_DIR, f"{prefix}.mp4")

        print(f"\n=== Segment {seg_num}/10 — submitting ===", flush=True)
        wf = build_workflow(seg_num, prompt, seed, prefix, first_frame=prev_frame)
        pid = submit_prompt(wf)
        if not pid:
            print(f"SEGMENT {seg_num} SUBMIT FAILED — stopping", flush=True)
            return 1

        entry = wait_done(pid)
        if not entry:
            print(f"SEGMENT {seg_num} FAILED — stopping", flush=True)
            return 1

        remote_name = get_output_filename(entry)
        if not remote_name:
            print(f"SEGMENT {seg_num} no output file — stopping", flush=True)
            return 1

        if download_video(remote_name, local_video):
            print(f"SEGMENT {seg_num} downloaded: {local_video}", flush=True)
        else:
            print(f"SEGMENT {seg_num} download FAILED", flush=True)
            return 1

        # Extract last frame for next segment
        frame_path = os.path.join(LOCAL_FRAME_DIR, f"frame_{seg_num:02d}.png")
        if extract_last_frame(local_video, frame_path):
            up = upload_first_frame(frame_path)
            if up:
                prev_frame = up
                print(f"SEGMENT {seg_num} last frame → next: {up}", flush=True)
            else:
                print(f"SEGMENT {seg_num} frame upload FAILED — next segment will be T2V", flush=True)
                prev_frame = None
        else:
            print(f"SEGMENT {seg_num} frame extract FAILED — next segment will be T2V", flush=True)
            prev_frame = None

    print("\nALL SEGMENTS DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

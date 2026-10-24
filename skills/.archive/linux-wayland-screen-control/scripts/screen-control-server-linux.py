#!/usr/bin/env python3
"""screen-control-server-linux.py — Linux port of the Windows PowerShell screen-control server.

Lets Vesper see and drive Tyler's Linux laptop (CachyOS, KDE Wayland) for co-op gaming (RS3).
Same endpoints/JSON as the Windows version:
  GET  /screenshot   -> PNG of primary screen (spectacle -b -n -o)
  GET  /info         -> screen size + hostname
  POST /click  {x,y,button}   -> click (ydotool)
  POST /drag   {from_x,from_y,to_x,to_y} -> smooth drag (ydotool, 10 steps)
  POST /scroll {clicks}       -> wheel scroll
  POST /key    {key}          -> key press (WASD, SPACE, ENTER, ESC, arrows...)
  POST /type   {text}         -> type string
Requires: spectacle, ydotool (daemon: systemctl --user enable --now ydotool.service),
python3. Run from Tyler's DESKTOP session (Wayland socket), not a bare SSH session.
IMPORTANT: KDE Wayland — scrot/import/grim all return BLACK (see skill body). spectacle is the only working capture.
"""
import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 8080
SHOT = "/tmp/vesper_screen.png"
SOCKET = os.path.expanduser("~/.ydotool_socket")
ENV = dict(os.environ)
ENV["YDOTOOL_SOCKET"] = SOCKET

# key name -> ydotool keycode (linux input-event-codes)
KEYMAP = {
    "W": 17, "A": 30, "S": 31, "D": 32,
    "Q": 16, "E": 18, "R": 19, "F": 33,
    "SPACE": 57, "ENTER": 28, "ESC": 1,
    "TAB": 15, "SHIFT": 42, "CTRL": 29,
    "UP": 103, "DOWN": 108, "LEFT": 105, "RIGHT": 106,
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
    "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
}

# ydotool mouse buttons: BTN_LEFT=0x110(272), BTN_RIGHT=0x111(273), BTN_MIDDLE=0x112(274)
BTN = {"left": 272, "right": 273, "middle": 274}


def run(cmd, timeout=15, env=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env=env or ENV)
        return r.stdout.strip()
    except Exception as e:
        return f"ERR {e}"


def get_screen_size():
    return 1920, 1080  # updated by /info consumers; spectacle captures full compositor


def take_shot():
    # KDE Plasma Wayland: grim needs wlr-screencopy (kwin lacks it); scrot/import are X11-only (black).
    # spectacle captures through kwin itself — the ONLY reliable path on this compositor.
    run(["spectacle", "-b", "-n", "-o", SHOT])
    try:
        with open(SHOT, "rb") as f:
            return f.read()
    except Exception:
        return b""


def yd_mouse_move(x, y):
    run(["ydotool", "mousemove", "--absolute", str(x), str(y)])


def yd_click(btn=272):
    run(["ydotool", "click", str(btn)])


def yd_scroll(clicks):
    # wheel up/down via ydotool click keycodes (263 = REL_WHEEL up, 264 = down)
    btn = "263" if clicks > 0 else "264"
    for _ in range(abs(clicks)):
        run(["ydotool", "click", btn])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}", flush=True)

    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_png(self, png_bytes):
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(png_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(png_bytes)

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.lower()
        if path == "/screenshot":
            data = take_shot()
            if not data or len(data) < 1000:
                self._send_json({"error": "spectacle capture failed/black"}, 500)
                return
            self._send_png(data)
            print(f"  -> screenshot sent ({len(data)} bytes)", flush=True)
        elif path == "/info":
            w, h = get_screen_size()
            self._send_json({
                "screen_width": w,
                "screen_height": h,
                "hostname": run(["hostname"]).strip(),
                "session": "wayland",
                "engine": "spectacle+ydotool",
            })
        else:
            self._send_json({"status": "Vesper screen-control (Linux/Wayland)", "endpoints": ["/screenshot", "/info", "/click", "/drag", "/scroll", "/key", "/type"]})

    def do_POST(self):
        path = urlparse(self.path).path.lower()
        body = self._read_body()

        if path == "/click":
            x, y = int(body.get("x", 0)), int(body.get("y", 0))
            button = BTN.get(body.get("button", "left"), 272)
            yd_mouse_move(x, y)
            time.sleep(0.03)
            yd_click(button)
            print(f"  -> click ({x},{y}) btn={button}", flush=True)
            self._send_json({"ok": True})
        elif path == "/drag":
            fx, fy = int(body.get("from_x", 0)), int(body.get("from_y", 0))
            tx, ty = int(body.get("to_x", 0)), int(body.get("to_y", 0))
            yd_mouse_move(fx, fy)
            time.sleep(0.03)
            run(["ydotool", "mousedown", "272"])
            steps = 10
            for i in range(1, steps + 1):
                ix = fx + int((tx - fx) * i / steps)
                iy = fy + int((ty - fy) * i / steps)
                yd_mouse_move(ix, iy)
                time.sleep(0.02)
            time.sleep(0.03)
            run(["ydotool", "mouseup", "272"])
            print(f"  -> drag ({fx},{fy})->({tx},{ty})", flush=True)
            self._send_json({"ok": True})
        elif path == "/scroll":
            clicks = int(body.get("clicks", 0))
            yd_scroll(clicks)
            print(f"  -> scroll {clicks}", flush=True)
            self._send_json({"ok": True})
        elif path == "/key":
            key = str(body.get("key", "")).upper()
            kc = KEYMAP.get(key)
            if kc is None:
                self._send_json({"error": f"unknown key {key}"}, 400)
                return
            run(["ydotool", "key", f"{kc}:1", f"{kc}:0"])
            print(f"  -> key {key} (kc={kc})", flush=True)
            self._send_json({"ok": True})
        elif path == "/type":
            text = str(body.get("text", ""))
            run(["ydotool", "type", "--key-delay", "40", text])
            print(f"  -> type {text[:40]}{'...' if len(text) > 40 else ''}", flush=True)
            self._send_json({"ok": True})
        else:
            self._send_json({"error": "unknown endpoint"}, 404)


def main():
    print("=== Vesper Screen-Control (Linux/Wayland) ===", flush=True)
    print(f"Listening on {HOST}:{PORT} — spectacle+ydotool", flush=True)
    print(f"Socket: {SOCKET}", flush=True)
    srv = HTTPServer((HOST, PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!", flush=True)


if __name__ == "__main__":
    main()

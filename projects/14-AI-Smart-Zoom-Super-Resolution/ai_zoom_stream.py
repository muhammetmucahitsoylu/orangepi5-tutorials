#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Smart Zoom & Neural Super-Resolution Live Streaming Server
Real-time 1080p camera capture, dynamic ROI zoom, FSRCNN/ESPCN super-resolution,
and side-by-side interactive web dashboard on Orange Pi 5 (RK3588S).
Zero external pip dependencies (Pure Python 3 standard library + OpenCV).
"""

import os
import sys
import time
import threading
import argparse
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import cv2
from cv2 import dnn_superres
import numpy as np

# Global shared state
class StreamState:
    def __init__(self):
        self.lock = threading.Lock()
        self.raw_frame = None
        self.processed_frame = None
        self.zoom_level = 2.0
        self.active_model_name = "fsrcnn_x2"
        self.display_mode = "split" # "split", "ai_only", "bicubic_only"
        self.fps = 0.0
        self.inference_ms = 0.0
        self.soc_temp = 0.0
        self.is_running = True
        self.snapshot_counter = 0

state = StreamState()

def get_soc_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

class CameraThread(threading.Thread):
    def __init__(self, source_idx=0, width=1920, height=1080):
        super().__init__(daemon=True)
        self.source_idx = source_idx
        self.width = width
        self.height = height
        self.cap = None

    def run(self):
        print(f"[*] Starting Camera Thread on /dev/video{self.source_idx} (FourCC: MJPG, {self.width}x{self.height})...")
        self.cap = cv2.VideoCapture(self.source_idx)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print(f"[HATA] Cannot open camera on index {self.source_idx}!")
            state.is_running = False
            return

        print("[OK] Camera capture loop active and streaming frames.")
        while state.is_running:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            with state.lock:
                state.raw_frame = frame
        
        if self.cap:
            self.cap.release()

class ProcessingThread(threading.Thread):
    def __init__(self, models_dir):
        super().__init__(daemon=True)
        self.models_dir = models_dir
        self.models = {}
        self.load_models()

    def load_models(self):
        print("[*] Pre-loading Super-Resolution Neural Networks...")
        configs = [
            ("fsrcnn_x2", "FSRCNN_x2.pb", "fsrcnn", 2),
            ("fsrcnn_x4", "FSRCNN_x4.pb", "fsrcnn", 4),
            ("espcn_x2",  "ESPCN_x2.pb",  "espcn",  2),
            ("espcn_x4",  "ESPCN_x4.pb",  "espcn",  4),
        ]
        for key, fname, algo, scale in configs:
            path = os.path.join(self.models_dir, fname)
            if os.path.exists(path):
                sr = dnn_superres.DnnSuperResImpl_create()
                sr.readModel(path)
                sr.setModel(algo, scale)
                sr.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                sr.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                self.models[key] = (sr, scale)
                print(f"  [+] Loaded {key} ({algo.upper()} {scale}x): {path}")
            else:
                print(f"  [-] Model file not found: {path}")

    def run(self):
        fps_count = 0
        fps_start = time.perf_counter()
        
        while state.is_running:
            t0 = time.perf_counter()
            with state.lock:
                frame = None if state.raw_frame is None else state.raw_frame.copy()
                zoom = state.zoom_level
                model_key = state.active_model_name
                mode = state.display_mode

            if frame is None:
                time.sleep(0.01)
                continue

            orig_h, orig_w = frame.shape[:2]

            # 1. Determine ROI bounding box based on zoom level
            crop_w = int(orig_w / zoom)
            crop_h = int(orig_h / zoom)
            
            # Fixed standard patch size for smooth real-time video
            # Scale patch to reasonable resolution for high FPS
            cx, cy = orig_w // 2, orig_h // 2
            x1 = max(0, cx - crop_w // 2)
            y1 = max(0, cy - crop_h // 2)
            x2 = min(orig_w, x1 + crop_w)
            y2 = min(orig_h, y1 + crop_h)
            
            roi = frame[y1:y2, x1:x2]
            
            # Pre-downscale ROI if too large for real-time neural inference (keep input <= 320x240 for high FPS)
            inf_input = roi
            input_h, input_w = inf_input.shape[:2]
            if input_w > 320 or input_h > 240:
                inf_input = cv2.resize(inf_input, (320, int(320 * input_h / input_w)), interpolation=cv2.INTER_AREA)

            # 2. Select AI model
            sr_obj, sr_scale = self.models.get(model_key, (None, 2))
            
            # 3. Super-Resolution Inference vs. Bicubic
            t_inf_start = time.perf_counter()
            if sr_obj is not None:
                ai_upscaled = sr_obj.upsample(inf_input)
            else:
                ai_upscaled = cv2.resize(inf_input, (inf_input.shape[1] * 2, inf_input.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
            t_inf_end = time.perf_counter()
            inf_ms = (t_inf_end - t_inf_start) * 1000.0

            # Target display resolution for comparison
            disp_h, disp_w = ai_upscaled.shape[:2]
            bicubic_zoom = cv2.resize(inf_input, (disp_w, disp_h), interpolation=cv2.INTER_CUBIC)

            # 4. Compose Display Frame based on Mode
            if mode == "split":
                # Annotate left (Bicubic)
                cv2.rectangle(bicubic_zoom, (0, 0), (disp_w, 36), (15, 15, 15), -1)
                cv2.putText(bicubic_zoom, f"CLASSICAL BICUBIC ZOOM ({zoom:.1f}x)", (10, 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 180, 255), 2, cv2.LINE_AA)
                
                # Annotate right (AI)
                cv2.rectangle(ai_upscaled, (0, 0), (disp_w, 36), (15, 15, 15), -1)
                cv2.putText(ai_upscaled, f"AI NEURAL SUPER-RES ({model_key.upper()})", (10, 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 180), 2, cv2.LINE_AA)
                
                # Divider bar
                divider = np.zeros((disp_h, 4, 3), dtype=np.uint8)
                divider[:, :] = (0, 255, 255) # Yellow separator line
                
                composite = np.hstack([bicubic_zoom, divider, ai_upscaled])
            elif mode == "ai_only":
                cv2.rectangle(ai_upscaled, (0, 0), (disp_w, 36), (15, 15, 15), -1)
                cv2.putText(ai_upscaled, f"AI NEURAL SUPER-RES ({model_key.upper()} - {zoom:.1f}x)", (10, 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2, cv2.LINE_AA)
                composite = ai_upscaled
            else:
                cv2.rectangle(bicubic_zoom, (0, 0), (disp_w, 36), (15, 15, 15), -1)
                cv2.putText(bicubic_zoom, f"CLASSICAL BICUBIC ZOOM ({zoom:.1f}x)", (10, 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 180, 255), 2, cv2.LINE_AA)
                composite = bicubic_zoom

            # 5. Telemetry Footer
            fps_count += 1
            if time.perf_counter() - fps_start >= 1.0:
                with state.lock:
                    state.fps = fps_count / (time.perf_counter() - fps_start)
                    state.inference_ms = inf_ms
                    state.soc_temp = get_soc_temperature()
                fps_count = 0
                fps_start = time.perf_counter()

            footer = np.zeros((32, composite.shape[1], 3), dtype=np.uint8)
            with state.lock:
                fps_val = state.fps
                temp_val = state.soc_temp
            
            telemetry_str = f"FPS: {fps_val:4.1f} | NPU/CPU Latency: {inf_ms:5.1f} ms | SoC Temp: {temp_val:4.1f} C | Zoom: {zoom:.1f}x"
            cv2.putText(footer, telemetry_str, (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
            cv2.putText(footer, "Orange Pi 5 (RK3588S)", (composite.shape[1] - 185, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1, cv2.LINE_AA)
            
            final_view = np.vstack([composite, footer])

            with state.lock:
                state.processed_frame = final_view

HTML_PAGE = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orange Pi 5 - AI Smart Zoom & Super-Resolution Dashboard</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --accent: #00ffaa;
            --accent-blue: #58a6ff;
            --text-color: #c9d1d9;
            --border: #30363d;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-color); color: var(--text-color); padding: 18px; text-align: center; }
        header { margin-bottom: 16px; }
        h1 { font-size: 1.6rem; color: #ffffff; letter-spacing: 0.5px; }
        h1 span { color: var(--accent); }
        .subtitle { font-size: 0.9rem; color: #8b949e; margin-top: 4px; }
        .container { max-width: 1360px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
        .stream-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        .stream-img { width: 100%; height: auto; display: block; background: #000; }
        .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; background: var(--card-bg); padding: 16px; border: 1px solid var(--border); border-radius: 12px; text-align: left; }
        .control-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 0.85rem; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }
        .slider-wrap { display: flex; align-items: center; gap: 12px; }
        input[type=range] { flex: 1; accent-color: var(--accent); cursor: pointer; }
        .badge { font-weight: bold; font-size: 1rem; color: var(--accent); min-width: 45px; }
        .btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
        button { background: #21262d; color: var(--text-color); border: 1px solid var(--border); padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
        button:hover { background: #30363d; border-color: #8b949e; }
        button.active { background: var(--accent); color: #0d1117; font-weight: bold; border-color: var(--accent); }
        .snapshot-btn { background: #238636; color: #fff; font-weight: bold; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; transition: background 0.2s; }
        .snapshot-btn:hover { background: #2ea043; }
        .toast { position: fixed; bottom: 20px; right: 20px; background: var(--accent); color: #000; padding: 12px 20px; border-radius: 8px; font-weight: bold; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Orange Pi 5 (RK3588S) <span>AI Smart Zoom</span></h1>
            <p class="subtitle">Real-Time Neural Super-Resolution vs. Classical Digital Interpolation</p>
        </header>

        <div class="stream-card">
            <img class="stream-img" src="/video_feed" alt="Live AI Zoom Stream">
        </div>

        <div class="controls">
            <div class="control-group">
                <label>🔍 Digital Zoom Level</label>
                <div class="slider-wrap">
                    <input type="range" id="zoomSlider" min="1.0" max="4.0" step="0.1" value="2.0" oninput="updateZoom(this.value)">
                    <span class="badge" id="zoomVal">2.0x</span>
                </div>
            </div>

            <div class="control-group">
                <label>🧠 Super-Resolution Model</label>
                <div class="btn-group">
                    <button class="active" onclick="setModel('fsrcnn_x2', this)">FSRCNN (2x)</button>
                    <button onclick="setModel('fsrcnn_x4', this)">FSRCNN (4x)</button>
                    <button onclick="setModel('espcn_x2', this)">ESPCN (2x)</button>
                    <button onclick="setModel('espcn_x4', this)">ESPCN (4x)</button>
                </div>
            </div>

            <div class="control-group">
                <label>📺 Display Mode</label>
                <div class="btn-group">
                    <button class="active" onclick="setMode('split', this)">Split View</button>
                    <button onclick="setMode('ai_only', this)">AI Only</button>
                    <button onclick="setMode('bicubic_only', this)">Bicubic Only</button>
                </div>
            </div>

            <div class="control-group" style="justify-content: flex-end;">
                <label>📸 Export Snapshot</label>
                <button class="snapshot-btn" onclick="takeSnapshot()">Capture High-Res Snapshot</button>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Snapshot saved to disk!</div>

    <script>
        function updateZoom(val) {
            document.getElementById('zoomVal').innerText = parseFloat(val).toFixed(1) + 'x';
            fetch('/api/zoom?level=' + val);
        }
        function setModel(name, btn) {
            document.querySelectorAll('.control-group:nth-child(2) button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            fetch('/api/model?name=' + name);
        }
        function setMode(name, btn) {
            document.querySelectorAll('.control-group:nth-child(3) button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            fetch('/api/mode?name=' + name);
        }
        function takeSnapshot() {
            fetch('/api/snapshot').then(r => r.json()).then(data => {
                const t = document.getElementById('toast');
                t.innerText = 'Snapshot saved: ' + data.filename;
                t.style.display = 'block';
                setTimeout(() => { t.style.display = 'none'; }, 3000);
            });
        }
    </script>
</body>
</html>
"""

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/video_feed":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()

            while state.is_running:
                with state.lock:
                    frame = None if state.processed_frame is None else state.processed_frame.copy()

                if frame is None:
                    time.sleep(0.02)
                    continue

                # Encode frame to JPEG with high quality
                ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if not ret:
                    continue

                frame_bytes = jpeg.tobytes()
                try:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame_bytes)}\r\n\r\n".encode("utf-8"))
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b"\r\n")
                except (BrokenPipeError, ConnectionResetError):
                    break
                time.sleep(0.01)

        elif path == "/api/zoom":
            if "level" in params:
                try:
                    z = float(params["level"][0])
                    with state.lock:
                        state.zoom_level = max(1.0, min(4.0, z))
                except ValueError:
                    pass
            self.send_response(200)
            self.end_headers()

        elif path == "/api/model":
            if "name" in params:
                m = params["name"][0]
                with state.lock:
                    state.active_model_name = m
            self.send_response(200)
            self.end_headers()

        elif path == "/api/mode":
            if "name" in params:
                m = params["name"][0]
                with state.lock:
                    state.display_mode = m
            self.send_response(200)
            self.end_headers()

        elif path == "/api/snapshot":
            filename = ""
            with state.lock:
                state.snapshot_counter += 1
                filename = f"ai_zoom_snapshot_{int(time.time())}_{state.snapshot_counter}.jpg"
                if state.processed_frame is not None:
                    cv2.imwrite(filename, state.processed_frame)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"status": "ok", "filename": "{filename}"}}'.encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default HTTP server access logs for maximum throughput
        pass

def main():
    parser = argparse.ArgumentParser(description="Live AI Smart Zoom Server for Orange Pi 5")
    parser.add_argument("--source", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default: 5000)")
    parser.add_argument("--width", type=int, default=1920, help="Camera width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Camera height (default: 1080)")
    args = parser.parse_args()

    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

    print("=" * 72)
    print("🚀 ORANGE PI 5 (RK3588S) AI SMART ZOOM & SUPER-RESOLUTION SERVER")
    print("=" * 72)
    print(f"[*] Camera Source Index : /dev/video{args.source} ({args.width}x{args.height})")
    print(f"[*] Models Directory    : {models_dir}")
    print(f"[*] Web Server Port     : {args.port}")

    # Start Worker Threads
    cam_thread = CameraThread(source_idx=args.source, width=args.width, height=args.height)
    cam_thread.start()

    proc_thread = ProcessingThread(models_dir=models_dir)
    proc_thread.start()

    server = ThreadedHTTPServer(("0.0.0.0", args.port), StreamHandler)
    print(f"\n[READY] Web Server is live at: http://<ORANGE_PI_IP>:{args.port}")
    print("   -> Open http://<ORANGE_PI_IP>:5000 in your browser to view AI Zoom!")
    print("   -> Press Ctrl+C to terminate server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down AI Zoom server...")
    finally:
        state.is_running = False
        server.server_close()
        print("[*] Server terminated cleanly.")

if __name__ == "__main__":
    main()

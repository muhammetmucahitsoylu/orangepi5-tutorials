#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Smart Zoom & Neural Super-Resolution Live Streaming Server
Real-time 1080p hardware camera ingestion, dynamic ROI zoom, FSRCNN/ESPCN neural networks,
adaptive edge sharpening, CLAHE micro-contrast, and interactive side-by-side web dashboard
on Orange Pi 5 (Rockchip RK3588S).
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
        self.sharpen_level = 1.4      # 0.0 (raw neural) to 2.5 (maximum edge crispness)
        self.contrast_level = 2.0     # 0.0 (off) to 4.0 (CLAHE clip limit)
        self.active_model_name = "fsrcnn_x2"
        self.display_mode = "split"   # "split", "ai_only", "bicubic_only"
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
        print(f"[*] Initializing Hardware Camera on /dev/video{self.source_idx} (V4L2, FourCC: MJPG, {self.width}x{self.height})...")
        # Must pass cv2.CAP_V4L2 to ensure 1080p is negotiated rather than falling back to 640x480
        self.cap = cv2.VideoCapture(self.source_idx, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print(f"[HATA] Cannot open camera on index {self.source_idx}!")
            state.is_running = False
            return

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[OK] Camera negotiated resolution: {actual_w}x{actual_h} @ V4L2 MJPG")

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
            with state.lock:
                frame = None if state.raw_frame is None else state.raw_frame.copy()
                zoom = state.zoom_level
                model_key = state.active_model_name
                mode = state.display_mode
                s_level = state.sharpen_level
                c_level = state.contrast_level

            if frame is None:
                time.sleep(0.01)
                continue

            orig_h, orig_w = frame.shape[:2]

            # 1. Determine ROI bounding box based on zoom level (centered)
            crop_w = max(32, int(orig_w / zoom))
            crop_h = max(24, int(orig_h / zoom))
            
            cx, cy = orig_w // 2, orig_h // 2
            x1 = max(0, cx - crop_w // 2)
            y1 = max(0, cy - crop_h // 2)
            x2 = min(orig_w, x1 + crop_w)
            y2 = min(orig_h, y1 + crop_h)
            
            roi = frame[y1:y2, x1:x2]
            
            # Keep patch at optimal size (cap width to 480 for real-time 15-25 FPS inference)
            inf_input = roi
            input_h, input_w = inf_input.shape[:2]
            if input_w > 480:
                scale_ratio = 480.0 / input_w
                inf_input = cv2.resize(inf_input, (480, int(input_h * scale_ratio)), interpolation=cv2.INTER_AREA)

            # 2. Select AI model
            sr_obj, sr_scale = self.models.get(model_key, (None, 2))
            
            # 3. Super-Resolution Inference
            t_inf_start = time.perf_counter()
            if sr_obj is not None:
                ai_raw = sr_obj.upsample(inf_input)
            else:
                ai_raw = cv2.resize(inf_input, (inf_input.shape[1] * 2, inf_input.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
            
            disp_h, disp_w = ai_raw.shape[:2]

            # 4. Classical Bicubic Zoom (Un-enhanced baseline)
            bicubic_zoom = cv2.resize(inf_input, (disp_w, disp_h), interpolation=cv2.INTER_CUBIC)

            # 5. Smart AI Detail Reconstruction Pipeline
            ai_upscaled = ai_raw.copy()

            # A) Micro-Contrast Enhancement (CLAHE on Luminance channel)
            if c_level > 0.05:
                ycrcb = cv2.cvtColor(ai_upscaled, cv2.COLOR_BGR2YCrCb)
                y_plane, cr_plane, cb_plane = cv2.split(ycrcb)
                clahe = cv2.createCLAHE(clipLimit=c_level, tileGridSize=(8, 8))
                y_enhanced = clahe.apply(y_plane)
                ai_upscaled = cv2.cvtColor(cv2.merge([y_enhanced, cr_plane, cb_plane]), cv2.COLOR_YCrCb2BGR)

            # B) Adaptive Edge Sharpening (Unsharp Masking)
            if s_level > 0.05:
                gaussian = cv2.GaussianBlur(ai_upscaled, (0, 0), 2.0)
                ai_upscaled = cv2.addWeighted(ai_upscaled, 1.0 + s_level, gaussian, -s_level, 0)

            t_inf_end = time.perf_counter()
            inf_ms = (t_inf_end - t_inf_start) * 1000.0

            # 6. Compose Display Frame based on Mode
            if mode == "split":
                # Annotate left (Bicubic Baseline)
                cv2.rectangle(bicubic_zoom, (0, 0), (disp_w, 38), (15, 15, 15), -1)
                cv2.putText(bicubic_zoom, f"CLASSICAL BICUBIC ZOOM ({zoom:.1f}x)", (12, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 160, 255), 2, cv2.LINE_AA)
                
                # Annotate right (Smart AI Super-Res)
                cv2.rectangle(ai_upscaled, (0, 0), (disp_w, 38), (15, 15, 15), -1)
                ai_tag = f"SMART AI SUPER-RES ({model_key.upper()} | Sharp:{s_level:.1f}x)"
                cv2.putText(ai_upscaled, ai_tag, (12, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 170), 2, cv2.LINE_AA)
                
                # Divider bar
                divider = np.zeros((disp_h, 4, 3), dtype=np.uint8)
                divider[:, :] = (0, 240, 255) # Bright cyan-gold separator line
                
                composite = np.hstack([bicubic_zoom, divider, ai_upscaled])
            elif mode == "ai_only":
                cv2.rectangle(ai_upscaled, (0, 0), (disp_w, 38), (15, 15, 15), -1)
                ai_tag = f"SMART AI SUPER-RES ({model_key.upper()} | {zoom:.1f}x | Sharp:{s_level:.1f}x)"
                cv2.putText(ai_upscaled, ai_tag, (12, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 170), 2, cv2.LINE_AA)
                composite = ai_upscaled
            else:
                cv2.rectangle(bicubic_zoom, (0, 0), (disp_w, 38), (15, 15, 15), -1)
                cv2.putText(bicubic_zoom, f"CLASSICAL BICUBIC ZOOM ({zoom:.1f}x)", (12, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.58, (100, 160, 255), 2, cv2.LINE_AA)
                composite = bicubic_zoom

            # 7. Telemetry Footer
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
            
            telemetry_str = f"FPS: {fps_val:4.1f} | Latency: {inf_ms:5.1f} ms | SoC Temp: {temp_val:4.1f} C | Zoom: {zoom:.1f}x | Sharpness: {s_level:.1f}x"
            cv2.putText(footer, telemetry_str, (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 220, 220), 1, cv2.LINE_AA)
            cv2.putText(footer, "Orange Pi 5 (RK3588S)", (composite.shape[1] - 185, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 220, 255), 1, cv2.LINE_AA)
            
            final_view = np.vstack([composite, footer])

            with state.lock:
                state.processed_frame = final_view

HTML_PAGE = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orange Pi 5 - Smart AI Zoom & Super-Resolution</title>
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #131b2e;
            --accent: #00f59b;
            --accent-blue: #38bdf8;
            --text-color: #e2e8f0;
            --text-muted: #94a3b8;
            --border: rgba(255, 255, 255, 0.08);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg-color); color: var(--text-color); padding: 18px; text-align: center; }
        header { margin-bottom: 16px; }
        h1 { font-size: 1.6rem; color: #ffffff; letter-spacing: 0.5px; }
        h1 span { color: var(--accent); }
        .subtitle { font-size: 0.9rem; color: var(--text-muted); margin-top: 4px; }
        .container { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
        .stream-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 12px 32px rgba(0,0,0,0.6); }
        .stream-img { width: 100%; height: auto; display: block; background: #000; }
        
        .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; background: var(--card-bg); padding: 18px; border: 1px solid var(--border); border-radius: 12px; text-align: left; }
        .control-group { display: flex; flex-direction: column; gap: 8px; }
        label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; display: flex; justify-content: space-between; align-items: center; }
        .slider-wrap { display: flex; align-items: center; gap: 12px; }
        input[type=range] { flex: 1; accent-color: var(--accent); cursor: pointer; height: 6px; }
        .badge { font-weight: bold; font-size: 0.95rem; color: var(--accent); min-width: 48px; text-align: right; }
        
        .btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
        button { background: #1e293b; color: var(--text-color); border: 1px solid var(--border); padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
        button:hover { background: #334155; border-color: var(--accent-blue); }
        button.active { background: var(--accent); color: #0b0f19; font-weight: bold; border-color: var(--accent); box-shadow: 0 0 12px rgba(0,245,155,0.3); }
        
        .snapshot-btn { background: #059669; color: #fff; font-weight: bold; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; transition: background 0.2s, transform 0.1s; }
        .snapshot-btn:hover { background: #10b981; transform: translateY(-1px); }
        .toast { position: fixed; bottom: 24px; right: 24px; background: var(--accent); color: #0b0f19; padding: 12px 24px; border-radius: 8px; font-weight: bold; display: none; box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 999; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Orange Pi 5 (RK3588S) <span>Smart AI Zoom & Super-Resolution</span></h1>
            <p class="subtitle">1080p UVC Ingestion &bull; Neural Super-Resolution vs. Classical Bicubic Zoom</p>
        </header>

        <div class="stream-card">
            <img class="stream-img" src="/video_feed" alt="Live AI Zoom Stream">
        </div>

        <div class="controls">
            <!-- Zoom Slider -->
            <div class="control-group">
                <label>🔍 Dijital Zoom Çarpanı <span id="zoomVal" class="badge">2.0x</span></label>
                <div class="slider-wrap">
                    <input type="range" id="zoomSlider" min="1.0" max="4.0" step="0.1" value="2.0" oninput="updateZoom(this.value)">
                </div>
            </div>

            <!-- Neural Sharpness Slider -->
            <div class="control-group">
                <label>⚡ Keskinlik Gücü (Unsharp Mask) <span id="sharpVal" class="badge">1.4x</span></label>
                <div class="slider-wrap">
                    <input type="range" id="sharpSlider" min="0.0" max="2.5" step="0.1" value="1.4" oninput="updateSharp(this.value)">
                </div>
            </div>

            <!-- Contrast Slider -->
            <div class="control-group">
                <label>🌟 Mikro-Kontrast (CLAHE) <span id="contrastVal" class="badge">2.0</span></label>
                <div class="slider-wrap">
                    <input type="range" id="contrastSlider" min="0.0" max="4.0" step="0.5" value="2.0" oninput="updateContrast(this.value)">
                </div>
            </div>

            <!-- Super-Resolution Model Selection -->
            <div class="control-group">
                <label>🧠 Yapay Zeka Modeli</label>
                <div class="btn-group">
                    <button class="active" onclick="setModel('fsrcnn_x2', this)">FSRCNN (2x)</button>
                    <button onclick="setModel('fsrcnn_x4', this)">FSRCNN (4x)</button>
                    <button onclick="setModel('espcn_x2', this)">ESPCN (2x)</button>
                    <button onclick="setModel('espcn_x4', this)">ESPCN (4x)</button>
                </div>
            </div>

            <!-- Display Mode Selection -->
            <div class="control-group">
                <label>📺 Görüntü Modu</label>
                <div class="btn-group">
                    <button class="active" onclick="setMode('split', this)">Split View (Kıyaslama)</button>
                    <button onclick="setMode('ai_only', this)">Sadece AI</button>
                    <button onclick="setMode('bicubic_only', this)">Sadece Bicubic</button>
                </div>
            </div>

            <!-- Snapshot Export -->
            <div class="control-group" style="justify-content: flex-end;">
                <label>📸 Snapshot Kaydet</label>
                <button class="snapshot-btn" onclick="takeSnapshot()">Yüksek Çözünürlüklü Kare Al</button>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Snapshot başarıyla kaydedildi!</div>

    <script>
        function updateZoom(val) {
            document.getElementById('zoomVal').innerText = parseFloat(val).toFixed(1) + 'x';
            fetch('/api/zoom?level=' + val);
        }
        function updateSharp(val) {
            const v = parseFloat(val);
            document.getElementById('sharpVal').innerText = v === 0 ? 'KAPALI' : v.toFixed(1) + 'x';
            fetch('/api/sharpen?val=' + val);
        }
        function updateContrast(val) {
            const v = parseFloat(val);
            document.getElementById('contrastVal').innerText = v === 0 ? 'KAPALI' : v.toFixed(1);
            fetch('/api/contrast?val=' + val);
        }
        function setModel(name, btn) {
            document.querySelectorAll('.control-group:nth-child(4) button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            fetch('/api/model?name=' + name);
        }
        function setMode(name, btn) {
            document.querySelectorAll('.control-group:nth-child(5) button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            fetch('/api/mode?name=' + name);
        }
        function takeSnapshot() {
            fetch('/api/snapshot').then(r => r.json()).then(data => {
                const t = document.getElementById('toast');
                t.innerText = 'Snapshot Kaydedildi: ' + data.filename;
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

                ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
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

        elif path == "/api/sharpen":
            if "val" in params:
                try:
                    s = float(params["val"][0])
                    with state.lock:
                        state.sharpen_level = max(0.0, min(2.5, s))
                except ValueError:
                    pass
            self.send_response(200)
            self.end_headers()

        elif path == "/api/contrast":
            if "val" in params:
                try:
                    c = float(params["val"][0])
                    with state.lock:
                        state.contrast_level = max(0.0, min(4.0, c))
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
    print("🚀 ORANGE PI 5 (RK3588S) SMART AI ZOOM & SUPER-RESOLUTION SERVER")
    print("=" * 72)
    print(f"[*] Camera Source Index : /dev/video{args.source} (Target: {args.width}x{args.height})")
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

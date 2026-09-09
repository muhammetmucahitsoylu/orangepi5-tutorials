# **Orange Pi 5 (RK3588S) Real-Time Camera and NPU Vision Pipeline Guide**

This guide demonstrates how to build an end-to-end, zero-latency computer vision pipeline on the Orange Pi 5 (Rockchip RK3588S). It ingests video from a **USB UVC WebCam** or an **RTSP IP Camera**, uses dedicated capture threads to eliminate stream buffering, accelerates **YOLOv8** object detection across the **6 TOPS 3-core NPU**, and broadcasts the annotated stream with live telemetry (FPS, NPU latency, SoC thermals) via an embedded HTTP MJPEG web server.

---

## **1. Pipeline Architecture: Overcoming the Sequential Loop Bottleneck**

A standard sequential `while True` loop is disastrous for real-time edge streaming:

```
Flawed Sequential Design:
[ Frame Capture (30ms) ] ──> [ NPU Inference (15ms) ] ──> [ Encoding & Display (10ms) ] ──> TOTAL: 55ms (~18 FPS)
*Hardware camera framebuffers fill up, resulting in severe 2-3 second video lag!
```

Our decoupled **Asynchronous Multi-Threaded Pipeline**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Camera Input (USB / RTSP)                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Thread 1: Dedicated Ingestion Engine                                  │
│  - Continuously drains hardware buffer (`cap.grab()`)                  │
│  - Retains strictly the latest frame in memory (Zero Latency)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Latest Raw Frame)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Thread 2: NPU YOLOv8 Inference Engine (RKNN-Lite2)                    │
│  - Tri-core NPU (Core 0, 1, 2) hardware-accelerated tensor operations  │
│  - Bounding box regression and Non-Maximum Suppression (NMS)           │
│  - Real-time telemetry monitoring (Inference ms, SoC thermals, FPS)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Web Ingestion: Threaded MJPEG HTTP Server (Flask)                     │
│  - Zero client configuration: Viewable in any modern browser           │
│  - Endpoint: `http://ORANGE_PI_IP:5000`                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **2. Critical Hardware & Driver Considerations**

1. **Headless Execution & Qt Abort:** Running standard `cv2.imshow()` on an SSH/headless server crashes instantly:
   ```
   qt.qpa.plugin: Could not find the platform plugin "xcb" ...
   ```
   Broadcasting over HTTP MJPEG eliminates any display server dependency.
2. **USB UVC Video Format Lock:** Default USB drivers often default to uncompressed `YUYV` over USB 2.0, throttling the camera to 5 FPS. Enforcing FourCC `MJPG` inside OpenCV unlocks 30 to 60 FPS hardware capture.
3. **RTSP Buffer Lag:** By default, FFmpeg buffers 30+ frames. Setting low-delay and zero-buffer flags drops network camera latency to <100ms.
4. **The MIPI CSI Trap vs. USB UVC (Rockchip RKAIQ ISP Quirk):**
   * **USB UVC Webcams (Plug & Play):** Feature integrated hardware ISPs, outputting pre-processed MJPEG/YUYV directly via standard V4L2 and `cv2.VideoCapture(0)`.
   * **MIPI CSI Sensors (OV13850, IMX415, etc.):** Stream raw Bayer sensor data into the RK3588 SoC. Processing this raw data requires Rockchip's proprietary **RKAIQ 3A Server (`librkaiq.so` / `rkaiq_3A_server`)** userspace daemon for Auto Exposure (AE), Auto White Balance (AWB), and Focus (AF).
   * *Why standard OpenCV fails on MIPI CSI:* Opening `/dev/video11` directly without an active RKAIQ daemon yields a completely black or corrupted frame. MIPI CSI requires constructing a dedicated GStreamer pipeline (`v4l2src device=/dev/video11 ! video/x-raw,format=NV12 ... ! appsink`) with Rockchip media-ctl routing. For frictionless computer vision development, this guide standardizes on high-throughput USB UVC / RTSP streams.

---

## **3. Step 1: Environment & Dependencies**

On your Orange Pi 5:

```bash
sudo apt update
sudo apt install -y v4l-utils python3-pip python3-opencv

# Python web and array processing libraries
pip3 install flask numpy pillow
```

### **Verify Camera Device:**
If using a USB camera, verify device node recognition:
```bash
v4l2-ctl --list-devices
```
*Confirm availability of `/dev/video0` or `/dev/video1`.*

---

## **4. Step 2: Acquire the RKNN YOLOv8 Model**

We will use the `yolov8n_rk3588.rknn` compiled in Project 03 or the official Rockchip model zoo:

```bash
mkdir -p ~/projects/camera-pipeline && cd ~/projects/camera-pipeline

# Option 1 (Recommended): Copy model compiled in Project 03:
if [ -f ~/projects/ilk-projem/models/yolov8n_rk3588.rknn ]; then
    cp ~/projects/ilk-projem/models/yolov8n_rk3588.rknn ./yolov8n.rknn
    echo "Successfully copied model from Project 03."
fi

# Option 2: Clone and copy from official airockchip rknn_model_zoo:
# git clone --depth 1 https://github.com/airockchip/rknn_model_zoo.git
# cp rknn_model_zoo/examples/yolov8/model/RK3588/yolov8n.rknn ./yolov8n.rknn
```

---

## **5. Step 3: Complete Asynchronous Vision Pipeline (`pipeline.py`)**

Create `pipeline.py`:

```python
import os
import cv2
import time
import threading
import numpy as np
from flask import Flask, Response, render_template_string
from rknnlite.api import RKNNLite

# --- CONFIGURATION ---
MODEL_PATH = "yolov8n.rknn"
CAMERA_SOURCE = 0          # 0 for USB WebCam, or RTSP URL: "rtsp://admin:pass@192.168.1.50:554/stream"
INPUT_SIZE = 640
OBJ_THRESH = 0.45
NMS_THRESH = 0.50

# 80 COCO Classes
CLASSES = ("person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
           "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
           "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
           "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
           "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
           "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
           "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
           "sofa", "pottedplant", "bed", "diningtable", "toilet", "vtvmonitor", "laptop", "mouse",
           "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
           "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush")

COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# Shared state
latest_raw_frame = None
latest_processed_frame = None
frame_lock = threading.Lock()
is_running = True
telemetry = {"fps": 0.0, "latency": 0.0, "temp": 0.0, "objects": 0}

def get_soc_temp():
    """Reads RK3588 on-die thermal sensor."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

# --- 1. DEDICATED CAMERA INGESTION THREAD ---
def camera_capture_thread():
    global latest_raw_frame, is_running
    
    if isinstance(CAMERA_SOURCE, str) and CAMERA_SOURCE.startswith("rtsp"):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
        cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(CAMERA_SOURCE)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("[-] Error: Unable to open camera source!")
        is_running = False
        return

    print("[+] Camera capture pipeline initiated.")
    while is_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        
        with frame_lock:
            latest_raw_frame = frame

    cap.release()

# --- 2. NPU ACCELERATED INFERENCE THREAD ---
def npu_inference_thread():
    global latest_raw_frame, latest_processed_frame, is_running, telemetry
    
    rknn = RKNNLite()
    if rknn.load_rknn(MODEL_PATH) != 0:
        print("[-] Failed to load RKNN model!")
        is_running = False
        return

    # Enable tri-core NPU scheduling
    if rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2) != 0:
        print("[-] Failed to initialize NPU runtime!")
        is_running = False
        return

    print("[+] Tri-core NPU Engine Online. Inference running...")
    
    fps_counter = 0
    fps_timer = time.time()

    while is_running:
        frame = None
        with frame_lock:
            if latest_raw_frame is not None:
                frame = latest_raw_frame.copy()

        if frame is None:
            time.sleep(0.005)
            continue

        start_t = time.time()
        orig_h, orig_w = frame.shape[:2]

        # Preprocessing: Resize to 640x640 & convert BGR to RGB
        input_img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = np.expand_dims(input_img, axis=0)

        # NPU Forward Pass
        outputs = rknn.rknn_run(inputs=[input_img])

        # YOLOv8 Parsing
        pred = np.squeeze(outputs[0]).transpose() # (8400, 84)
        boxes = pred[:, :4]
        class_scores = pred[:, 4:]

        # Map center/width coordinates back to source aspect ratio
        x1 = (boxes[:, 0] - boxes[:, 2] / 2) * (orig_w / INPUT_SIZE)
        y1 = (boxes[:, 1] - boxes[:, 3] / 2) * (orig_h / INPUT_SIZE)
        x2 = (boxes[:, 0] + boxes[:, 2] / 2) * (orig_w / INPUT_SIZE)
        y2 = (boxes[:, 1] + boxes[:, 3] / 2) * (orig_h / INPUT_SIZE)

        formatted_boxes = np.stack([x1, y1, x2, y2], axis=-1)
        classes = np.argmax(class_scores, axis=-1)
        scores = np.max(class_scores, axis=-1)

        mask = scores > OBJ_THRESH
        valid_boxes = formatted_boxes[mask]
        valid_scores = scores[mask]
        valid_classes = classes[mask]

        indices = cv2.dnn.NMSBoxes(
            valid_boxes.tolist(), 
            valid_scores.tolist(), 
            OBJ_THRESH, 
            NMS_THRESH
        )

        detected_count = 0
        if len(indices) > 0:
            for idx in indices.flatten():
                bx = valid_boxes[idx].astype(int)
                cls_id = valid_classes[idx]
                score = valid_scores[idx]
                label = f"{CLASSES[cls_id]}: {score:.2f}"
                color = COLORS[cls_id]

                cv2.rectangle(frame, (bx[0], bx[1]), (bx[2], bx[3]), color, 2)
                cv2.putText(frame, label, (bx[0], max(20, bx[1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                detected_count += 1

        latency = (time.time() - start_t) * 1000.0

        # Telemetry Calculation
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            telemetry["fps"] = fps_counter / (time.time() - fps_timer)
            telemetry["latency"] = latency
            telemetry["temp"] = get_soc_temp()
            telemetry["objects"] = detected_count
            fps_counter = 0
            fps_timer = time.time()

        # Telemetry HUD
        hud_text = f"FPS: {telemetry['fps']:.1f} | NPU Latency: {telemetry['latency']:.1f}ms | SoC: {telemetry['temp']:.1f}C | Detections: {detected_count}"
        cv2.rectangle(frame, (0, 0), (orig_w, 35), (20, 20, 20), -1)
        cv2.putText(frame, hud_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2, cv2.LINE_AA)

        with frame_lock:
            latest_processed_frame = frame

    rknn.release()

# --- 3. FLASK STREAMING SERVER ---
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Orange Pi 5 (RK3588S) NPU Vision Stream</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #38bdf8; margin-bottom: 5px; }
        .stream-card { display: inline-block; background: #1e293b; padding: 15px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin-top: 15px; }
        img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }
        .meta { margin-top: 10px; font-size: 14px; color: #94a3b8; }
    </style>
</head>
<body>
    <h1>🍊 Orange Pi 5 Real-Time NPU Vision Pipeline</h1>
    <p>6 TOPS NPU + YOLOv8 + Multi-Threaded Low-Latency Ingestion</p>
    <div class="stream-card">
        <img src="/video_feed" alt="Live Camera Stream">
        <div class="meta">Live MJPEG Feed | Hardware Accelerated NPU Inference</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

def generate_stream():
    while is_running:
        frame = None
        with frame_lock:
            if latest_processed_frame is not None:
                frame = latest_processed_frame.copy()

        if frame is None:
            time.sleep(0.01)
            continue

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    t_cam = threading.Thread(target=camera_capture_thread, daemon=True)
    t_npu = threading.Thread(target=npu_inference_thread, daemon=True)

    t_cam.start()
    t_npu.start()

    print("[*] Web Stream hosted on: http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
```

---

## **6. Step 4: Execution & Verification**

```bash
cd ~/projects/camera-pipeline
python3 pipeline.py
```

### **Stream Access:**
Open any browser on the same network:
```text
http://ORANGE_PI_IP:5000
```
*You will see the real-time annotated feed with live telemetry reporting 30-60 FPS, 12-18ms NPU inference delay, and temperature tracking.*

---

## **7. Step 5: Continuous 24/7 `systemd` Service**

```bash
sudo tee /etc/systemd/system/npu-camera.service <<EOF
[Unit]
Description=Orange Pi 5 Real-Time NPU Camera Vision Pipeline
After=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=/home/orangepi/projects/camera-pipeline
ExecStart=/usr/bin/python3 /home/orangepi/projects/camera-pipeline/pipeline.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable npu-camera.service
sudo systemctl start npu-camera.service
```

---

## **8. Troubleshooting & Common Pitfalls**

| Symptom | Root Cause | Solution |
| :--- | :--- | :--- |
| **Stream stuck at 5 FPS** | USB camera defaults to uncompressed YUYV format. | Ensure `cv2.CAP_PROP_FOURCC = MJPG` is configured. |
| **RTSP 3-second stream delay** | FFmpeg buffers incoming network frames. | Inject `nobuffer` and `low_delay` flags into `OPENCV_FFMPEG_CAPTURE_OPTIONS`. |
| **`cv2.error: (-215:Assertion failed)`** | Input tensor shape mismatch. | Verify input resizing to (640, 640) with 3 color channels. |
| **NPU Core busy error** | Prior zombie Python process locked `/dev/rknpu*`. | Terminate using `sudo fuser -k /dev/rknpu*`. |

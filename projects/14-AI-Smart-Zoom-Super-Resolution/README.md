# Project 14: AI Smart Zoom & Neural Super-Resolution (Orange Pi 5)

> 🎯 **Hardware Accelerated Real-Time Digital Zoom Restoration on Rockchip RK3588S**

![AI Smart Zoom Banner](../../assets/banners/ai_zoom_banner.png)

This project solves the fundamental problem of **digital zoom quality degradation** using deep learning super-resolution neural networks (**FSRCNN** and **ESPCN**) on the **Orange Pi 5 (RK3588S)**.

---

## ⚡ Key Features

- **Real-Time 1080p Video Ingestion:** Zero-latency multi-threaded hardware frame grabber over USB UVC (`/dev/video0`, FourCC: `MJPG`).
- **Deep Learning Super-Resolution:** Reconstructs lost high-frequency textures and edge gradients via Sub-pixel Convolution (PixelShuffle) and Fast Super-Resolution CNNs.
- **Dynamic 1.0x – 4.0x Zoom Control:** Smooth continuous zoom adjustment without pixel stretching or aliasing.
- **Interactive Side-by-Side Web Dashboard:** View traditional digital zoom (Bicubic) vs. Neural AI Zoom simultaneously in your web browser.
- **Real-Time Telemetry:** Live FPS, neural inference latency (ms), zoom magnification, and RK3588 SoC die temperature.
- **Zero External PIP Dependencies:** Runs out of the box with standard Python 3 and OpenCV.

---

## 🚀 Quick Start

### 1. Download Pre-Trained Models
```bash
cd projects/14-AI-Smart-Zoom-Super-Resolution/models
python3 download_models.py
cd ..
```

### 2. Run CLI Benchmark & Export Comparison Image
```bash
python3 benchmark_zoom.py --source 0 --scale 2 --crop-size 240
```
This captures a frame from your connected camera, benchmarks Nearest, Bilinear, Bicubic, Lanczos, FSRCNN, and ESPCN, and exports `zoom_comparison.jpg`.

### 3. Launch the Live Interactive Web Stream
```bash
python3 ai_zoom_stream.py --source 0 --port 5000
```
Open your browser and navigate to:
```
http://<ORANGE_PI_IP>:5000
```

---

## 📊 Benchmark & Comparison

| Algorithm / Method | Type | Latency (ms) | FPS | Visual Quality |
| :--- | :--- | :--- | :--- | :--- |
| **Nearest Neighbor** | Classical | ~0.15 ms | >1000 FPS | Extreme pixelation / Blocky |
| **Bilinear** | Classical | ~0.45 ms | >1000 FPS | Noticeably blurred |
| **Bicubic** | Classical (Baseline) | ~0.85 ms | >1000 FPS | Soft edges, lack of fine texture |
| **Lanczos-4** | Classical Resampling | ~1.65 ms | ~600 FPS | Sharper but introduces ringing artifacts |
| **ESPCN (x2 / x4)** | **Neural Net (AI)** | **~44.9 ms** | **~22.2 FPS** | **Sub-pixel synthesis, crisp lines** |
| **FSRCNN (x2 / x4)**| **Neural Net (AI)** | **~65.3 ms** | **~15.3 FPS** | **Optimal visual fidelity & contrast** |

---

## 📸 Real-World Hardware Snapshots (Orange Pi Box at 4.0x Zoom)

Captured live on an **Orange Pi 5 (RK3588S)** with an active A4Tech FHD 1080P USB camera:

### 1. FSRCNN (4x Neural Super-Resolution) vs. Classical Bicubic Zoom
![FSRCNN 4x Neural Zoom vs Bicubic](../../assets/benchmarks/ai_zoom_fsrcnn_x4.jpg)

### 2. ESPCN (4x Sub-Pixel Super-Resolution) vs. Classical Bicubic Zoom
![ESPCN 4x Sub-Pixel Zoom vs Bicubic](../../assets/benchmarks/ai_zoom_espcn_x4.jpg)

### 3. FSRCNN (2x) & ESPCN (2x) Comparisons
| FSRCNN 2x Zoom | ESPCN 2x Zoom |
| :---: | :---: |
| ![FSRCNN 2x](../../assets/benchmarks/ai_zoom_fsrcnn_x2.jpg) | ![ESPCN 2x](../../assets/benchmarks/ai_zoom_espcn_x2.jpg) |


# Project 14: AI Smart Zoom & Neural Super-Resolution (Orange Pi 5)

> 🎯 **Hardware Accelerated Real-Time Digital Zoom Restoration on Rockchip RK3588S**

![AI Smart Zoom Super-Resolution Comparison](../../assets/benchmarks/ai_zoom_fsrcnn_x4.jpg)

This project solves the fundamental problem of **digital zoom quality degradation** using deep learning super-resolution neural networks (**FSRCNN** and **ESPCN**) on the **Orange Pi 5 (RK3588S)**.

---

## ⚡ Key Features

- **Rockchip RK3588 Tri-Core NPU Acceleration (6.0 TOPS):** Real-time Sub-Pixel CNN (ESPCN 3x) neural inference running on hardware NPU cores (`NPU_CORE_0_1_2`) with near-zero CPU load!
- **Real-Time 1080p Video Ingestion:** Zero-latency multi-threaded hardware frame grabber over USB UVC (`/dev/video0`, FourCC: `MJPG`, 1920x1080).
- **Deep Learning Super-Resolution:** Reconstructs lost high-frequency textures and edge gradients via Sub-pixel Convolution (PixelShuffle) and Fast Super-Resolution CNNs.
- **Dynamic 1.0x – 4.0x Zoom Control:** Smooth continuous zoom adjustment without pixel stretching or aliasing.
- **Interactive Side-by-Side Web Dashboard:** View traditional digital zoom (Bicubic) vs. Neural AI Zoom simultaneously in your web browser with live sliders for Zoom (1.0x–4.0x), Unsharp Sharpness (0.0x–2.5x), and CLAHE Micro-Contrast (0.0–4.0).
- **One-Click NPU Switching:** Seamlessly toggle between CPU FSRCNN/ESPCN models and the 6.0 TOPS RK3588 NPU engine directly from the web interface.
- **Real-Time Telemetry:** Live FPS, neural inference latency (ms), zoom magnification, NPU/CPU engine badge, and RK3588 SoC die temperature.
- **Zero External PIP Dependencies:** Runs out of the box with standard Python 3 and OpenCV (`rknn-toolkit-lite2` optional for NPU acceleration).

---

## 📦 Pre-Trained & Pre-Compiled Model Downloads

All models are pre-compiled and hosted as release assets for direct high-speed download:

| Model | Target Architecture | Format | Size | Direct Download Link |
| :--- | :--- | :---: | :---: | :--- |
| **ESPCN (3x Super-Resolution)** | **Rockchip RK3588 NPU (6 TOPS)** | `.rknn` | **512 KB** | [Direct Download `super_resolution_rk3588.rknn`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/super_resolution_rk3588.rknn) |
| **Sub-Pixel CNN (3x ONNX)** | Host Compiler / ONNX Runtime | `.onnx` | 240 KB | [Direct Download `super-resolution-10.onnx`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/super-resolution-10.onnx) |
| **FSRCNN (2x Super-Resolution)** | OpenCV DNN (CPU) | `.pb` | 39 KB | [Direct Download `FSRCNN_x2.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/FSRCNN_x2.pb) |
| **FSRCNN (4x Super-Resolution)** | OpenCV DNN (CPU) | `.pb` | 42 KB | [Direct Download `FSRCNN_x4.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/FSRCNN_x4.pb) |
| **ESPCN (2x Super-Resolution)** | OpenCV DNN (CPU) | `.pb` | 86 KB | [Direct Download `ESPCN_x2.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/ESPCN_x2.pb) |
| **ESPCN (4x Super-Resolution)** | OpenCV DNN (CPU) | `.pb` | 100 KB | [Direct Download `ESPCN_x4.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/ESPCN_x4.pb) |

---

## 🚀 Quick Start

### 1. Download & Verify Pre-Trained Models
```bash
cd projects/14-AI-Smart-Zoom-Super-Resolution/models
python3 download_models.py
cd ..
```

### 2. (Optional) Compile ONNX to RKNN for RK3588 NPU
The pre-compiled `super_resolution_rk3588.rknn` (512 KB) is already included in the repository. If you wish to re-compile from source using `rknn-toolkit2`:
```bash
python3 models/convert_to_rknn.py
```

### 3. Run CLI Benchmark & Multi-Panel Comparison
```bash
python3 benchmark_zoom.py --source 0 --scale 2 --crop-size 224
```
This benchmarks Classical Resampling (Nearest, Bilinear, Bicubic, Lanczos), CPU Deep Learning (FSRCNN, ESPCN), and the **RK3588 Tri-Core NPU**, exporting a 6-panel comparison grid `zoom_comparison.jpg`.

### 4. Launch the Live Interactive Web Stream
```bash
python3 ai_zoom_stream.py --source 0 --port 5000
```
Open your browser and navigate to:
```
http://<ORANGE_PI_IP>:5000
```
Click **"⚡ NPU ESPCN (3x 6-TOPS)"** in the web dashboard to engage the Rockchip RK3588 NPU cores!

---

## 📊 Benchmark & Comparison (Orange Pi 5 Physical Hardware)

Tested directly on **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS (Linux 6.1)** with an active A4Tech FHD 1080P USB camera:

| Algorithm / Method | Execution Backend | Latency (ms) | Est. FPS | Visual Quality & Characteristic |
| :--- | :--- | :--- | :--- | :--- |
| **Nearest Neighbor** | Classical (CPU) | 0.41 ms | >2400 FPS | Severe pixelation / blocky artifacts |
| **Bilinear** | Classical (CPU) | 1.15 ms | ~870 FPS | Softened transitions, noticeably blurred |
| **Bicubic (Standard Zoom)** | Classical (CPU Baseline) | 2.25 ms | ~440 FPS | Blurry edges, smeared small text |
| **Lanczos-4** | Classical Resampling (CPU) | 1.96 ms | ~510 FPS | Ringing/halo artifacts along high-contrast borders |
| **FSRCNN x2 (CPU AI)** | CPU DNN (OpenCV) | 82.81 ms | ~12.1 FPS | High structural fidelity, sharp reconstructed edges |
| **ESPCN x2 (CPU AI)** | CPU DNN (OpenCV) | 42.57 ms | ~23.5 FPS | Real-time CPU sub-pixel synthesis |
| **RK3588 NPU (ESPCN 3x)** | **Rockchip NPU (6.0 TOPS)** | **34.38 ms** | **~29.1 FPS** | **Tri-Core NPU hardware accelerated, ~0% CPU load** |
| **NPU + Smart Enhancer** | **NPU + CLAHE + Sharpening** | **42.95 ms** | **~23.3 FPS** | **Max clarity, razor-sharp text & PCB traces** |

---

## 📸 Real-World Hardware Snapshots (Orange Pi Box at 4.0x Zoom)

Captured live on an **Orange Pi 5 (RK3588S)** with an active A4Tech FHD 1080P USB camera in V4L2 1080p mode:

#### FSRCNN (4x Smart AI Super-Resolution + Edge Sharpening) vs. Classical Bicubic Zoom
![FSRCNN 4x Neural Zoom vs Bicubic](../../assets/benchmarks/ai_zoom_fsrcnn_x4.jpg)

#### ESPCN (4x Sub-Pixel Super-Resolution + Edge Sharpening) vs. Classical Bicubic Zoom
![ESPCN 4x Sub-Pixel Zoom vs Bicubic](../../assets/benchmarks/ai_zoom_espcn_x4.jpg)

#### FSRCNN (2x) & ESPCN (2x) Comparisons (3.7x Zoom)
| FSRCNN 2x Smart AI Zoom | ESPCN 2x Smart AI Zoom |
| :---: | :---: |
| ![FSRCNN 2x](../../assets/benchmarks/ai_zoom_fsrcnn_x2.jpg) | ![ESPCN 2x](../../assets/benchmarks/ai_zoom_espcn_x2.jpg) |

> 💡 **The Secret to Clarity:** While classical bicubic digital zoom (left) smears and blurs pixel gradients, the **Smart AI** pipeline (right) harnesses sub-pixel convolutional inference on the Rockchip RK3588 Tri-Core NPU coupled with CLAHE micro-contrast and adaptive unsharp masking to reconstruct razor-sharp text and intricate PCB circuit traces.




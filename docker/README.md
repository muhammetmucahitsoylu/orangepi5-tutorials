# Containerized RKNN-Toolkit-Lite2 Environment (Orange Pi 5)

> Run isolated, reproducible Neural Processing Unit (NPU) vision inference inside Docker on the **Orange Pi 5 / 5B / 5 Plus (RK3588 / RK3588S)** with direct hardware device passthrough.

---

## 🧠 How Embedded AI on Orange Pi 5 Works (The Engineering Pipeline)

To deploy deep learning models on embedded edge hardware without thermal throttling or single-digit frame rates, we bypass the CPU and utilize the on-chip **6 TOPS Tri-Core NPU**.

The complete workflow from model development to physical inference:

```text
[ Training / Host PC ]                   [ Orange Pi 5 Hardware ]
+-------------------------+              +-----------------------------------------+
|  PyTorch / YOLOv8 / ONNX|              |  Docker Container: opi5_rknn_workspace  |
|  (Floating Point FP32)  |              |                                         |
+------------+------------+              |  +-----------------------------------+  |
             |                           |  | Python Vision Script (OpenCV)      |  |
   [ RKNN-Toolkit2 ]                     |  | - Resize & Color Conversion (RGB) |  |
   (Model Conversion &                   |  +-----------------+-----------------+  |
    INT8 Quantization)                   |                    |                    |
             |                           |  +-----------------v-----------------+  |
             v                           |  | rknn-toolkit-lite2 (librknnrt.so) |  |
+-------------------------+              |  +-----------------+-----------------+  |
|   model.rknn Binary     |              |                    | DMA Zero-Copy      |
|  (Target: rk3588)       | == Transmit =>  +-----------------v-----------------+  |
+-------------------------+              |  | Kernel Driver: /dev/dri/renderD129|  |
                                         +--+-----------------+-----------------+--+
                                                              |
                                         +--------------------v--------------------+
                                         |  RK3588S Tri-Core NPU (Core 0, 1, 2)    |
                                         |  ⚡ 2.8 ms Latency (~350+ FPS)          |
                                         +-----------------------------------------+
```

1. **Model Source (FP32):** Standard models (PyTorch `.pt`, TensorFlow `.pb`, or ONNX) use 32-bit floating point numbers. Running FP32 on an embedded ARM CPU is slow (~3-5 FPS) and power-hungry.
2. **Quantization & Compilation (RKNN-Toolkit2):** Rockchip's toolkit converts floating point weights into 8-bit integers (**INT8**). The NPU contains specialized hardware integer matrix multipliers that execute billions of operations per watt.
3. **Hardware Deployment (RKNN-Toolkit-Lite2):** On the board, the lightweight runtime loads the `.rknn` binary and maps input tensors directly to NPU memory via DMA buffers.
4. **Kernel Acceleration:** On Linux Kernel 6.1+, the driver communicates via DRM minor node `/dev/dri/renderD129` to wake up all 3 NPU cores simultaneously.

---

## 🚀 Quick Start (1-Step Launch)

From the root of this repository on your Orange Pi 5:

```bash
cd docker
docker compose up -d --build
```

### 1. Hardware Verification Test
Verify that the Linux kernel driver and all 3 NPU hardware cores are accessible inside Docker:
```bash
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_npu.py
```

Expected output:
```text
[*] Initializing runtime with core_mask=NPU_CORE_0_1_2 (Tri-Core 6 TOPS)...
I RKNN: librknnrt version: 2.3.2
I RKNN: RKNN Driver Information, version: 0.9.7
[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!
[PASSED] Physical RK3588 NPU passthrough verified 100% inside Docker!
```

---

## 🔬 Ready-to-Run Vision Demos

### A. Real-Time Image Classification (`test_image_ai.py`)
Classifies images across 1000 categories in **~2.8 milliseconds (~350+ FPS)** on the tri-core NPU. Automatically draws a visual diagnostic HUD on the image and saves `classification_result.jpg`.

```bash
# Preset tests: dog, monkey, plane, apple, fruits, shuttle, kangal
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_image_ai.py dog
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_image_ai.py kangal
```

### B. Object Detection: YOLOv5 vs. YOLOv8
We support both official Anchor-Based (**YOLOv5**) and Anchor-Free DFL (**YOLOv8**) pipelines on the tri-core NPU:

```bash
# 1. Official High-Accuracy YOLOv5 (COCO 330k dataset @ ~31 ms / 32 FPS):
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolo_demo.py bus.jpg
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolo_demo.py kangal.jpg

# 2. Experimental Anchor-Free YOLOv8 (DFL pipeline @ ~22 ms / 45 FPS):
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolov8.py bus.jpg
```

👉 **Detailed Technical Benchmark & Comparison Guide:** Read [`YOLO_COMPARISON.md`](./YOLO_COMPARISON.md) for full latency, accuracy, and silicon-architecture analysis.

---

## 🌐 Visual Inspection via Browser

Because inference runs headless over SSH, you can inspect the annotated images directly in your browser:

1. **Start the background HTTP file server** inside the container:
   ```bash
   docker exec -d -w /workspace/docker opi5_rknn_workspace python3 -m http.server 8000
   ```

2. **Open in your host computer's browser:**
   - Classification output: `http://<ORANGE_PI_IP>:8000/classification_result.jpg`
   - YOLO detection output: `http://<ORANGE_PI_IP>:8000/yolo_result.jpg`
   - File directory: `http://<ORANGE_PI_IP>:8000/`

---

## ⚙️ Docker Architecture & Passthrough Details

* **Direct Device Passthrough:** The `docker-compose.yml` mounts `/dev/dri` and `/dev/dma_heap` into the container namespace.
  * **Kernel 6.1+ (Ubuntu 24.04 Noble / Debian Bookworm):** The Rockchip RKNPU driver (v0.9.7+) registers natively under the Linux Direct Rendering Manager (DRM) subsystem as `/dev/dri/renderD129` (NPU accelerator) and `/dev/dri/renderD128` (Mali GPU).
  * **Legacy Kernel 5.10 (Ubuntu 22.04 Jammy):** Uses `/dev/rknpu`.
* **SoC Device Tree Identification:** The RKNN runtime verifies hardware compatibility by reading `/proc/device-tree/compatible`. Docker masks `/proc` by default, so `privileged: true` and mounting `/proc/device-tree/compatible:/proc/device-tree/compatible:ro` enable seamless hardware detection.
* **Shared Memory (IPC Host):** `ipc: host` enables zero-copy shared memory performance between host Linux camera streams (V4L2/GStreamer) and containerized vision models.
* **Network Mode Host:** `network_mode: host` binds containerized servers (e.g. HTTP, RTSP, Flask) directly to the board's network interfaces without NAT overhead.

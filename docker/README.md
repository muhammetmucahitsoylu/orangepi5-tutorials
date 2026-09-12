# Containerized RKNN-Toolkit-Lite2 Environment (Orange Pi 5)

> Run isolated, reproducible Neural Processing Unit (NPU) inference inside Docker on the **Orange Pi 5 (RK3588S)** with direct hardware device passthrough (`/dev/rknpu`).

---

## 🚀 Quick Start (1-Step Launch)

From the root of this repository on your Orange Pi 5:

```bash
cd docker
docker compose up -d --build
```

### 1. Run the Tri-Core NPU Hardware Verification Test
```bash
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_npu.py
```

Expected output:
```text
[*] Downloading reference NPU model: resnet18_for_rk3588.rknn...
[+] Download complete: 11996108 bytes
--- Initializing Orange Pi 5 RKNN NPU Session ---
[*] Loading RKNN model graph...
[*] Initializing runtime with core_mask=NPU_CORE_0_1_2 (Tri-Core 6 TOPS)...
I RKNN: [16:31:02.519] RKNN Runtime Information, librknnrt version: 2.3.2
I RKNN: [16:31:02.519] RKNN Driver Information, version: 0.9.7
I RKNN: [16:31:02.520] RKNN Model Information, target: RKNPU v2, target platform: rk3588
[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!
[PASSED] Physical RK3588 NPU passthrough verified 100% inside Docker!
```

### 2. Attach to the Container Shell
```bash
docker exec -it opi5_rknn_workspace bash
```

---

## ⚙️ Architecture & Passthrough Details

* **Direct Device Passthrough:** The `docker-compose.yml` mounts `/dev/dri` and `/dev/dma_heap` into the container namespace.
  * **Kernel 6.1 (Ubuntu 24.04 Noble):** The Rockchip RKNPU driver (v0.9.7+) registers natively under the Linux Direct Rendering Manager (DRM) subsystem as `/dev/dri/renderD129` (accelerator) and `renderD128` (GPU).
  * **Legacy Kernel 5.10 (Ubuntu 22.04 Jammy):** If running legacy BSP images with the dedicated `/dev/rknpu` character node, you can also add `/dev/rknpu:/dev/rknpu` to `devices:`.
* **SoC Device Tree Identification:** The RKNN runtime verifies the hardware SoC model by reading `/proc/device-tree/compatible` (which outputs `rockchip,rk3588s-orangepi-5 rockchip,rk3588`). Docker masks `/proc` by default, so `privileged: true` and `- /proc/device-tree/compatible:/proc/device-tree/compatible:ro` are configured to allow automatic hardware detection.
* **NPU Runtime Library (`librknnrt.so`):** The container automatically downloads and provisions Rockchip's official `librknnrt.so` v2.3.2 into `/usr/lib/librknnrt.so`, guaranteeing zero dependency mismatch across host OS distributions.
* **Host Volume Sync:** The parent repository directory (`../`) is mounted into `/workspace`. Any code, benchmarks, or model files modified inside the container persist on your host NVMe SSD.
* **IPC Host Mode:** Enabled to ensure zero-copy shared memory performance between host Linux camera streams (V4L2/GStreamer) and containerized computer vision models.

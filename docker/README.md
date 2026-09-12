# Containerized RKNN-Toolkit-Lite2 Environment (Orange Pi 5)

> Run isolated, reproducible Neural Processing Unit (NPU) inference inside Docker on the **Orange Pi 5 (RK3588S)** with direct hardware device passthrough (`/dev/rknpu`).

---

## 🚀 Quick Start (1-Step Launch)

From the root of this repository on your Orange Pi 5:

```bash
cd docker
docker compose up -d --build
```

### 1. Attach to the Container Shell
```bash
docker exec -it opi5_rknn_workspace bash
```

### 2. Verify Hardware NPU Access Inside Container
```bash
python3 -c "from rknnlite.api import RKNNLite; rknn = RKNNLite(); print('NPU Hardware Successfully Bound!')"
```

---

## ⚙️ Architecture & Passthrough Details

* **Direct Device Passthrough:** The `docker-compose.yml` mounts `/dev/dri` and `/dev/dma_heap` into the container namespace.
  * **Kernel 6.1 (Ubuntu 24.04 Noble):** The Rockchip RKNPU driver (v0.9.7+) registers natively under the Linux Direct Rendering Manager (DRM) subsystem as `/dev/dri/renderD129`. Mounting `/dev/dri` directly exposes the 6 TOPS NPU to the container without relying on legacy character devices.
  * **Legacy Kernel 5.10 (Ubuntu 22.04 Jammy):** If running legacy BSP images with the dedicated `/dev/rknpu` character node, you can also add `/dev/rknpu:/dev/rknpu` to `devices:`.
* **Host Volume Sync:** The parent repository directory (`../`) is mounted into `/workspace`. Any code, benchmarks, or model files modified inside the container persist on your host NVMe SSD.
* **IPC Host Mode:** Enabled to ensure zero-copy shared memory performance between host Linux camera streams (V4L2/GStreamer) and containerized computer vision models.

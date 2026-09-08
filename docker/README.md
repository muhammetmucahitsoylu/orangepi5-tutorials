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

* **Direct Device Passthrough:** The `docker-compose.yml` mounts `/dev/rknpu` and `/dev/mali0` directly into the container namespace.
* **Host Volume Sync:** The parent repository directory (`../`) is mounted into `/workspace`. Any code or model files modified inside the container persist on your host NVMe SSD.
* **IPC Host Mode:** Enabled to ensure zero-copy shared memory performance between host Linux camera streams (V4L2/GStreamer) and containerized computer vision models.

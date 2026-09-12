# **Orange Pi 5 (RK3588S) NPU Activation and RKNN Runtime Setup Guide**

> 🛡️ **Verified on Hardware:** All steps and code in this project have been physically tested and verified on **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)**.

This guide provides a step-by-step procedure to initialize the 3-core **6 TOPS Neural Processing Unit (NPU)** on the Rockchip RK3588S, verify kernel driver compatibility, configure Python environments, and troubleshoot version-mismatch exceptions.

---

## **1. Why Standard PyTorch Cannot Target the NPU**

* **Common Pitfall:** Running `pip install torch` on ARM Linux does NOT route computation to the RK3588 NPU. Standard PyTorch only understands x86/ARM CPUs and Nvidia CUDA GPUs.
* **Rockchip Edge AI Workflow:**
  1. Train or export models (YOLO, ResNet, MobileNet) to `.onnx`.
  2. Quantize and compile the model into Rockchip's proprietary **`.rknn`** format using `rknn-toolkit2` on a PC.
  3. Deploy using **`rknn-toolkit-lite2`** on the Orange Pi 5 to execute directly on the 6 TOPS NPU hardware cores with sub-millisecond latency.

---

## **2. Step 1: Verify NPU Kernel Driver Compatibility**

Inspect NPU driver initialization in kernel logs:

```bash
dmesg | grep -i rknpu
```
*Expected Output:* `RKNPU: Driver version: 0.9.x` or newer.

> [!IMPORTANT]
> **CRITICAL VERSION PINNING & COMPATIBILITY RULE:**  
> In the Rockchip ecosystem, your model compiler (`rknn-toolkit2`), board runtime (`librknnrt.so`), and kernel driver (`rknpu.ko`) **must remain strictly pinned to the same version family**:
> * **Verified Baseline for this Repository:** RKNPU Kernel Driver: **`v0.9.8`**, Runtime & Toolkit: **`v2.3.2`**.
> * Inspect driver version directly: `cat /sys/kernel/debug/rknpu/version`
> * For full version matrices and resolving runtime mismatch errors, see [docs/COMPATIBILITY.md](../../docs/COMPATIBILITY.md).

Verify NPU clock governor:
```bash
cat /sys/class/devfreq/*npu*/cur_freq
```
*Expected Output:* `1000000000` (Confirms 1.0 GHz peak clock frequency).

---

## **3. Step 2: Provision C Runtime Shared Library (`librknnrt.so`)**

Applications require the proprietary hardware runtime library in system library paths:

```bash
# Method 1: Direct and Fast Download (Recommended)
sudo curl -sL -o /usr/lib/librknnrt.so https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig

# Method 2: Via Git Repository Clone (Alternative)
cd /tmp
git clone --depth 1 https://github.com/rockchip-linux/rknpu2.git
sudo cp rknpu2/runtime/RK3588/Linux/librknn_api/aarch64/librknnrt.so /usr/lib/
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig
rm -rf /tmp/rknpu2
```

---

## **4. Step 3: Configure Python & Install Matching RKNN-Lite Wheel**

Check your installed Python version:
```bash
python3 --version
```

### **Create Virtual Environment:**
```bash
mkdir -p ~/projects/npu-env && cd ~/projects/npu-env
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install numpy opencv-python pillow
```

### **Install Version-Specific Wheel:**
* **For Python 3.10 (Ubuntu 22.04 LTS):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```
* **For Python 3.11 (Debian Bookworm):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```
* **For Python 3.12 (Ubuntu 24.04):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```

---

## **5. Step 4: "Hello NPU" — Tri-Core Hardware Initialization Test**

> [!NOTE]
> In RKNN-Toolkit-Lite2 architecture, `rknn.init_runtime()` strictly requires loading a compiled `.rknn` model into memory (`load_rknn`) before opening a hardware session. The script below downloads an official reference model and activates all 3 cores (6 TOPS).

Create `test_npu.py`:

```python
import os
import urllib.request
import subprocess
from rknnlite.api import RKNNLite

MODEL_FILE = "resnet18_for_rk3588.rknn"
MODEL_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/resnet18_for_rk3588.rknn"

# 1. Ensure sample RKNN model exists
if not os.path.exists(MODEL_FILE):
    print(f"[*] Downloading reference NPU model: {MODEL_FILE}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)

print("--- Initializing Orange Pi 5 RKNN NPU ---")
rknn = RKNNLite()

# 2. Load model graph
ret = rknn.load_rknn(MODEL_FILE)
if ret != 0:
    print(f"[ERROR] Failed to load model! Code: {ret}")
    exit(ret)

# 3. Engage all 3 NPU cores (Core 0, 1, 2) for full 6 TOPS throughput:
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!")
    print("\n--- Driver & API Version Information ---")
    rknn.get_sdk_version()
    try:
        telemetry = subprocess.check_output("cat /sys/kernel/debug/rknpu/load 2>/dev/null || true", shell=True).decode()
        if telemetry.strip():
            print("\n--- Real-Time NPU Core Telemetry ---")
            print(telemetry.strip())
    except Exception:
        pass
else:
    print(f"[ERROR] Failed to initialize NPU! Return code: {ret}")

rknn.release()
```

### **Run the Test:**
```bash
# Execute within activated virtual environment:
python3 test_npu.py
```

**Expected Output:**
```text
--- Initializing Orange Pi 5 RKNN NPU ---
[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!

--- Driver & API Version Information ---
==============================================
RKNN VERSION:
  API: 2.3.2
  DRV: 0.9.7 (or 0.9.8)
==============================================
```

---

## **6. Alternative: Isolated Zero-Dependency Setup via Docker**

To completely bypass Python version pinning conflicts and keep your host system pristine, run the pre-configured isolated Docker environment:

```bash
cd docker
docker compose up -d --build
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_npu.py
```

*This container maps `/dev/dri`, `/dev/dma_heap`, and `/proc/device-tree/compatible` directly into an Ubuntu 22.04 + Python 3.10 runtime with full tri-core hardware acceleration.*

---

## **7. Troubleshooting & Diagnostics Matrix**

| Error / Symptom | Root Cause | Verified Solution |
| :--- | :--- | :--- |
| `rknn_init, RKNN driver version(0.8.2) is not match with runtime version(2.x.x)` | Running legacy RKNPU kernel module (v0.8) with modern RKNN v2 runtime. | Upgrade kernel via `sudo apt update && sudo apt upgrade` or install Rockchip BSP 5.10.110+ image. |
| `ImportError: librknnrt.so: cannot open shared object file` | Missing shared object in system library path. | Copy `librknnrt.so` to `/usr/lib/` and run `sudo ldconfig`. |
| `is not a supported wheel on this platform` | Python version mismatch (e.g. attempting to install cp310 on Python 3.12). | Run `python3 --version` and install the exact matching `cp310`, `cp311`, or `cp312` wheel. |
| `/dev/rknpu not found (Kernel 6.1)` | Kernel 6.1 (Ubuntu 24.04) initializes RKNPU as a DRM minor render node (`/dev/dri/renderD129`) instead of a legacy character device. | Expected behavior. RKNN v2.3.2+ automatically binds to `/dev/dri/renderD129`. Map `/dev/dri` and `/dev/dma_heap` in Docker or permissions. |
| `Permission denied: /dev/rknpu` or `/dev/dri/renderD129` | Non-root user lacks access rights to device node. | Add user to video/render groups: `sudo usermod -aG video,render $USER` and log back in. |
| `It is detected that some necessary files are missing in the container` | Container lacks `/proc/device-tree/compatible` or `librknnrt.so`. | Configure `privileged: true` and mount `-v /proc/device-tree/compatible:/proc/device-tree/compatible:ro`. |

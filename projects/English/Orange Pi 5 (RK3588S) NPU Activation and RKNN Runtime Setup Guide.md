# **Orange Pi 5 (RK3588S) NPU Activation and RKNN Runtime Setup Guide**

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
> **CRITICAL VERSION COMPATIBILITY RULE:**  
> If the kernel reports `Driver version: 0.8.x`, you are on an outdated BSP kernel that is **incompatible** with RKNN-Toolkit2 v2.x runtimes (raising `Driver version mismatch` errors). Upgrade your system packages first: `sudo apt update && sudo apt upgrade -y`.

Verify NPU clock governor:
```bash
cat /sys/class/devfreq/*npu*/cur_freq
```
*Expected Output:* `1000000000` (Confirms 1.0 GHz peak clock frequency).

---

## **3. Step 2: Provision C Runtime Shared Library (`librknnrt.so`)**

Applications require the proprietary hardware runtime library in system library paths:

```bash
# 1. Clone official Rockchip rknpu2 repository:
cd /tmp
git clone --depth 1 https://github.com/rockchip-linux/rknpu2.git

# 2. Copy 64-bit ARM library into system directory:
sudo cp rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so /usr/lib/

# 3. Configure permissions and refresh linker cache:
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig

# 4. Clean up:
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
  pip install https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.0/rknn_toolkit_lite2-2.3.0-cp310-cp310-linux_aarch64.whl
  ```
* **For Python 3.11 (Debian Bookworm):**
  ```bash
  pip install https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.0/rknn_toolkit_lite2-2.3.0-cp311-cp311-linux_aarch64.whl
  ```
* **For Python 3.12 (Ubuntu 24.04):**
  ```bash
  pip install https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.0/rknn_toolkit_lite2-2.3.0-cp312-cp312-linux_aarch64.whl
  ```

---

## **5. Step 4: "Hello NPU" — Tri-Core Hardware Initialization Test**

Create `test_npu.py`:

```python
from rknnlite.api import RKNNLite
import subprocess

print("--- Initializing Orange Pi 5 RKNN NPU ---")

rknn = RKNNLite()

# Engage all 3 NPU cores (Core 0, 1, 2) for full 6 TOPS throughput:
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[SUCCESS] All 3 NPU cores initialized successfully!")
    try:
        telemetry = subprocess.check_output("cat /sys/kernel/debug/rknpu/load", shell=True).decode()
        print("\n--- Real-Time NPU Core Telemetry ---")
        print(telemetry.strip())
    except Exception:
        print("[!] Note: Reading debugfs telemetry requires root privileges.")
else:
    print(f"[ERROR] Failed to initialize NPU! Return code: {ret}")

rknn.release()
```

Run test:
```bash
sudo $(which python3) test_npu.py
```

**Expected Output:**
```text
--- Initializing Orange Pi 5 RKNN NPU ---
[SUCCESS] All 3 NPU cores initialized successfully!

--- Real-Time NPU Core Telemetry ---
NPU load:  Core0: 0%, Core1: 0%, Core2: 0%
```

---

## **6. Troubleshooting & Diagnostics Matrix**

| Error / Symptom | Root Cause | Verified Solution |
| :--- | :--- | :--- |
| `rknn_init, RKNN driver version(0.8.2) is not match with runtime version(2.x.x)` | Running legacy RKNPU kernel module (v0.8) with modern RKNN v2 runtime. | Upgrade kernel via `sudo apt update && sudo apt upgrade` or install Rockchip BSP 5.10.110+ image. |
| `ImportError: librknnrt.so: cannot open shared object file` | Missing shared object in system library path. | Copy `librknnrt.so` to `/usr/lib/` and run `sudo ldconfig`. |
| `is not a supported wheel on this platform` | Python version mismatch (e.g. attempting to install cp310 on Python 3.12). | Run `python3 --version` and install the exact matching `cp310`, `cp311`, or `cp312` wheel. |
| `Permission denied: /dev/rknpu` | Non-root user lacks access rights to device node. | Execute `sudo chmod 666 /dev/rknpu*` or add user to video/dialout group. |

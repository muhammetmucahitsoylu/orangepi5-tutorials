# **Orange Pi 5 (RK3588S) NPU Activation and RKNN Runtime Setup Guide**

This guide explains how to initialize the onboard 3-core **6 TOPS** Neural Processing Unit (NPU) on the Rockchip RK3588S SoC, verify kernel driver telemetry, and configure the Python runtime environment for accelerating machine learning inference.

---

## **1. RK3588 NPU Architecture: Why Standard PyTorch Won't Work**

* **Common Misconception:** Beginners often assume running `pip install torch` will automatically utilize the NPU. Standard PyTorch only recognizes x86/ARM CPUs or Nvidia CUDA GPUs; it cannot interface with Rockchip's proprietary NPU silicon.
* **The Rockchip Edge AI Pipeline:**
  1. Train your neural network (YOLO, ResNet, MobileNet) on your PC or export it as standard `.onnx`.
  2. Quantize and compile the model into Rockchip's **`.rknn`** format using the desktop compilation toolkit.
  3. Deploy the lightweight **RKNN-Toolkit-Lite2** runtime on the Orange Pi 5 to stream input tensors directly onto the 6 TOPS NPU cores with low-millisecond latency.

---

## **2. Step 1: Verify Kernel NPU Driver Status**

On official Ubuntu 24.04 (Linux 6.1-rockchip) releases, the NPU driver (`rknpu`) is integrated into the kernel tree:

```bash
# 1. Verify that the kernel NPU driver is loaded:
dmesg | grep -i rknpu
```
*Expected Output:* `RKNPU: Driver version: 0.9.x` or higher.

```bash
# 2. Check NPU clock frequency:
cat /sys/class/devfreq/fdab0000.npu/cur_freq
```
*Expected Output:* `1000000000` (confirms the NPU core is clocked at its 1.0 GHz maximum).

---

## **3. Step 2: Install the System C Runtime Library (`librknnrt.so`)**

The user-space runtime library must be installed so that C++ and Python applications can interface with the kernel NPU device:

```bash
# 1. Clone the official Rockchip rknpu2 repository:
cd /tmp
git clone --depth 1 https://github.com/rockchip-linux/rknpu2.git

# 2. Install the 64-bit ARM runtime library to your system library path:
sudo cp rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so /usr/lib/

# 3. Apply executable permissions and refresh dynamic linker cache:
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig

# 4. Clean up temporary files:
rm -rf /tmp/rknpu2
```

---

## **4. Step 3: Install RKNN-Toolkit-Lite2 for Python**

The lightweight client runtime (`rknn-toolkit-lite2`) is deployed directly on edge devices like the Orange Pi 5:

1. Navigate to your project folder and activate your virtual environment:
   ```bash
   cd ~/projects/my-first-project
   source venv/bin/activate
   ```

2. Install core math and vision dependencies:
   ```bash
   pip install --upgrade pip
   pip install numpy opencv-python pillow
   ```

3. Install the official pre-built wheel matching your Python version (Python 3.10 or 3.11):
   ```bash
   # For Python 3.10 (Ubuntu 22.04 LTS):
   pip install https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.0/rknn_toolkit_lite2-2.3.0-cp310-cp310-linux_aarch64.whl

   # OR directly from PyPI on modern Ubuntu versions:
   pip install rknn-toolkit-lite2
   ```

---

## **5. Step 4: "Hello NPU" — Waking Up All 3 Hardware Cores**

Validate your environment and confirm that all 3 hardware cores respond to initialization:

Create `src/test_npu.py`:

```python
from rknnlite.api import RKNNLite
import subprocess

print("--- Initializing Orange Pi 5 RKNN NPU ---")

# Instantiate runtime client
rknn = RKNNLite()

# Configure NPU to engage all three independent cores simultaneously
# RKNNLite.NPU_CORE_0_1_2 activates the full 6 TOPS computing capacity
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[SUCCESS] All 3 NPU Cores initialized successfully at hardware level!")
    
    # Read active kernel load telemetry
    try:
        telemetry = subprocess.check_output("sudo cat /sys/kernel/debug/rknpu/load", shell=True).decode()
        print("\n--- Real-Time NPU Hardware Status ---")
        print(telemetry.strip())
    except Exception as e:
        print("Could not read telemetry (requires root privileges).")
else:
    print(f"[ERROR] Failed to initialize NPU! Error code: {ret}")

rknn.release()
```

### **Run Verification:**
```bash
sudo $(which python3) src/test_npu.py
```

*Expected Terminal Output:*
```text
--- Initializing Orange Pi 5 RKNN NPU ---
[SUCCESS] All 3 NPU Cores initialized successfully at hardware level!

--- Real-Time NPU Hardware Status ---
NPU load:  Core0: 0%, Core1: 0%, Core2: 0%
```

---

## **6. Conclusion & Next Steps**

Your Orange Pi 5's dedicated 6 TOPS hardware accelerator is now fully awakened and ready for inference workloads.

In upcoming tutorials, you can:
* Quantize and convert **YOLOv8** object detection models into `.rknn` format.
* Execute real-time camera inference at **60+ FPS** while maintaining sub-15% CPU load.

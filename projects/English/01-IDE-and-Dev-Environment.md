# **Orange Pi 5 (RK3588S) IDE and Development Environment Setup for Developers**

> 🛡️ **Verified on Hardware:** All steps and code in this project have been physically tested and verified on **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)**.

This guide provides a step-by-step walkthrough for software developers to build a professional development workflow for C/C++, Python, and Edge AI projects on the Orange Pi 5 from scratch.

---

## **1. Development Workflow Philosophy: Where Should You Code?**

When developing on single-board computers (SBCs), there are two primary approaches:

* **The Inefficient Approach:** Attaching a dedicated monitor, keyboard, and mouse to the Orange Pi 5 and running a resource-heavy GUI IDE (such as desktop VS Code or PyCharm) locally on the board. This wastes precious RAM and CPU cores that should be reserved for compilation, testing, and inference.
* **The Professional Approach (Recommended):** Running Visual Studio Code on your laptop/workstation and connecting directly to the Orange Pi 5 via **VS Code Remote - SSH**. You edit code smoothly on your desktop while files, compilers, Python interpreters, and terminal sessions run natively on the Orange Pi 5 hardware.

---

## **2. Method 1: VS Code Remote - SSH (Industry Standard)**

### **Step 1: Laptop Preparation**
1. Open **Visual Studio Code** on your workstation.
2. Click the **Extensions** icon on the left sidebar (or press `Ctrl + Shift + X`).
3. Search for **Remote - SSH** (by Microsoft) and install it.

### **Step 2: Connect to the Orange Pi 5**
1. Press `F1` (or `Ctrl + Shift + P`) and type `Remote-SSH: Connect to Host...`.
2. Enter your SSH connection string:
   ```text
   your_username@ORANGE_PI_IP
   ```
3. Enter your user password when prompted. The bottom-left corner will display `SSH: ORANGE_PI_IP` in green.
4. Go to **File -> Open Folder** and open your project directory (e.g., `/home/your_username/projects`).

*Now, any terminal command or file you edit in VS Code runs natively on the Orange Pi 5.*

---

## **3. Method 2: Code-Server (Browser-Based VS Code)**

If you want to write code from any device (tablet, restricted work laptop) using only a web browser, deploy **Code-Server** on the board:

```bash
# 1. Install Code-Server using the official automated installer:
curl -fsSL https://code-server.dev/install.sh | sh

# 2. Enable and launch the systemd service for your user:
sudo systemctl enable --now code-server@$USER

# 3. Retrieve your generated access password:
cat ~/.config/code-server/config.yaml | grep password
```

*Open `http://ORANGE_PI_IP:8080` in your web browser and enter the password to access a full VS Code IDE in your browser.*

---

## **4. Step 3: Install Essential Build & Developer Toolchains**

Install the necessary compilers, header files, and build systems for C/C++ and Python:

```bash
sudo apt update && sudo apt install -y \
  build-essential \
  cmake \
  git \
  ninja-build \
  pkg-config \
  python3-dev \
  python3-pip \
  python3-venv \
  libopencv-dev
```

---

## **5. Step 4: Standard Project Directory Layout & Python venv**

To prevent polluting the system package tree and maintain reproducible builds, always isolate your project using a Python virtual environment (`venv`):

```bash
# 1. Create a root workspace and your first project folder:
mkdir -p ~/projects/my-first-project && cd ~/projects/my-first-project

# 2. Create the standard directory structure:
mkdir -p src models data

# 3. Initialize an isolated virtual environment:
python3 -m venv venv

# 4. Activate the virtual environment:
source venv/bin/activate
```

### **Standard Project Architecture**
```text
my-first-project/
├── venv/                 # Isolated Python virtual environment
├── src/                  # Application source code (.py, .cpp)
│   └── main.py
├── models/               # Model weights (.onnx, .rknn)
├── data/                 # Sample inputs, test images
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## **6. Quick Verification: Hardware Inspection Script**

Verify your workspace by creating `src/main.py`:

```python
import platform
import os

print("--- Orange Pi 5 Hardware Verification ---")
print(f"Architecture: {platform.machine()}")
print(f"Logical CPU Cores: {os.cpu_count()}")

# NPU status check
npu_freq_path = "/sys/class/devfreq/fdab0000.npu/cur_freq"
if os.path.exists(npu_freq_path):
    with open(npu_freq_path, "r") as f:
        freq = int(f.read().strip()) / 1_000_000
    print(f"NPU Hardware Core: Active ({freq:.0f} MHz)")
else:
    print("NPU Hardware Core: Not detected (Ensure Rockchip BSP kernel is installed)")
```

Execute the script:
```bash
python3 src/main.py
```

*Your development environment is now fully established. You can now build high-performance C++ and Python applications targeting the CPU, GPU, and onboard NPU.*

# Hardware & Software Version Compatibility Matrix (Pinning Reference)

> **Living Engineering Baseline:** This document establishes the exact, verified software versions, kernel branches, and driver dependencies validated across all guides and code repositories in `muhammetmucahitsoylu/orangepi5-tutorials`.

---

## 1. Validated Board & Operating System Matrix

| Component | Verified Reference Version | Secondary Supported Version | Known Caveats & Deprecated |
| :--- | :--- | :--- | :--- |
| **Reference Hardware** | **Orange Pi 5 (RK3588S) V1.3.2** | Orange Pi 5 (V1.1 / V1.2), Orange Pi 5 Plus | Orange Pi 5B lacks M.2 NVMe slot (eMMC only). |
| **Primary OS Distribution** | **Ubuntu 22.04.5 LTS (Jammy Jellyfish)** | Ubuntu 24.04 LTS (Noble Numbat) | Debian 11 (Bullseye) has outdated glibc/pip dependencies. |
| **Linux Kernel Branch** | **Rockchip BSP `5.10.160-rockchip-rk3588`** (Joshua Riek / Official BSP) | Rockchip BSP `6.1.x` | Mainline Linux (6.8+) lacks in-tree RKNPU/VPU drivers (CPU fallback only). |
| **Desktop Environment** | **XFCE4 / Minimal Server (Headless)** | GNOME (Ubuntu Desktop) | Wayland native can cause screen-recording and X11 forwarding glitches. |
| **Python Toolchain** | **Python 3.10.12** | Python 3.12 (Ubuntu 24.04) | Python 3.8 is deprecated by upstream Rockchip SDKs. |

---

## 2. Rockchip NPU / RKNN Software Stack Compatibility Matrix

In the Rockchip RK3588 ecosystem, **model files (`.rknn`), PC compiler (`rknn-toolkit2`), board runtime (`librknnrt.so`), and the Linux kernel driver (`rknpu.ko`) must remain strictly version-aligned**.

### Official Version Mapping:

| RKNPU Kernel Driver (`/sys/kernel/debug/rknpu/version`) | Board Runtime Library (`librknnrt.so`) | Host PC Compiler (`rknn-toolkit2`) | Board Python Engine (`rknn-toolkit-lite2`) | Supported `.rknn` Model Format | Repo Validation Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **`v0.9.8`** (Recommended) | **`v2.3.0` / `v2.3.2`** | **`v2.3.0` / `v2.3.2`** | **`v2.3.2`** | **RKNN v2.3 Specification** | 🟢 **Active Repository Baseline** |
| `v0.9.6` | `v1.6.0` | `v1.6.0` | `v1.6.0` | RKNN v1.6 Specification | 🟡 Legacy Stable (Requires v1.6 models) |
| `v0.9.3` | `v1.5.2` | `v1.5.2` | `v1.5.2` | RKNN v1.5 Specification | 🔴 Deprecated (Incompatible with v2.x models) |

### RKLLM (Large Language Models on NPU) Version Mapping:

| Component | Target Platform | Verified Pinned Version | Package Source |
| :--- | :---: | :---: | :--- |
| **Host RKLLM Toolkit** | x86_64 Linux PC | `v1.1.4` / `v1.3.0` | `airockchip/rknn-llm` (`rkllm-toolkit/packages`) |
| **Board C++ Runtime** | aarch64 Orange Pi 5 | `librkllmrt.so v1.1.4+` | `/usr/lib/librkllmrt.so` |
| **Inference CLI** | aarch64 Orange Pi 5 | `llm_demo` (C++ Native) | `rknn-llm/examples/rkllm_api_demo` |
| **Minimum RKNPU Driver**| Kernel Space | **`>= v0.9.6`** (`v0.9.8` optimal) | Rockchip BSP 5.10 / 6.1 |
| **Quantization Scheme** | Hardware NPU | **W4A16 / W8A8** | 4-bit weight, 16-bit activation |

---

## 3. Five-Second Self-Diagnostics Command Cheatsheet

Before deploying or debugging any NPU/AI pipeline, run these 4 commands on your Orange Pi 5 terminal to verify your stack alignment:

### 1. Check Kernel Driver Version:
```bash
cat /sys/kernel/debug/rknpu/version
# Verified Output: RKNPU driver: v0.9.8 (or higher)
```

### 2. Check Board Userspace Runtime Version:
```bash
strings /usr/lib/librknnrt.so | grep -i "librknnrt version" | head -n 1
# Verified Output: librknnrt version: 2.3.2 (or matching repo baseline)
```

### 3. Check Tri-Core Hardware Load:
```bash
sudo cat /sys/kernel/debug/rknpu/load
# Expected Output: Core0: 0%, Core1: 0%, Core2: 0% (Ready for workload)
```

### 4. Check NPU Operational Frequency:
```bash
cat /sys/class/devfreq/fdab0000.npu/cur_freq
# Expected Output: 1000000000 (1.0 GHz maximum hardware frequency)
```

---

## 4. Troubleshooting Version Mismatch Errors

### Error 1: `RKNN_ERR_MODEL_VERSION_MISMATCH (-14)`
* **Root Cause:** The `.rknn` model file was generated on PC with `rknn-toolkit2 v2.x`, but your Orange Pi 5 board is running an older `librknnrt.so v1.x` runtime (or vice versa).
* **Definitive Fix:** Update the board's runtime library:
  ```bash
  sudo wget -O /usr/lib/librknnrt.so https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/librknnrt.so
  sudo ldconfig
  ```

### Error 2: `rknpu driver version: 0.9.x is too low`
* **Root Cause:** Your Linux kernel is running an ancient BSP driver (`< 0.9.6`) while `rknn-toolkit-lite2 v2.x` expects at least driver `0.9.8`.
* **Definitive Fix:** Upgrade your kernel to Joshua Riek's latest release or update kernel packages:
  ```bash
  sudo apt update && sudo apt install -y linux-image-legacy-rk3588
  sudo reboot
  ```

### Error 3: `ImportError: libxslt.so.1 / libgomp.so.1: cannot open shared object file`
* **Root Cause:** Missing C system shared dependencies required by the pre-compiled Python wheels.
* **Definitive Fix:** Install native dependencies:
  ```bash
  sudo apt update && sudo apt install -y libxslt1-dev zlib1g-dev libgomp1 libgl1
  ```

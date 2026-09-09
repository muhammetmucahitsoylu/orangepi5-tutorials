# 🚀 Orange Pi 5 Hardware-Verified Release (v2.0.0)

This major release marks the **100% physical hardware verification** across all 18 guides and 26 projects on an **Orange Pi 5 (RK3588S, 8GB RAM, 512GB NVMe SSD)** running **Ubuntu 24.04.1 LTS (Noble) with Rockchip BSP Kernel 6.1.0-1025**.

---

## 🤖 Pre-Compiled & Quantized AI Model Assets (.rknn / .rkllm)

Skip the host PC conversion pipeline (`rknn-toolkit2` / `rkllm-toolkit`) and download pre-quantized models directly to your Orange Pi 5:

| Model | Format / Precision | Target Hardware | Direct Download Link | Source & License |
| :--- | :---: | :---: | :--- | :--- |
| **ResNet-18 (Classification)** | `.rknn` (INT8/FP16) | RK3588 NPU (3 Cores) | [Direct Download `resnet18_for_rk3588.rknn`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/resnet18_for_rk3588.rknn) | Apache 2.0 (Rockchip Model Zoo) |
| **YOLOv8 COCO Labels** | `.txt` (80 Classes) | Host & Target | [Direct Download `coco_80_labels_list.txt`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/coco_80_labels_list.txt) | AGPL-3.0 / Ultralytics COCO |
| **Qwen-1.8B Chat** | `.rkllm` (W4A16) | RK3588 NPU (3 Cores) | [Direct Download `qwen-chat-1_8B.rkllm`](https://huggingface.co/Pelochus/qwen-1_8B-rk3588/resolve/main/qwen-chat-1_8B.rkllm) | Apache 2.0 / Qwen Open |
| **Qwen2-1.5B Chat** | `.rkllm` (W4A16) | RK3588 NPU (3 Cores) | [Direct Download `qwen2-1.8B-rk3588.rkllm`](https://huggingface.co/Pelochus/qwen2-1_5B-rk3588/resolve/main/qwen2-1.8B-rk3588.rkllm) | Apache 2.0 / Qwen Open |

```bash
# 📥 Quick Terminal Download (Run directly on Orange Pi 5):
mkdir -p ~/models && cd ~/models
wget https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/resnet18_for_rk3588.rknn
wget https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/coco_80_labels_list.txt
```

---

## ⚡ Live Hardware Benchmark Highlights

* **Storage:** M.2 NVMe direct sequential write at **416 MB/s** (99% of theoretical PCIe 2.0 x1 limit).
* **Thermals:** 8-core CPU prime compute under `stress-ng` reached **55.4°C** with zero thermal throttling.
* **NPU Telemetry:** 3-core NPU active at **1.0 GHz** with `librknnrt.so v2.3.2` and driver `v0.9.7`.
* **Robotics:** Live DDS publisher/subscriber communication verified under **ROS 2 Jazzy Jalisco**.
* **Kernel Driver:** Linux Out-of-Tree character device driver compiled against `linux-headers-6.1.0-1025-rockchip`.

---

## 🛠️ What's Changed
* **100% CI/CD Pass:** Automated GitHub Actions pipeline verifying ARM64 cross-compilation (`aarch64-linux-gnu-g++`), ShellCheck (0 warnings), and Lychee markdown links.
* **Vector Pinout:** Added SVG 26-pin header diagram and UART 1.5M baud wiring guide in `docs/GPIO_PINOUT.md`.
* **Mainline Linux Roadmap:** Added upstream 6.10+ Panthor DRM GPU and mainline NPU roadmap in `docs/COMPATIBILITY.md`.
* **Dual-Licensing:** MIT License for source code and CC BY-SA 4.0 for documentation.

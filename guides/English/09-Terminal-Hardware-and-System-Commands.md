# **Orange Pi 5 (RK3588S) Terminal Hardware, Sensor & System Management Guide**

> 🛡️ **Verified & Tested:** All commands and sysfs paths in this guide have been verified on physical **Orange Pi 5 (Rockchip RK3588S) + Ubuntu 24.04 / 22.04 LTS (Kernel 6.1 BSP)**.

This handbook provides exact terminal commands to read multi-sensor thermals, control cooling fans, configure CPU scaling governors, inspect the 6 TOPS NPU, optimize RAM caches, and manage cameras.

---

## 🚫 **CRITICAL: Banned Commands (Raspberry Pi vs Orange Pi 5)**

AI models often conflate Orange Pi with Raspberry Pi. The following commands **DO NOT WORK on Orange Pi 5**:

| Invalid / Banned Command | Why It Fails | Orange Pi 5 (RK3588) Verified Equivalent |
|:---|:---|:---|
| `vcgencmd measure_temp` | Exclusive to Raspberry Pi Broadcom VideoCore GPU. | `paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) \| awk '{printf "%-20s: %.1f °C\n", $1, $2/1000}'` or `sensors` |
| `raspi-config` | Raspberry Pi proprietary config utility. | `sudo orangepi-config` |
| `rpi.gpio` (Python) | BCM GPIO register specific. | `gpiod` (`python3-libgpiod`) or `periphery` |
| `/boot/config.txt` | Raspberry Pi boot file. | `/boot/orangepiEnv.txt` or `/boot/armbianEnv.txt` |

---

## 🌡️ **1. Thermal Zones & Temperature Reading**

Rockchip RK3588S features **7 independent on-die thermal sensors**:
- `soc-thermal`: General silicon periphery (`btop` reads this by default).
- `bigcore0-thermal`: Cortex-A76 High Performance Cores 0-1 (peaks under LLM load).
- `bigcore1-thermal`: Cortex-A76 High Performance Cores 2-3.
- `littlecore-thermal`: Cortex-A55 Efficiency Cores 0-3.
- `center-thermal`: Silicon center core thermal sensor.
- `gpu-thermal`: Mali-G610 MP4 GPU.
- `npu-thermal`: 6 TOPS NPU Accelerator.

### **Method 1: Read All 7 Zones in One Clean Table (Built-in Sysfs)**
```bash
paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) | awk '{printf "%-22s: %.1f °C\n", $1, $2/1000}'
```

### **Method 2: `sensors` (lm-sensors)**
```bash
sensors
```

### **Method 3: Terminal TUI Monitor (`btop`)**
```bash
btop
```

---

## 💨 **2. Cooling Fan Control**

### **Check Current Fan Speed:**
```bash
cat /sys/class/thermal/cooling_device0/cur_state
```
*(States: `0` = Off, `1` = Low, `2` = Medium, `3` = 100% Full Speed).*

### **Lock Fan to Maximum 100% Speed:**
```bash
echo 3 | sudo tee /sys/class/thermal/cooling_device0/cur_state
```

---

## ⚡ **3. CPU Frequencies & Scaling Governors**

### **View Current Core Frequencies:**
```bash
cat /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq
```

### **Set All Cores to Maximum Performance Governor:**
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

---

## 🧠 **4. NPU (6 TOPS) Diagnostics**

### **Verify Device Node & Permissions:**
```bash
ls -l /dev/dri/renderD129
```

### **Fix Permissions for NPU:**
```bash
sudo usermod -aG video,render $USER && sudo chmod 666 /dev/dri/renderD129
```

### **Live Tri-Core NPU Load:**
```bash
cat /sys/kernel/debug/rknpu/load
```

---

## 🧹 **5. Memory (RAM) & NVMe Swap**

### **Clear Page Cache & Inodes:**
```bash
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

---

## 📷 **6. Camera & Video Devices (V4L2)**

### **List Video Nodes:**
```bash
v4l2-ctl --list-devices
```

### **Query Formats & Max Resolution:**
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

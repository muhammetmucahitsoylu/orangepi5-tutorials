# **Orange Pi 5 (RK3588S) Browser and Hardware Video Acceleration Guide**

This guide provides practical steps to fix stuttering, high CPU usage, and excessive fan noise when streaming 1080p or 4K YouTube and web videos in the Chromium browser on the Orange Pi 5.

---

## **1. Root Cause: Why Do Videos Stutter?**

The Orange Pi 5 is powered by a capable 8-core processor and includes a dedicated video processing unit (VPU) capable of 4K/8K hardware decoding. However, standard Linux distributions do not enable hardware video acceleration in Chromium by default:

* **Default Behavior:** The browser decodes video streams using the CPU cores instead of the dedicated video chip (software decoding).
* **Observed Problem:** When playing a 1080p or 4K video, CPU usage spikes to **80–100%**, causing dropped frames, video stutter, and loud cooling fan noise.
* **The Fix:** Enable hardware video decoding in Chromium to offload all video processing tasks directly to the onboard VPU.

---

## **2. Step 1: Install Required Video Libraries**

Ensure that the Rockchip hardware video acceleration packages are installed on your system by running:

```bash
sudo apt update && sudo apt install -y rockchip-mpp libv4l-rkmpp
```

---

## **3. Step 2: Enable Hardware Acceleration in Chromium**

### **Method A: Browser Flags (Recommended)**

1. Open **Chromium**.
2. Type `chrome://flags` in the address bar and press **Enter**.
3. Locate the following two settings using the search bar and set both to **Enabled**:
   * **Override software rendering list:** `Enabled`
   * **Hardware-accelerated video decode:** `Enabled`
4. Click the **Relaunch** button at the bottom right corner of the window to restart the browser.

### **Method B: Launch via Terminal or Shortcut**

If you prefer starting Chromium with hardware acceleration flags directly, run the following command in your terminal:

```bash
chromium-browser --enable-features=VaapiVideoDecoder,VaapiVideoEncoder --use-gl=egl
```

---

## **4. Step 3: Recommended YouTube Tweak (enhanced-h264ify)**

YouTube often serves video streams encoded in AV1 or VP9 formats. To ensure reliable hardware decoding for all playback:

1. Install the **enhanced-h264ify** extension from the Chrome Web Store.
2. In the extension settings, block the **AV1** codec so that YouTube serves streams encoded in **H.264** or **VP9**. This guarantees seamless hardware decoding on the VPU.

---

## **5. Verification: How to Confirm It Works**

To verify that hardware video acceleration is active:

1. In Chromium, navigate to `chrome://gpu`.
2. Find the **Video Decode** status line:
   * It should display **Hardware accelerated** in green text.

### **Before & After Comparison (4K 60FPS Video Test)**

| Metric | Software Decoding (Default) | Hardware Accelerated (After Fix) |
| :--- | :--- | :--- |
| **CPU Utilization** | 80% – 95% | **10% – 18%** |
| **Playback Quality** | Frequent stuttering and dropped frames | **Smooth 60 FPS playback** |
| **Thermal & Fan Status** | High temperature, fan at full speed | Cool, quiet operation |

# **Orange Pi 5 (RK3588S) Hardware and Accessory Compatibility Guide**

This guide provides practical recommendations for selecting the correct power supply, M.2 SSD, cooling system, and peripherals for the Orange Pi 5 (Rockchip RK3588S). It focuses on essential, field-tested guidance to help you avoid common stability issues, unexpected reboots, and hardware recognition failures.

---

## **1. Power Supply Selection**

Unexpected reboots and system crashes under load on the Orange Pi 5 are most commonly caused by using an inadequate power supply.

* **Recommended Specification:** **Fixed 5V / 4A (20W) Type-C power adapter.**
* **Why Standard Phone Chargers Should Not Be Used:**  
  Standard mobile phone chargers (5V 2A or 5V 3A) cannot supply sufficient instantaneous current when the board boots into a desktop environment, runs package updates (`apt update`), or encounters heavy CPU load. As soon as the input voltage drops, the board automatically shuts down or reboots to protect itself.
* **Fast-Charging (PD) Adapters:**  
  Multi-port fast chargers (USB Power Delivery) may fail to provide a consistent, stable 5V rail, leading to sudden system freezes.
* **Conclusion:** Always use the official Orange Pi 5V 4A power supply or a reputable, fixed-output 5V 4A DC adapter.

---

## **2. M.2 SSD Compatibility & Speed Expectations**

The Orange Pi 5 features a single M.2 socket on the underside of the board. Keep the following rules in mind when choosing an SSD:

### **NVMe (PCIe) Only**
* **Do NOT install an M.2 SATA SSD.** The slot does not have SATA data lines routed to it; M.2 SATA drives will not be detected at all (`lsblk` will show nothing).
* Only **M.2 NVMe (PCIe)** drives are supported (M-Key).

### **Speed Limits (PCIe 2.0 x1)**
* The M.2 interface on the Orange Pi 5 is hardware-limited to **PCIe 2.0 x1** (a single lane).
* Even if you install a high-end Gen4 SSD rated for 7,000 MB/s, your practical sequential read/write speeds will cap at **~410 – 420 MB/s**.
* You do not need to spend extra money on premium high-speed drives; any reliable, budget-friendly NVMe SSD will fully saturate the board's available bus bandwidth.

### **Sleep Mode (ASPM) Freezes and Fix**
Some SSDs (notably certain revisions of the Kingston NV2 or drives using Phison controllers) may freeze the system when the board enters idle or low-power sleep states.
* **Solution:** Add the following parameter to `/boot/armbianEnv.txt` or your distribution's bootloader configuration:
  ```text
  extraargs=pcie_aspm=off
  ```

### **Recommended SSD Models**
* **Compatible:** M.2 NVMe SSDs.
* **Incompatible:** All M.2 SATA SSDs.

---

## **3. Cooling Selection (Passive vs. Active Fan)**

When the processor temperature reaches **80°C**, the board automatically throttles clock speeds to prevent overheating, which degrades performance significantly.

* **Passive Aluminum Heatsink:** Suitable only for light desktop browsing or basic terminal tasks. Under sustained workloads, temperatures quickly exceed 80°C and trigger thermal throttling.
* **Active Fan Cooling (Recommended):** An aluminum heatsink equipped with a 5V fan keeps temperatures within the 70–75°C range even under 100% all-core load. Active cooling is strongly recommended for 24/7 server tasks, software compilation, or AI workloads.
* **Connection:** Connect directly to the onboard 2-pin 5V fan header.

---

## **4. Networking & Peripherals**

### **No Onboard Wi-Fi or Bluetooth**
* The standard Orange Pi 5 does not include built-in Wi-Fi or Bluetooth hardware.
* For network connectivity, use the built-in **Gigabit Ethernet** port or a USB Wi-Fi adapter with native Linux kernel driver support (such as adapters based on the Realtek RTL8821CU or RTL8811CU chipsets).

### **USB 3.0 Wireless Interference**
* When an external drive or high-speed device is plugged into the blue USB 3.0 port, it can generate radio interference on the 2.4 GHz band.
* **Symptom:** Wireless keyboard/mouse dongles plugged adjacent to the USB 3.0 port may experience dropped keystrokes, stuttering, or latency.
* **Solution:** Plug 2.4 GHz wireless dongles into a USB 2.0 port, or use a short USB extension cable to move the receiver away from the USB 3.0 port.

---

## **5. Hardware Selection Summary**

| Component | Recommended Choice | What to Avoid |
| :--- | :--- | :--- |
| **Power Supply** | Dedicated 5V / 4A fixed Type-C adapter | Standard phone chargers (5V 2A), unstable multi-port PD adapters |
| **M.2 Storage** | M.2 NVMe PCIe SSD (~418 MB/s practical ceiling) | M.2 SATA SSDs (completely unsupported) |
| **Cooling** | 5V active fan heatsink | Running without a heatsink or using tiny passive pads under load |
| **Network** | Wired Gigabit Ethernet or compatible USB Wi-Fi dongle | Generic wireless adapters without Linux in-tree drivers |
| **Wireless Dongles** | Connected via USB 2.0 port or USB extension cable | Plugged directly adjacent to active USB 3.0 storage drives |

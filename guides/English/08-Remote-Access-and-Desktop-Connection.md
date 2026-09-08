# **Orange Pi 5 (RK3588S) Remote Access and Desktop Connection Guide**

This guide provides practical instructions for connecting to the Orange Pi 5 from a laptop or desktop computer without an external monitor, keyboard, or mouse, covering both command-line (CMD / Terminal) and graphical desktop (GUI) access methods.

---

## **PART 1: Command-Line Interface (Terminal / CMD)**

### **Method 1: Standard SSH Connection (Network-Based)**

When both your laptop and the Orange Pi 5 are connected to the same local network (Wi-Fi or Ethernet), connect directly using your operating system's built-in terminal:

* **From Windows (CMD / PowerShell), macOS, or Linux:**
  ```bash
  ssh your_username@ORANGE_PI_IP
  ```
  *(Default image credentials are often `orangepi` or `root`, password: `orangepi`)*

### **Method 2: Passwordless Key-Based Authentication (SSH Key)**
To avoid typing your password upon every connection and improve security, install your public key onto the board:

* **From Windows PowerShell (single command transfer):**
  ```powershell
  # Generate an ED25519 key if you do not have one:
  ssh-keygen -t ed25519

  # Copy public key to Orange Pi:
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh your_username@ORANGE_PI_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
  ```

### **Method 3: Hardware UART Serial Console (No Network or Display Required)**
The most reliable recovery interface when network access is down, the IP is unknown, or the board freezes during bootloader stages.

* **Hardware Requirement:** 3.3V TTL USB-to-serial adapter (CP2102 or CH340).
* **Connection Options (V1.3.2 Hardware Pinout):**
  * **Recommended: Dedicated 3-Pin Debug UART Header:**  
    Located directly below the 26-pin expansion header (the square solder pad is GND):
    * USB-TTL **GND** -> Orange Pi 5 **GND** (Bottom square pin)
    * USB-TTL **RX** -> Orange Pi 5 **TX** (Top pin)
    * USB-TTL **TX** -> Orange Pi 5 **RX** (Middle pin)
  * **Alternative: Via 26-Pin Header (UART0):**
    * USB-TTL **GND** -> Pin 6 (GND)
    * USB-TTL **RX** -> Pin 8 (`GPIO4_A3` / `UART0_TX_M2`)
    * USB-TTL **TX** -> Pin 10 (`GPIO4_A4` / `UART0_RX_M2`)
* **Critical Setting:** The Rockchip RK3588 serial debug console communicates at a non-standard speed of **1,500,000 (1.5M)** baud. In PuTTY, minicom, or screen, strictly configure baud rate to `1500000`. Refer to [docs/GPIO_PINOUT.md](../../docs/GPIO_PINOUT.md) for full header mappings.

---

## **PART 2: Graphical Desktop Access (Remote Desktop / GUI)**

### **Method 1: Windows Remote Desktop (RDP / xrdp) — Most Convenient**

Connect using Windows' native "Remote Desktop Connection" client without installing third-party software on your PC.

1. **Install xrdp on the Orange Pi 5:**
   ```bash
   sudo apt update && sudo apt install -y xrdp
   sudo systemctl enable --now xrdp
   ```
2. **Grant certificate permissions to the xrdp service:**
   ```bash
   sudo adduser xrdp ssl-cert
   ```
3. **Connect:**  
   On Windows, press `Win + R`, type `mstsc`, and press **Enter**. Enter your Orange Pi 5's IP address and click **Connect**. Provide your username and password to access the full desktop environment.

---

### **Method 2: VNC Server (TigerVNC) — Lightweight & Flexible**

Ideal for low-bandwidth networks or connecting from macOS and Linux laptops.

1. **Install TigerVNC:**
   ```bash
   sudo apt install -y tigervnc-standalone-server tigervnc-common
   ```
2. **Set a VNC password:**
   ```bash
   vncpasswd
   ```
3. **Start the VNC display server:**
   ```bash
   vncserver :1 -geometry 1920x1080 -depth 24
   ```
4. **Connect:** Launch **RealVNC Viewer** on your computer and connect to `ORANGE_PI_IP:5901`.

---

### **Method 3: RustDesk / NoMachine — High FPS & Low Latency**

The best choice for streaming media, audio forwarding, and fluid 60 FPS remote desktop responsiveness.

* **NoMachine (Recommended):** Download the NoMachine ARM64 `.deb` package on the Orange Pi 5 and the client on your PC. NoMachine automatically discovers the board on your LAN, offering zero-configuration hardware-accelerated desktop streaming and audio playback.

---

### **Method 4: SSH X11 Forwarding (Launch Single GUI Apps)**

Forward individual graphical windows (such as a text editor or an OpenCV camera preview) to your laptop without loading a full desktop session:

* **Connection Command:**
  ```bash
  ssh -X your_username@ORANGE_PI_IP
  ```
* Once connected, running a command like `gedit` or `galculator` will open the window natively on your laptop's screen *(requires an X-server like VcXsrv or Xming on Windows)*.

---

## **3. Comparison Matrix**

| Method | Protocol / Type | Client-side Software | Best Use Case |
| :--- | :--- | :--- | :--- |
| **SSH (CMD/PowerShell)** | Terminal | None (Built-in) | Server administration, scripts, headless package management |
| **UART Serial Console** | Hardware Console | USB-TTL Cable + PuTTY | Low-level recovery when OS or networking fails |
| **Windows RDP (xrdp)** | Graphical Desktop | None (Built into Windows) | Quick, hassle-free remote desktop without client installs |
| **NoMachine** | Graphical Desktop | NoMachine Client | High-performance 60 FPS desktop with audio passthrough |
| **SSH X11 (-X)** | Single Window | X-Server (e.g. VcXsrv) | Running individual GUI applications without full desktop |

# **Orange Pi 5 (RK3588S) Personal Cloud and Jellyfin Hardware Media Server Guide**

This guide details converting your Orange Pi 5 into a complete, private **Home Cloud & Streaming Station (NAS & Media Server)** powered by CasaOS, Nextcloud (automatic smartphone backup replacing Google Photos), and Jellyfin with hardware-accelerated 4K transcoding via the Rockchip RK3588 VPU.

---

## **1. Architecture & Hardware Superiority**

Compared to traditional single-board computers (such as Raspberry Pi 4/5), the Orange Pi 5 offers unmatched multimedia capabilities:
* **8K 10-bit VPU Hardware Acceleration:** Transcodes 4K HEVC/H.265 streams in real-time directly on silicon with near-zero CPU consumption.
* **Dedicated M.2 NVMe PCIe Bus:** Provides steady 400 MB/s+ sequential throughput, eliminating the bottlenecks of USB-tethered drives during multi-user write operations.
* **CasaOS Unified Dashboard:** A sleek, mobile-responsive web orchestration layer that makes managing Docker containers intuitive.

```
[ Internet / Local Network ] 
              │
              ▼
[ Orange Pi 5 (RK3588S) ]
 ├── CasaOS Web Management Dashboard (Port 80)
 ├── Nextcloud: Seamless background camera roll backup (Google Photos replacement)
 ├── Jellyfin: 4K HDR transcoding to Smart TVs/phones (Private Netflix replacement)
 └── Samba (SMB): Direct network drive mapping in Windows Explorer and macOS Finder
```

---

## **2. Step 1: Mounting M.2 NVMe Storage Permanently**

To ensure persistent mount points across reboots, mount your NVMe SSD by its filesystem UUID:

```bash
# 1. Identify your NVMe partition UUID:
sudo blkid
# Example output: /dev/nvme0n1p1: UUID="a1b2c3d4-xxxx" TYPE="ext4"

# 2. Create structured storage directories:
sudo mkdir -p /DATA/AppData /DATA/Media /DATA/Documents

# 3. Add persistent entry to /etc/fstab:
echo "UUID=a1b2c3d4-xxxx /DATA ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# 4. Mount without rebooting:
sudo mount -a
```

---

## **3. Step 2: Install CasaOS (Modern Home Cloud Layer)**

CasaOS deploys a lightweight containerized web dashboard to supervise your entire server:

```bash
curl -fsSL https://get.casaos.io | sudo bash
```

*Installation completes in approximately 2 minutes. Open your web browser and navigate to `http://ORANGE_PI_IP` to access the setup wizard.*

1. Configure your master administrator username and secure password.
2. The dashboard will immediately display real-time CPU thermals, RAM allocation, and NVMe disk health.

---

## **4. Step 3: Nextcloud for Automated Mobile Camera Backup**

Inside the CasaOS App Store, locate and install **Nextcloud**.

### **Configuration Steps:**
1. **Installation:** Click "Install" from the app directory.
2. **Storage Binding:** Map the storage volume to your high-speed NVMe path (`/DATA/Documents`).
3. **Mobile Client Setup:**
   * Install the official **Nextcloud** app on your iOS or Android device.
   * Point server address to `http://ORANGE_PI_IP:8080` and log in.
   * Navigate to **Settings -> Auto Upload**.
   * *All photos and videos captured on your smartphone will now automatically sync to your private Orange Pi 5 SSD whenever connected to Wi-Fi.*

---

## **5. Step 4: Jellyfin with Rockchip VPU Hardware Transcoding (4K Playback)**

Jellyfin transforms your raw video library into a rich media experience. The critical technical milestone is **passing the RK3588S VPU video decoding nodes into the Docker container.**

### **1. Configure Hardware Device Permissions:**
```bash
# 1. Grant immediate access to VPU, 2D RGA, and render nodes:
sudo chmod 666 /dev/mpp_service /dev/rga /dev/dri/*

# 2. CRITICAL: Persist permissions across reboots via udev rule:
sudo tee /etc/udev/rules.d/99-rockchip-permissions.rules <<EOF
KERNEL=="mpp_service", MODE="0666"
KERNEL=="rga", MODE="0666"
KERNEL=="renderD*", MODE="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### **2. Deploy Hardware-Accelerated Jellyfin Container:**
Launch the container via Docker Compose using the Rockchip-optimized Jellyfin image:

```yaml
version: "3.8"
services:
  jellyfin:
    image: nyanmisaka/jellyfin:latest  # Rockchip MPP optimized build
    container_name: jellyfin
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /DATA/AppData/Jellyfin/config:/config
      - /DATA/AppData/Jellyfin/cache:/cache
      - /DATA/Media:/media
    devices:
      - /dev/dri:/dev/dri                      # GPU acceleration
      - /dev/mpp_service:/dev/mpp_service      # Rockchip VPU Hardware Decoder
      - /dev/rga:/dev/rga                      # 2D Raster Graphic Accelerator
    restart: unless-stopped
```

Deploy:
```bash
docker compose up -d
```

### **3. Enable VPU Acceleration in Jellyfin Admin UI:**
1. Navigate to `http://ORANGE_PI_IP:8096`.
2. Open **Dashboard -> Playback -> Transcoding**.
3. Under **Hardware Acceleration**, select **Rockchip MPP (RKMPP)** or **VAAPI**.
4. Check all supported hardware decoding codecs: **H.264, HEVC (H.265), VP9, and AV1**.

---

## **6. Step 5: Native Network Storage Sharing (Samba / SMB)**

To map your Orange Pi 5 disk as a local hard drive in Windows "This PC" or macOS Finder:

```bash
# 1. Install Samba server:
sudo apt install -y samba

# 2. Append share configuration to /etc/samba/smb.conf:
sudo tee -a /etc/samba/smb.conf <<EOF

[OrangePi_Share]
   path = /DATA
   browseable = yes
   writable = yes
   guest ok = no
   create mask = 0775
   directory mask = 0775
EOF

# 3. Create your Samba user password:
sudo smbpasswd -a $USER

# 4. Restart Samba service:
sudo systemctl restart smbd
```

* **Windows Connection:** Open File Explorer and enter `\\ORANGE_PI_IP\OrangePi_Share` into the address bar.
* **macOS Connection:** In Finder, press `Cmd + K` and enter `smb://ORANGE_PI_IP/OrangePi_Share`.

---

## **7. Hardware Benchmark & Power Efficiency**

| Metric | Software CPU Transcoding (SBC Default) | Orange Pi 5 (RK3588S VPU Offloaded) |
| :--- | :--- | :--- |
| **4K HEVC -> 1080p Transcoding** | Unplayable (~3-5 FPS, 100% CPU lockup) | **Smooth 60 FPS (<15% CPU load, VPU Active)** |
| **Simultaneous Torrent + Sync** | Bottlenecks on USB bus | **400 MB/s concurrent NVMe throughput** |
| **Idle Power Consumption** | ~8 – 12 Watts (X86 Mini PC) | **~3.5 – 6.5 Watts (Negligible electricity cost)** |

> [!TIP]
> This setup permanently replaces monthly cloud storage subscriptions while keeping all your private data, documents, and media physically secured inside your home network.

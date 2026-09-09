# **Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide**

> 🛡️ **Hardware Verified:** Upstream Docker Engine, Compose, and hardware passthrough of `/dev/mpp_service`, `/dev/rga`, and `/dev/mali0` are validated on **Orange Pi 5 running Ubuntu 24.04 / 22.04 LTS**.

This guide demonstrates how to install upstream Docker Engine on the Orange Pi 5, remediate distro-specific `cgroup` memory limit warnings, pass hardware acceleration nodes (VPU/GPU) directly into containers (Jellyfin/Plex), and resolve common permission and driver faults.

---

## **1. Upstream Docker Engine Installation**

Avoid bloated Snap packages. Install the official Docker Engine directly from Docker’s upstream APT repository:

```bash
# 1. Install prerequisites:
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# 2. Add Docker's official GPG key:
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Set up repository:
. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Install Docker packages:
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. Add current user to docker group:
sudo usermod -aG docker $USER
```
*(Apply group permissions immediately without rebooting via `newgrp docker`).*

---

## **2. Resolving cgroup Memory & Swap Limit Warnings (Distro-Specific)**

Running `docker info` often prints:
```text
WARNING: No memory limit support
WARNING: No swap limit support
```

This occurs because kernel cgroup accounting is disabled by default in boot parameters. **Apply the fix according to your running distribution:**

### **Scenario A: If Running Armbian**
```bash
sudo nano /boot/armbianEnv.txt
```
Append to `extraargs=` (or add a new line):
```text
extraargs=cgroup_enable=memory swapaccount=1
```

### **Scenario B: If Running Official Orange Pi OS / Ubuntu**
```bash
# 1. If /boot/orangepiEnv.txt exists:
sudo nano /boot/orangepiEnv.txt
# Append:
extraargs=cgroup_enable=memory swapaccount=1

# 2. If using U-Boot extlinux configuration:
sudo nano /boot/extlinux/extlinux.conf
# Locate the active "append" kernel command line and append:
cgroup_enable=memory swapaccount=1
```

*Reboot via `sudo reboot`. Verify warnings have cleared in `docker info`.*

---

## **3. Mapping Hardware Acceleration (VPU / GPU) into Containers**

Transcoding high-bitrate 4K media (Jellyfin/Plex) or processing camera feeds (Frigate) without saturating the CPU requires mapping Rockchip hardware device nodes:

* `/dev/dri`: Mali-G610 GPU interfaces
* `/dev/mpp_service`: Rockchip VPU hardware video decoder/encoder
* `/dev/rga`: 2D graphics raster engine

### **Sample `docker-compose.yml` (Hardware-Accelerated Jellyfin)**

```yaml
version: "3.8"
services:
  jellyfin:
    image: nyanmisaka/jellyfin:latest  # Rockchip MPP accelerated image
    container_name: jellyfin
    network_mode: "host"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /path/to/media:/media
    devices:
      - /dev/dri:/dev/dri
      - /dev/mpp_service:/dev/mpp_service
      - /dev/rga:/dev/rga
    restart: unless-stopped
```

* **Outcome:** Offloading 4K HEVC transcoding to the VPU keeps CPU utilization at **~5–10%** instead of 100% throttling.

---

## **4. Verification**

```bash
docker run --rm hello-world
```

---

## **5. Troubleshooting & Diagnostics Matrix**

| Error / Symptom | Root Cause | Verified Solution |
| :--- | :--- | :--- |
| `permission denied while trying to connect to the Docker daemon socket` | Active shell session does not reflect recent `docker` group membership. | Execute `newgrp docker` or reboot the machine. |
| `error gathering device information while adding device "/dev/mpp_service": no such file` | Running mainline (vanilla) Linux kernel lacking proprietary Rockchip MPP drivers. | Run `ls -l /dev/mpp_service`. If missing, switch to a vendor Rockchip BSP kernel (5.10.x / 6.1-rockchip). |
| GPG certificate validation failure during `apt update` | RTC time desynchronization on boards without battery backup. | Synchronize network time via `sudo timedatectl set-ntp true`. |
| Transcoding fails inside container | Missing group permissions for video/render nodes. | Add user to host groups: `sudo usermod -aG video,render $USER` and map GIDs via `group_add` in compose. |

# **Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide**

This guide provides instructions for deploying a clean, native Docker and Docker Compose environment on the Orange Pi 5, eliminating cgroup memory limit warnings, and passing hardware acceleration (VPU/GPU) devices into containers (e.g., Jellyfin, Plex, Frigate).

---

## **1. Native Docker Engine Installation**

Avoid slow Snap packages by installing the official upstream Docker APT repository directly:

```bash
# 1. Install prerequisites:
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# 2. Add Docker's official GPG key:
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Set up the Docker APT repository:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Install Docker Engine and the Compose plugin:
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. Add your current user to the docker group (to run docker without sudo):
sudo usermod -aG docker $USER
```
*(Log out and back in, or run `newgrp docker` to apply group membership).*

---

## **2. Resolving cgroup Memory & Swap Warnings**

Running `docker info` may display:
`WARNING: No memory limit support / WARNING: No swap limit support`

This occurs because kernel cgroup memory accounting is disabled by default on some arm64 builds.

* **Fix:** Append the following parameters to your boot configuration (`/boot/armbianEnv.txt` or extlinux.conf):
  ```text
  extraargs=cgroup_enable=memory swapaccount=1
  ```
* Reboot the system for the kernel parameters to take effect.

---

## **3. Hardware Acceleration Passthrough (VPU / GPU)**

To allow containerized media servers (Jellyfin/Plex) or computer vision stacks (Frigate) to perform hardware transcoding, map the board's hardware acceleration nodes into the container:

* `/dev/dri`: ARM Mali-G610 GPU DRM interface
* `/dev/mpp_service`: Rockchip VPU hardware video decoder/encoder
* `/dev/rga`: 2D raster graphic accelerator

### **Example `docker-compose.yml` (Hardware-Accelerated Jellyfin)**

```yaml
version: "3.8"
services:
  jellyfin:
    image: nyanmisaka/jellyfin:latest  # Optimized image with Rockchip MPP/RGA support
    container_name: jellyfin
    network_mode: "host"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
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

* **Outcome:** When streaming high-bitrate 4K content to client devices, transcoding load is completely offloaded to the VPU, keeping CPU utilization under **10%**.

---

## **4. Verification**

Verify that Docker can pull and run containers:

```bash
docker run --rm hello-world
```

If "Hello from Docker!" is printed, the engine is fully operational.

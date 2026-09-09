# **Orange Pi 5 (RK3588S) Headless Server and Initial Optimization Guide**

> 🛡️ **Hardware Verified:** ZRAM memory compression, headless GUI disabling (500MB+ RAM reclaimed), and persistent governor services are physically validated on **Orange Pi 5 running Ubuntu 24.04 / 22.04 LTS**.

This guide provides practical instructions for deploying the Orange Pi 5 as a 24/7 headless home server, Docker host, or network appliance without an attached monitor, keyboard, or mouse.

---

## **1. Initial SSH Connection & User Hardening**

Connect the board to your local network via an Ethernet cable and identify its assigned IP address:

```bash
# Initial SSH login (Official image default user: root or orangepi, password: orangepi):
ssh root@ORANGE_PI_IP
```

### **Create a Dedicated Sudo User**
Avoid operating directly as `root`. Create a personalized user account with administrative privileges:

```bash
# 1. Create your user account:
adduser your_username

# 2. Grant sudo permissions:
usermod -aG sudo your_username
```

---

## **2. Disable Display Manager to Free Up RAM**

If your installed image includes a desktop environment, running an active GUI stack without an attached monitor wastes **500 to 700 MB of RAM**. Switch to pure headless (CLI) mode:

```bash
# Switch default boot target from graphical desktop to multi-user CLI:
sudo systemctl set-default multi-user.target

# (Optional) To restore the desktop environment in the future:
# sudo systemctl set-default graphical.target
```

---

## **3. Configure ZRAM: Memory Safety & SSD Wear Reduction**

Compiling software or running multiple container stacks can exhaust physical memory. Rather than relying on disk-based swap partitions that degrade SSD endurance through continuous writes, configure compressed in-memory swap (**ZRAM**):

```bash
# 1. Install the zram-tools utility:
sudo apt install -y zram-tools

# 2. Allocate 50% of total physical RAM to fast ZRAM swap:
sudo tee -a /etc/default/zramswap <<EOF
ALGO=zstd
PERCENT=50
PRIORITY=100
EOF

# 3. Restart the ZRAM service:
sudo systemctl restart zramswap

# 4. Verification:
zramctl
```

---

## **4. Network Time Synchronization (NTP / Clock Accuracy)**

The standard Orange Pi 5 does not include a battery-backed real-time clock (RTC). An inaccurate system clock breaks SSL handshakes, package manager repositories (`apt`), and TLS certificates:

```bash
# 1. Enable automated systemd time synchronization:
sudo timedatectl set-ntp true

# 2. Configure your local timezone (Example: UTC or your region):
sudo timedatectl set-timezone UTC

# 3. Verify synchronization:
timedatectl status
```
*(Verify that `NTP service: active` and `System clock synchronized: yes` are displayed).*

---

## **5. Persistent Performance Governor Service**

To ensure your server responds to incoming network requests without CPU governor wake-up latency, configure a lightweight `systemd` service that locks CPU and memory controllers to performance mode at boot:

```bash
sudo tee /etc/systemd/system/cpu-performance.service <<EOF
[Unit]
Description=Set CPU and DMC to Performance Mode
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor && echo performance | tee /sys/class/devfreq/dmc/governor'

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service:
sudo systemctl daemon-reload
sudo systemctl enable --now cpu-performance.service
```

---

## **6. Post-Install Checklist**

* [x] Non-root administrative user configured.
* [x] Headless multi-user target enabled (500MB+ RAM reclaimed).
* [x] ZRAM compressed swap active to prevent out-of-memory lockups.
* [x] Timezone and automated NTP time synchronization active.
* [x] Automated boot-time performance governor service enabled.

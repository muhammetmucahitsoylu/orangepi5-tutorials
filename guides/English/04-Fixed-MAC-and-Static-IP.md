# **Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide**

> 🛡️ **Hardware Verified:** All `nmcli` static IP and MAC address persistent binding procedures are verified on **Orange Pi 5 hardware running Ubuntu 24.04 / 22.04 LTS**.

This guide provides a diagnostic workflow to determine whether your Orange Pi 5 is generating randomized MAC addresses on reboot, and demonstrates how to assign a persistent cloned MAC address and static local IP via NetworkManager when required.

> [!NOTE]
> **OBJECTIVE DIAGNOSTIC NOTICE:**  
> This issue **does NOT affect every Orange Pi 5 system.** On modern Armbian builds and recent official Orange Pi OS releases, the Rockchip Ethernet driver correctly reads hardware eFuse IDs, ensuring the MAC address is inherently persistent across reboots.  
> **If Step 1 reveals that your MAC address remains unchanged after rebooting, you DO NOT NEED this guide.** This documentation exists strictly to remediate chronic DHCP lease changes on legacy kernel builds or boards encountering eFuse readout timeouts.

---

## **1. Root Cause: Why Does the IP Change?**

On certain older kernel versions or BSP revisions, if U-Boot fails to pass the physical OTP MAC address to the Linux kernel, the kernel generates a randomized locally-administered address (`fe:xx:xx...`) at each boot:

* **Consequence:** Your router/DHCP server treats the board as an entirely new device on every boot, assigning a new IP address and breaking persistent SSH sessions, local port forwards, and Docker services.
* **Resolution:** Diagnose whether randomization is occurring; if so, assign a static cloned MAC address via NetworkManager.

---

## **2. Step 1: Diagnose MAC Address Persistence**

First, list your active physical network interfaces and determine your primary Ethernet interface name:

```bash
ip -br link
```
*(On Ubuntu 24.04, the primary Rockchip Gigabit Ethernet interface is typically named `end1`, while on Ubuntu 22.04 or legacy kernels it is named `eth0`).*

Inspect your interface details (e.g. for `end1`):

```bash
ip link show end1   # or: ip link show eth0
```

1. Note the 12-character hexadecimal string next to `link/ether` (e.g., `ee:7c:02:4b:91:aa`).
2. Reboot the board:
   ```bash
   sudo reboot
   ```
3. Re-run `ip link show end1` (or `eth0`).
   * **If the address is identical:** Your system is **NOT** affected. Skip Steps 2 and 3.
   * **If the address changed (e.g., starts with `fe:` or different octets):** Proceed to Step 2.

---

## **3. Step 2: Configure Persistent Cloned MAC Address (NetworkManager)**

1. Identify the connection name:
   ```bash
   nmcli connection show
   ```
   *(Look under the `NAME` column, commonly `Wired connection 1` or `eth0`).*

2. Assign a static cloned MAC address:
   ```bash
   sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.cloned-mac-address "EE:7C:02:4B:91:AA"
   ```

3. Re-activate the profile:
   ```bash
   sudo nmcli connection up "Wired connection 1"
   ```

---

## **4. Step 3: Pin Static IP Directly on Board**

```bash
# 1. Set static IPv4 address and CIDR prefix (e.g., 192.168.1.150/24):
sudo nmcli connection modify "Wired connection 1" ipv4.addresses "192.168.1.150/24"

# 2. Define Gateway (router IP, typically 192.168.1.1):
sudo nmcli connection modify "Wired connection 1" ipv4.gateway "192.168.1.1"

# 3. Specify upstream DNS resolvers:
sudo nmcli connection modify "Wired connection 1" ipv4.dns "1.1.1.1,8.8.8.8"

# 4. Switch from DHCP to manual assignment:
sudo nmcli connection modify "Wired connection 1" ipv4.method manual

# 5. Apply changes:
sudo nmcli connection up "Wired connection 1"
```

---

## **5. Verification**

```bash
ip addr show end1   # or: ip addr show eth0
```
*Verify that `inet` reflects your chosen IP (e.g., `192.168.1.150`) and `link/ether` displays your configured cloned MAC.*

---

## **6. Troubleshooting & Diagnostics Matrix**

| Error / Symptom | Root Cause | Verified Solution |
| :--- | :--- | :--- |
| `nmcli: command not found` | Minimal headless image without NetworkManager (`systemd-networkd` / Netplan in use). | Install NetworkManager via `sudo apt install network-manager` or apply static IP in `/etc/netplan/*.yaml`. |
| `Connection 'Wired connection 1' unknown` | Name mismatch (may be localized or labeled `eth0`). | Run `nmcli connection show` and copy the exact string inside quotes. |
| Loss of internet connectivity after static IP | Invalid gateway or unconfigured DNS. | Verify router IP via `ip route show` and ensure `1.1.1.1,8.8.8.8` are provided to `ipv4.dns`. |
| MAC still randomized after reboot | Cloned MAC not saved to persistent profile. | Inspect `/etc/NetworkManager/system-connections/*.nmconnection` to ensure `cloned-mac-address` is retained. |

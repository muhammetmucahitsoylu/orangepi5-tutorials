# **Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide**

This guide provides practical steps to fix the "random MAC address" issue that causes the Orange Pi 5 to receive a different IP address after every reboot, and explains how to configure a permanent static IP.

---

## **1. Root Cause: Why Does the IP Address Keep Changing?**

On some Orange Pi 5 boards or certain Linux kernel releases, if the permanent hardware MAC address cannot be read from U-Boot, the kernel generates a randomized locally administered MAC address upon every system startup:

* **Consequence:** Each time the board boots up, your router (DHCP server) detects it as a brand-new device and assigns a different IP address. This disrupts SSH connections, local server daemons, and port forwarding rules.
* **The Solution:** Assign a persistent cloned MAC address to the network interface and optionally bind a permanent static local IP.

---

## **2. Step 1: Check If Your MAC Address is Randomizing**

Run the following command in your terminal:

```bash
ip link show eth0
```

Note the 12-character hexadecimal hardware address listed after `link/ether`. Reboot the board with `sudo reboot` and run the command again. If the address has changed, your board is generating randomized MAC addresses.

---

## **3. Step 2: Configure a Permanent Fixed MAC Address**

The cleanest and most reliable method to pin a persistent MAC address is using **NetworkManager**.

1. Identify your active network connection name:
   ```bash
   nmcli connection show
   ```
   *(Typically listed as `Wired connection 1`).*

2. Assign a persistent cloned MAC address (you may adjust the ending octets as desired):
   ```bash
   sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.cloned-mac-address "EE:7C:02:4B:91:AA"
   ```

3. Reactivate the connection to apply changes immediately:
   ```bash
   sudo nmcli connection up "Wired connection 1"
   ```

*From now on, the board will present the exact same hardware identifier to your router on every reboot, allowing stable DHCP reservations.*

---

## **4. Step 3: Configure a Static IP Address On-Device**

To completely bypass DHCP and guarantee a permanent local IP address directly from the board:

```bash
# 1. Specify the static IP and subnet mask (Example: 192.168.1.150/24):
sudo nmcli connection modify "Wired connection 1" ipv4.addresses "192.168.1.150/24"

# 2. Specify your network gateway (Router IP, typically 192.168.1.1):
sudo nmcli connection modify "Wired connection 1" ipv4.gateway "192.168.1.1"

# 3. Define primary and secondary DNS resolvers:
sudo nmcli connection modify "Wired connection 1" ipv4.dns "1.1.1.1,8.8.8.8"

# 4. Switch the addressing method from DHCP (auto) to manual:
sudo nmcli connection modify "Wired connection 1" ipv4.method manual

# 5. Reconnect to apply the static configuration:
sudo nmcli connection up "Wired connection 1"
```

---

## **5. Verification**

Confirm that both the static IP and pinned MAC address are active:

```bash
ip addr show eth0
```

* If the `inet` line displays your configured static IP (e.g., `192.168.1.150`) and `link/ether` displays your fixed MAC address, configuration is complete and will persist across all subsequent reboots.

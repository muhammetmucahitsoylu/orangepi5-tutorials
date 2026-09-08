# **Orange Pi 5 (RK3588S) Network Shield (AdGuard Home, Unbound and Tailscale Guide)**

This guide covers converting the Orange Pi 5 into an enterprise-grade **Whole-Home Network Security & Privacy Gateway**, eliminating telemetry, malware, and intrusive advertisements at the router level, decoupling DNS resolution from commercial ISPs via Unbound, and exposing a secure WireGuard-based Tailscale mesh tunnel.

---

## **1. Security & Privacy Topology**

The gateway intercepts domain queries before they ever reach client endpoints (Smart TVs, mobile phones, IoT sensors, gaming consoles, PCs):

```
[ Local Clients (Phones, Smart TVs, PCs) ]
                   │ (DNS query: "ads.tracker.com")
                   ▼
[ 1. AdGuard Home (Orange Pi 5: Port 53) ] ──> Match against blocklists -> DROP/SINKHOLE (0.1 ms)
                   │ (Clean domain query: "google.com")
                   ▼
[ 2. Unbound DNS Resolver (Port 5335) ] ──> Resolves iteratively directly from authoritative root servers
                   │
                   ▼
[ Internet Root Anchors (.) ] (ISPs and third parties cannot log your browsing history)

+ [ 3. Tailscale Mesh Tunnel ] ──> Route external cellular data securely back to home via encrypted Exit Node.
```

---

## **2. Step 1: Resolving Port 53 Binding Conflict (`systemd-resolved`)**

By default, Ubuntu's `systemd-resolved` binds to UDP port 53. Free this port for AdGuard Home:

```bash
# 1. Disable DNSStubListener in systemd-resolved:
sudo sed -r -i.orig 's/#?DNSStubListener=yes/DNSStubListener=no/g' /etc/systemd/resolved.conf

# 2. CRITICAL: Point resolv.conf directly to upstream DNS so internet resolution stays active:
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf

# 3. Restart systemd-resolved (Port 53 is now freed without losing internet access):
sudo systemctl restart systemd-resolved
```

---

## **3. Step 2: AdGuard Home Installation**

AdGuard Home acts as the central DNS filter with a responsive web management interface:

```bash
# Execute official installer:
curl -s -S -L https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh | sudo sh -s -- -v
```

### **Initial Setup Wizard:**
1. Open your browser and navigate to `http://ORANGE_PI_IP:3000`.
2. **Web Interface:** Listen on Port `80` or `8080`.
3. **DNS Server:** Listen on Port `53` on all interfaces (`0.0.0.0`).
4. Set up administrative credentials.
5. Access the full dashboard at `http://ORANGE_PI_IP`.

---

## **4. Step 3: Unbound Root Recursive DNS Resolver Setup**

Commercial upstream providers (Google 8.8.8.8, Cloudflare 1.1.1.1) maintain query logs. **Unbound** eliminates intermediaries by querying the Internet root name servers directly with DNSSEC validation:

```bash
# 1. Install Unbound:
sudo apt update && sudo apt install -y unbound

# 2. Deploy optimized configuration:
sudo tee /etc/unbound/unbound.conf.d/adguard.conf <<EOF
server:
    verbosity: 1
    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    do-ip6: no

    # Security & Privacy Hardening
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    use-caps-for-id: no

    # Cache Optimization
    edns-buffer-size: 1232
    prefetch: yes
    num-threads: 4
    so-rcvbuf: 4m
    so-sndbuf: 4m
EOF

# 3. Enable and restart Unbound:
sudo systemctl restart unbound
sudo systemctl enable unbound
```

### **Verify Unbound Resolution:**
```bash
dig @127.0.0.1 -p 5335 google.com
```
*Expected result: `status: NOERROR` and valid IP responses directly from root authorities.*

---

## **5. Step 4: Routing AdGuard Home to Local Unbound**

1. Access your AdGuard Home dashboard (`http://ORANGE_PI_IP`).
2. Go to **Settings -> DNS Settings**.
3. Clear all default entries in **Upstream DNS Servers** and replace with:
   ```text
   127.0.0.1:5335
   ```
4. Click **Apply**.
*All domain queries from the entire house are now filtered by AdGuard and resolved recursively by Unbound.*

---

## **6. Step 5: Tailscale Subnet Routing & Encrypted Exit Node**

To maintain ad-blocking and encrypted home routing while on cellular data or untrusted public Wi-Fi:

```bash
# 1. Install Tailscale:
curl -fsSL https://tailscale.com/install.sh | sudo sh

# 2. Enable kernel packet forwarding:
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# 3. Advertise home subnet and register as Exit Node:
# (Replace 192.168.1.0/24 with your local LAN subnet):
sudo tailscale up --advertise-routes=192.168.1.0/24 --advertise-exit-node
```

* Authenticate your machine using the displayed authentication link.
* Open the [Tailscale Admin Console](https://login.tailscale.com/admin/machines), click **...** next to your Orange Pi 5, select **Edit route settings**, and approve both the subnet and exit node.
* *Install the Tailscale client on your smartphone, enable "Use Exit Node", and browse with zero ads anywhere in the world.*

---

## **7. Step 6: Router DHCP Deployment**

To automatically route all household devices through the shield:
1. Log into your primary router's admin interface (typically `192.168.1.1`).
2. Navigate to **DHCP Server Settings**.
3. Change **Primary DNS Server** to your **Orange Pi 5 Static IP Address**.
4. Save and reboot your router.

---

## **8. Architecture Benefits**

* **Smart TV & Streaming Protection:** Blocks telemetry, smart TV tracking, and intrusive popups before packets hit your screen.
* **Zero Client Overhead:** No background VPN applications draining battery on mobile phones inside the house.
* **True Decentralized Privacy:** Eliminates dependency on ISP DNS servers, preventing ISP metadata harvesting.

# **Zero to Hero Guide for Orange Pi 5: From Unboxing to Your First Project**

> **Who is this guide for?**  
> Anyone who has never used Linux before, has never opened a terminal (black command-line window), or is holding a Single-Board Computer (SBC) for the very first time. Without assuming any prior technical knowledge, this guide walks you from unboxing to running your first edge project.

---

## 🧭 Roadmap: Where We Start & Where We Are Going

```mermaid
flowchart LR
    A["1. Desk Setup<br>(ESD & Clean Power)"] --> B["2. Choosing the OS<br>(Ubuntu BSP Image)"]
    B --> C["3. Flash to SD<br>(BalenaEtcher)"]
    C --> D["4. First Connection<br>(Monitor or SSH)"]
    D --> E["5. Core Linux Skills<br>(Survival Commands)"]
    E --> F["6. Choose a Project<br>(AI, Server, Robotics)"]
```

---

## **Step 1: Unboxing – Preparing Your Desk & Hardware**

You are holding a bare green printed circuit board (PCB) populated with delicate surface-mount chips and exposed solder pads.

### 1. Electrostatic Discharge (ESD) Safety
* Do **not** place or power the board on carpets, wool blankets, or static-prone plastic surfaces.
* Keep the board resting on clean wood, cardboard, or the anti-static packaging box it arrived in.
* Never touch the header pins or bottom traces with bare fingers while the board is plugged in.

### 2. Power Supply: "Can I Use My Phone Charger?"
* **Strict Rule:** Do **not** use standard 5V/2A or 5V/3A mobile phone chargers. When the 8-core CPU spikes or an NVMe drive is accessed, standard phone chargers cause voltage drops (brownouts), triggering sudden shutdowns and reboots.
* **What You Need:** A dedicated **5V / 4A (20 Watt) fixed Type-C power adapter**.
* *(For full power and accessory details, see: [02. Hardware & Accessory Compatibility Guide](02-Hardware-and-Accessory-Compatibility.md))*.

### 3. Networking & Wi-Fi Notice
* **Important Fact:** The baseline Orange Pi 5 model **does NOT feature onboard Wi-Fi or Bluetooth**.
* To connect to the internet, you must plug a standard network cable into the **Gigabit Ethernet port** connected to your home router, or attach a Linux-compatible USB Wi-Fi dongle (e.g., RTL8821CU).

### 4. MicroSD Card Selection
* Use a high-quality MicroSD card (**32 GB or 64 GB minimum**) marked with an **A1** or **A2** application performance rating (e.g., SanDisk Extreme or Samsung EVO Plus).

---

## **Step 2: Operating System Selection (Escaping the Maze)**

When visiting the official Orange Pi download repository, you are confronted with a bewildering array of choices: *Android, OrangePi OS Arch, Droid, Debian, Ubuntu, OpenWRT*.

* **Our Recommended Choice:** **Ubuntu 22.04 LTS Desktop (Rockchip 5.10 or 6.1 BSP Kernel)**.
* **Why?** The 6 TOPS NPU drivers, hardware video decoding (VPU), and all 13 project guides in this repository are benchmarked and verified specifically against this distribution.
* Download the `.img.xz` or `.7z` archive from the official Orange Pi download mirror or Armbian portal and unpack it to extract the raw `.img` file.

---

## **Step 3: Flashing the OS to MicroSD (3 Clicks)**

Download and install the free, cross-platform **BalenaEtcher** software on your computer (Windows or Mac):

1. Insert your MicroSD card into your computer via a USB card reader.
2. Launch BalenaEtcher:
   * **Flash from file:** Select your extracted `.img` file.
   * **Select target:** Choose your MicroSD card *(CAUTION: Double-check you are not selecting your computer's internal primary hard drive!)*.
   * **Flash!** Click the button to begin writing.
3. The writing and verification (checksum) process typically completes within 3 to 5 minutes. Eject the card safely.

---

## **Step 4: Booting Up & Your First Connection**

Insert the flashed MicroSD card into the slot on the underside of the Orange Pi 5 (metal pins facing inward). Connect your Ethernet cable, then plug in the 5V/4A Type-C power supply. The onboard red LED will illuminate solidly, and the green LED will begin blinking.

Choose one of two connection workflows:

### Option A: You Have a Monitor, Keyboard, and Mouse
1. Connect the board to your monitor via an HDMI cable.
2. Plug your keyboard and mouse into the USB ports.
3. The Ubuntu desktop GUI will appear directly on your display.

### Option B: You Don't Have a Monitor (Headless Laptop Connection)
This is the standard, professional method. Ensure your laptop and Orange Pi 5 are connected to the same home local network (router).

1. On your Windows PC, open **PowerShell** or **Command Prompt (CMD)**.
2. Type the following command and press `Enter`:
   ```bash
   ssh orangepi@orangepi5.local
   ```
   *(If `orangepi5.local` fails to resolve on your local router, open your router's web portal at `192.168.1.1` to locate the IP lease assigned to the board, e.g., `ssh orangepi@192.168.1.145`)*.
3. If prompted with `"Are you sure you want to continue connecting (yes/no)?"`, type `yes` and press Enter.
4. **When Prompted for Password:** Type `orangepi` and press Enter.  
   *(Security Note: Linux terminals intentionally suppress password characters; no asterisks `*` or letters will appear as you type. This is expected behavior—simply type the password and hit Enter).*

---

## **Step 5: First-Boot Maintenance (3 Essential Tasks)**

Once logged into your terminal, immediately run these three foundational tasks:

### 1. Update the Default Password
Secure your device on your home network:
```bash
passwd
```
Enter the current password (`orangepi`), then type your new password twice.

### 2. Update System Package Repositories
Synchronize software catalogs with upstream Ubuntu mirrors:
```bash
sudo apt update && sudo apt upgrade -y
```
*(When you see `sudo` at the beginning of a command, the system is executing the task with administrative "Superuser" privileges).*

### 3. Run the Hardware Health Diagnostic
Execute our automated diagnostic utility to audit your board's subsystem health:
```bash
curl -sSL https://raw.githubusercontent.com/muhammetmucahitsoylu/orangepi5-tutorials/main/scripts/check_health.sh | bash
```
Your CPU die temperatures, NPU character nodes, and memory headroom will render on screen.

---

## **Step 6: Terminal Survival Kit (The Core 8 Commands)**

The Linux terminal is simply a **file explorer without a mouse**. Here are the only commands you need to get started:

| Command | Literal Meaning | What Does It Do? | Practical Example |
| :--- | :--- | :--- | :--- |
| `pwd` | *"Where am I?"* | Prints your current working directory path. | `pwd` |
| `ls` | *"What is here?"* | Lists all files and subdirectories in the current folder. | `ls -la` (Includes hidden files) |
| `cd` | *"Change Directory"* | Navigates into another directory. | `cd Desktop` or go back up with `cd ..` |
| `mkdir` | *"Make Directory"* | Creates a new folder. | `mkdir MyProjects` |
| `nano` | *"Text Editor"* | Opens a terminal-based text editor for editing config or code files. | `nano test.txt` *(Save: `Ctrl+O`, Exit: `Ctrl+X`)* |
| `cat` | *"Concatenate"* | Prints the text contents of a file directly to the screen. | `cat /etc/os-release` |
| `htop` | *"Task Manager"* | Displays a real-time monitor of CPU, RAM, and background tasks. | `htop` *(Press `q` to quit)* |
| `sudo reboot` | *"Reboot Board"* | Gracefully restarts the operating system. | `sudo reboot` |

---

## **Step 7: Where to Go Next? (Choose Your Path)**

Congratulations! You have set up your hardware, established a reliable network bridge, and mastered basic Linux terminal commands. You are now fully equipped to tackle the deep-dive guides and projects in this repository:

```mermaid
graph TD
    Start["Orange Pi 5 is Running"] --> Choice{"What would you like to build?"}
    
    Choice -->|"Performance & Speed"| Path1["1. Move to High-Speed NVMe<br>• Ditch slow MicroSD cards<br>• 10x faster boot times"]
    Path1 --> Guide1["Guide 01: SPI Flash & NVMe Boot"]
    
    Choice -->|"AI & Computer Vision"| Path2["2. Edge AI & Neural Engine<br>• Wake up the 6 TOPS NPU<br>• Run 75+ FPS YOLOv8"]
    Path2 --> Proj2["Project 02: NPU Activation"]
    Proj2 --> Proj3["Project 03: YOLOv8 AI Vision"]
    
    Choice -->|"Home Server & Media"| Path3["3. 24/7 Private Cloud<br>• Ad-blocking (AdGuard Home)<br>• Self-hosted Netflix (Jellyfin)"]
    Path3 --> Guide5["Guide 05: Headless Optimization"]
    Guide5 --> Proj11["Project 11: Personal Cloud & Jellyfin"]
    
    Choice -->|"Robotics & Hardware"| Path4["4. GPIO & Physical Computing<br>• Relays, LEDs, Sensors<br>• ROS 2 Robotics Node"]
    Path4 --> Pinout["docs/GPIO_PINOUT.md"]
    Pinout --> Proj8["Project 08: GPIO C++ Control"]
```

### 🔗 Quick Links to Next Projects:
* **For Speed & Storage:** [01. SPI Flash & NVMe Boot Installation Guide](01-Recovery-and-NVMe-Installation.md)
* **For Edge AI:** [02. NPU Activation & RKNN Runtime Setup](../../projects/English/02-NPU-Activation-and-RKNN.md)
* **For Private Cloud & Media:** [11. Personal Cloud & Jellyfin Media Server](../../projects/English/11-Personal-Cloud-Jellyfin.md)
* **For Hardware Pins & Electronics:** [26-Pin GPIO Header Reference & Pinout Guide](../../docs/GPIO_PINOUT.md)

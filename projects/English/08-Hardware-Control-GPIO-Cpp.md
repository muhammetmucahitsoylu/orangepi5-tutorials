# **Orange Pi 5 (RK3588S) Hardware Control and GPIO / C++ Development Guide**

This guide covers interfacing with the Orange Pi 5's 26-pin expansion header using C++ and Python to control LEDs, relays, buttons, sensors, and actuators with zero jitter and professional engineering patterns.

---

## **1. Orange Pi 5 GPIO Architecture & Common Pitfalls**

* **Why RPi.GPIO Fails:** Libraries built specifically for Raspberry Pi (`RPi.GPIO`, legacy `wiringPi`) write directly to memory-mapped registers of Broadcom BCM SoCs. The Orange Pi 5 is powered by the Rockchip RK3588S, which organizes pins across multiple hardware controllers (`gpiochip0` to `gpiochip4`).
* **Pin Naming Scheme:** RK3588 pins are designated by bank and index (e.g., `GPIO1_D2` = GPIO Chip 1, Line 26).
* **Two Modern Approaches:**
  1. **wiringOP:** Xunlong's maintained port of wiringPi for the RK3588S (convenient for C/C++ developers and quick physical pin mapping).
  2. **libgpiod:** The modern Linux kernel character device standard (`/dev/gpiochip*`), eliminating deprecated sysfs interfaces.

---

## **2. 26-Pin Header Pinout Diagram**

Key pin assignments on the Orange Pi 5 physical 26-pin header:

```
                  26-Pin Expansion Header (V1.3.2)
                         ┌────────┐
          3.3V Power [ 1]│  ●  ●  │[ 2]  5V Power
     GPIO1_B7 / PWM13[ 3]│  ●  ●  │[ 4]  5V Power
     GPIO1_B6 / UART1[ 5]│  ●  ●  │[ 6]  GND (Ground)
     GPIO1_C6 / PWM15[ 7]│  ●  ●  │[ 8]  GPIO4_A3 / UART0_TX
         GND (Ground)[ 9]│  ●  ●  │[10]  GPIO4_A4 / UART0_RX
      GPIO4_B2 / CAN1[11]│  ●  ●  │[12]  GPIO0_D5 / CAN2_TX
      GPIO4_B3 / CAN1[13]│  ●  ●  │[14]  GND (Ground)
      GPIO0_D4 / CAN2[15]│  ●  ●  │[16]  GPIO1_D3 / UART4_RX
          3.3V Power [17]│  ●  ●  │[18]  GPIO1_D2 / UART4_TX
  GPIO1_C1 / SPI_MOSI[19]│  ●  ●  │[20]  GND (Ground)
  GPIO1_C0 / SPI_MISO[21]│  ●  ●  │[22]  GPIO2_D4
   GPIO1_C2 / SPI_CLK[23]│  ●  ●  │[24]  GPIO1_C4 / SPI_CS1
         GND (Ground)[25]│  ●  ●  │[26]  GPIO1_A3 / PWM1
                         └────────┘
```

---

## **3. Step 1: Installing wiringOP and Inspecting Pin States**

`wiringOP` provides the indispensable `gpio readall` utility to inspect modes (IN/OUT/ALT) and voltage levels:

```bash
# 1. Clone the repository:
cd /tmp
git clone https://github.com/orangepi-xunlong/wiringOP.git
cd wiringOP

# 2. Build and install:
sudo ./build clean
sudo ./build

# 3. Verify the pin table (Requires root privileges):
sudo gpio readall
```

*The terminal will output a full matrix detailing physical pin numbers, wPi IDs, BCM mappings, and logic states.*

---

## **4. Step 2: C++ Embedded Development with CMake**

Standard CMake structure for high-speed deterministic embedded loops.

### **1. Directory Setup:**
```bash
mkdir -p ~/projects/gpio-cpp/src && cd ~/projects/gpio-cpp
```

### **2. `CMakeLists.txt`:**
```cmake
cmake_minimum_required(VERSION 3.10)
project(OrangePi_Hardware_Control CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Link against wiringPi/wiringOP
find_library(WIRINGOP_LIB wiringPi PATHS /usr/local/lib /usr/lib)

add_executable(hardware_app src/main.cpp)
target_link_libraries(hardware_app PRIVATE ${WIRINGOP_LIB} pthread)
```

### **3. C++ Source Code (`src/main.cpp`):**
Blinks an LED on Pin 7 (wiringOP Pin 2 / GPIO1_C6) and samples button state on Pin 11 (wiringOP Pin 5 / GPIO4_B2) with internal pull-up:

```cpp
#include <iostream>
#include <chrono>
#include <thread>
#include <wiringPi.h>

#define LED_PIN    2   // Physical Pin 7 (GPIO1_C6 - wiringOP 2)
#define BUTTON_PIN 5   // Physical Pin 11 (GPIO4_B2 - wiringOP 5)

int main() {
    std::cout << "--- Orange Pi 5 Hardware Control (C++) ---" << std::endl;

    // 1. Initialize wiringOP runtime
    if (wiringPiSetup() == -1) {
        std::cerr << "Failed to initialize wiringPi!" << std::endl;
        return 1;
    }

    // 2. Set pin directions
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT);
    pullUpDnControl(BUTTON_PIN, PUD_UP); // Enable internal pull-up resistor

    std::cout << "LED and button loop started. Press Ctrl+C to abort." << std::endl;

    for (int i = 0; i < 10; ++i) {
        int btn_state = digitalRead(BUTTON_PIN);
        if (btn_state == LOW) {
            std::cout << "Button Pressed!" << std::endl;
        }

        digitalWrite(LED_PIN, HIGH);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        digitalWrite(LED_PIN, LOW);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    return 0;
}
```

### **4. Compilation & Execution:**
```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Execute with root permissions for memory-mapped I/O access:
sudo ./hardware_app
```

---

## **5. Step 3: Modern Linux Kernel Standard: Python & `libgpiod`**

For upstream compatibility without third-party compiling, use character-device `libgpiod`:

```bash
sudo apt update && sudo apt install -y gpiod libgpiod-dev python3-libgpiod
```

### **Python Pin Control Script (`led_control.py`):**
```python
import gpiod
import time

# RK3588S GPIO1 controller (/dev/gpiochip1)
CHIP_NUM = 1
# GPIO1_C6 = line 22 (Physical Pin 7)
LINE_NUM = 22

chip = gpiod.Chip(f"gpiochip{CHIP_NUM}")
line = chip.get_line(LINE_NUM)

# Request output mode
config = gpiod.line_request()
config.consumer = "LED_Test"
config.request_type = gpiod.line_request.DIRECTION_OUTPUT

line.request(config)

try:
    print("Blinking LED via kernel libgpiod...")
    for _ in range(5):
        line.set_value(1) # HIGH (3.3V)
        time.sleep(0.5)
        line.set_value(0) # LOW (0V)
        time.sleep(0.5)
finally:
    line.release()
    chip.close()
    print("Pin resource released safely.")
```

### **Run Python Script:**
```bash
# Execute with sudo for gpiochip character device access:
sudo python3 led_control.py
```

---

## **6. I2C Bus Detection & Peripherals**

To communicate with I2C sensors (e.g. BMP280, MPU6050, SSD1306 OLED screens):

```bash
# 1. Install I2C inspection utilities:
sudo apt install -y i2c-tools

# 2. Probe the I2C bus:
sudo i2cdetect -y -r 1
```

*An active peripheral will report its hexadecimal address (e.g., `0x3c` for OLED or `0x68` for IMU) ready for communication.*

---

## **7. Summary**

* For deterministic, high-throughput robotics or motor loops, use **C++ with wiringOP and CMake**.
* For system daemons, microservices, and general scripts, leverage **libgpiod** for maximum upstream kernel stability.
* Ensure execution users belong to the `gpio` group or run with appropriate access privileges.

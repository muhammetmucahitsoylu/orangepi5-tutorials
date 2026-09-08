# Orange Pi 5 (RK3588S) 26-Pin GPIO Header Reference & Pinout Guide

> Complete physical pinout mapping, subsystem multiplexing (I2C, SPI, UART, PWM), and programming cheat sheet for the **Orange Pi 5 (Rockchip RK3588S)** 26-pin expansion header.

---

## 1. Physical 26-Pin Header Diagram

```
                              ORANGE PI 5 (26-PIN HEADER)
                                     Top View
                               +-------------------+
                       3.3V DC | [01]   |   [02]   | +5.0V DC (VCC)
            I2C6_SDA / GPIO0_B5 | [03]   |   [04]   | +5.0V DC (VCC)
            I2C6_SCL / GPIO0_B6 | [05]   |   [06]   | GROUND (GND)
             PWM3_M0 / GPIO0_C4 | [07]   |   [08]   | UART2_TX / GPIO0_C1
                    GROUND (GND)| [09]   |   [10]   | UART2_RX / GPIO0_C0
             PWM4_M0 / GPIO1_A0 | [11]   |   [12]   | GPIO1_A1 / PWM5_M0
             PWM6_M0 / GPIO1_A2 | [13]   |   [14]   | GROUND (GND)
             PWM7_M0 / GPIO1_A3 | [15]   |   [16]   | GPIO1_A4 / SPI4_CS0
                       3.3V DC | [17]   |   [18]   | GPIO1_A5 / SPI4_MISO
            SPI4_MOSI / GPIO1_A6 | [19]   |   [20]   | GROUND (GND)
            SPI4_CLK  / GPIO1_A7 | [21]   |   [22]   | GPIO1_B0
            I2C5_SDA  / GPIO3_C4 | [23]   |   [24]   | GPIO3_C5 / I2C5_SCL
                    GROUND (GND)| [25]   |   [26]   | GPIO3_D0
                               +-------------------+
```

---

## 2. Comprehensive Pin Mapping Table

> [!WARNING]
> **Voltage Warning:** All GPIO data pins on the Orange Pi 5 operate at **3.3V TTL logic levels**. Connecting 5V digital signals directly to any GPIO pin will permanently destroy the SoC I/O pad. Always use a level shifter.

| Physical Pin | Default Function | WiringOP ID | Linux `libgpiod` Chip & Offset | Linux Sysfs GPIO Index | Alternate Function 1 | Alternate Function 2 |
| :---: | :--- | :---: | :--- | :---: | :--- | :--- |
| **01** | **+3.3V Power** | — | — | — | DC Power Rail (Max 500mA) | — |
| **02** | **+5.0V Power** | — | — | — | DC Power Rail (Direct from Type-C) | — |
| **03** | **GPIO0_B5** | 8 | `gpiochip0` Line 13 | 13 | **I2C6_SDA** | — |
| **04** | **+5.0V Power** | — | — | — | DC Power Rail (Direct from Type-C) | — |
| **05** | **GPIO0_B6** | 9 | `gpiochip0` Line 14 | 14 | **I2C6_SCL** | — |
| **06** | **Ground (GND)**| — | — | — | 0V Ground Reference | — |
| **07** | **GPIO0_C4** | 7 | `gpiochip0` Line 20 | 20 | **PWM3_M0** | — |
| **08** | **GPIO0_C1** | 15 | `gpiochip0` Line 17 | 17 | **UART2_TX** (Debug Console) | — |
| **09** | **Ground (GND)**| — | — | — | 0V Ground Reference | — |
| **10** | **GPIO0_C0** | 16 | `gpiochip0` Line 16 | 16 | **UART2_RX** (Debug Console) | — |
| **11** | **GPIO1_A0** | 0 | `gpiochip1` Line 0 | 32 | **PWM4_M0** | — |
| **12** | **GPIO1_A1** | 1 | `gpiochip1` Line 1 | 33 | **PWM5_M0** | — |
| **13** | **GPIO1_A2** | 2 | `gpiochip1` Line 2 | 34 | **PWM6_M0** | — |
| **14** | **Ground (GND)**| — | — | — | 0V Ground Reference | — |
| **15** | **GPIO1_A3** | 3 | `gpiochip1` Line 3 | 35 | **PWM7_M0** | — |
| **16** | **GPIO1_A4** | 4 | `gpiochip1` Line 4 | 36 | **SPI4_CS0_M1** | — |
| **17** | **+3.3V Power** | — | — | — | DC Power Rail | — |
| **18** | **GPIO1_A5** | 5 | `gpiochip1` Line 5 | 37 | **SPI4_MISO_M1** | — |
| **19** | **GPIO1_A6** | 12 | `gpiochip1` Line 6 | 38 | **SPI4_MOSI_M1** | — |
| **20** | **Ground (GND)**| — | — | — | 0V Ground Reference | — |
| **21** | **GPIO1_A7** | 14 | `gpiochip1` Line 7 | 39 | **SPI4_CLK_M1** | — |
| **22** | **GPIO1_B0** | 6 | `gpiochip1` Line 8 | 40 | — | — |
| **23** | **GPIO3_C4** | 10 | `gpiochip3` Line 20 | 116 | **I2C5_SDA** | — |
| **24** | **GPIO3_C5** | 11 | `gpiochip3` Line 21 | 117 | **I2C5_SCL** | — |
| **25** | **Ground (GND)**| — | — | — | 0V Ground Reference | — |
| **26** | **GPIO3_D0** | 13 | `gpiochip3` Line 24 | 120 | — | — |

---

## 3. Sysfs Calculation Formula

In the Linux kernel, global GPIO numbers follow this formula:
$$\text{GPIO Index} = (\text{Bank Number} \times 32) + (\text{Port Letter} \times 8) + \text{Pin Number}$$
Where:
* **Port Letter Index:** `A = 0`, `B = 1`, `C = 2`, `D = 3`.
* **Example (`GPIO1_A2`):** $(1 \times 32) + (0 \times 8) + 2 = \mathbf{34}$.
* **Example (`GPIO3_C4`):** $(3 \times 32) + (2 \times 8) + 4 = 96 + 16 + 4 = \mathbf{116}$.

---

## 4. Programming Snippets

### A. Bash (`gpiod` Modern Linux Standard)
```bash
# Install tool
sudo apt install -y gpiod

# Inspect all available GPIO chips
gpiodetect

# Toggle Pin 11 (GPIO1_A0 -> gpiochip1 offset 0) HIGH then LOW
gpioset gpiochip1 0=1
sleep 1
gpioset gpiochip1 0=0

# Read state of Pin 12 (GPIO1_A1 -> gpiochip1 offset 1)
gpioget gpiochip1 1
```

### B. C++ (`wiringOP`)
```cpp
#include <wiringPi.h>
#include <iostream>

#define LED_PIN 0 // Physical Pin 11 (GPIO1_A0)

int main() {
    if (wiringPiSetup() == -1) {
        std::cerr << "wiringPi initialization failed!" << std::endl;
        return 1;
    }
    
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH); // 3.3V Active
    delay(1000);
    digitalWrite(LED_PIN, LOW);  // 0V Inactive
    return 0;
}
```

### C. Python 3 (`gpiod`)
```python
import gpiod
import time

chip = gpiod.Chip("gpiochip1")
line = chip.get_line(0) # Physical Pin 11
line.request(consumer="LED_Test", type=gpiod.LINE_REQ_DIR_OUT)

try:
    line.set_value(1) # HIGH
    time.sleep(1)
    line.set_value(0) # LOW
finally:
    line.release()
```

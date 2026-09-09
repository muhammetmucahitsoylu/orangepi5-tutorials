# **Orange Pi 5 (RK3588S) Donanım Kontrolü ve GPIO / C++ Geliştirme Rehberi**

Bu rehber; Orange Pi 5'in 26-pin genişleme konnektörünü kullanarak sensörler, röleler, butonlar ve motorlar gibi harici donanımları C++ ve Python ile profesyonel düzeyde kontrol etmeniz için hazırlanmıştır.

---

## **1. Orange Pi 5 GPIO Mimarisi ve Karşılaşılan Zorluklar**

* **RPi.GPIO Neden Çalışmaz?** Raspberry Pi için yazılmış kütüphaneler (`RPi.GPIO`, `wiringPi`), Broadcom BCM yongalarına göre donanım register'larına doğrudan erişir. Orange Pi 5 ise Rockchip RK3588S işlemcisine sahiptir ve pinler Linux çekirdeğinin modern `libgpiod` alt sistemi üzerinden yönetilir.
* **Pin İsimlendirme Farkı:** RK3588 üzerinde pinler port ve banka şeklinde adlandırılır (Örn: `GPIO1_D2` = GPIO Chip 1, Line 26).
* **İki Standart Çözüm:**
  1. **wiringOP:** Raspberry Pi'nin `wiringPi` kütüphanesine alışkın olanlar için Orange Pi 5 uyarlaması (hızlı C/C++ geliştirme ve pin numaralandırma tablosu için).
  2. **libgpiod:** Modern Linux çekirdek standardı (karakter aygıtı `/dev/gpiochip*` üzerinden doğrudan ve kararlı erişim).

---

## **2. 26-Pin Başlık Düzeni ve Pinout Şeması**

Orange Pi 5'in fiziksel 26-pin başlığındaki en kritik pinler:

```
                  26-Pin Genişleme Başlığı (V1.3.2)
                         ┌────────┐
          3.3V Güç [ 1]  │  ●  ●  │  [ 2]  5V Güç
   GPIO1_B7 / PWM13 [ 3]  │  ●  ●  │  [ 4]  5V Güç
   GPIO1_B6 / UART1 [ 5]  │  ●  ●  │  [ 6]  GND (Toprak)
   GPIO1_C6 / PWM15 [ 7]  │  ●  ●  │  [ 8]  GPIO4_A3 / UART0_TX
        GND (Toprak) [ 9]  │  ●  ●  │  [10]  GPIO4_A4 / UART0_RX
    GPIO4_B2 / CAN1 [11]  │  ●  ●  │  [12]  GPIO0_D5 / CAN2_TX
    GPIO4_B3 / CAN1 [13]  │  ●  ●  │  [14]  GND (Toprak)
    GPIO0_D4 / CAN2 [15]  │  ●  ●  │  [16]  GPIO1_D3 / UART4_RX
          3.3V Güç [17]  │  ●  ●  │  [18]  GPIO1_D2 / UART4_TX
 GPIO1_C1 / SPI_MOSI [19]  │  ●  ●  │  [20]  GND (Toprak)
 GPIO1_C0 / SPI_MISO [21]  │  ●  ●  │  [22]  GPIO2_D4
  GPIO1_C2 / SPI_CLK [23]  │  ●  ●  │  [24]  GPIO1_C4 / SPI_CS1
        GND (Toprak) [25]  │  ●  ●  │  [26]  GPIO1_A3 / PWM1
                         └────────┘
```

---

## **3. Adım 1: wiringOP Kurulumu ve Pin Tablosunu Görüntüleme**

`wiringOP`, pinlerin anlık voltajlarını, modlarını (IN/OUT/ALT) ve fiziksel pin karşılıklarını terminalden görmenizi sağlar:

```bash
# 1. Depoyu klonlayın:
cd /tmp
git clone https://github.com/orangepi-xunlong/wiringOP.git
cd wiringOP

# 2. Derleyin ve sisteme kurun:
sudo ./build clean
sudo ./build

# 3. Pin tablosunu doğrulayın (Root yetkisi gereklidir):
sudo gpio readall
```

*Terminalde 26 pinin tamamını, wPi numaralarını, BCM karşılıklarını ve voltaj seviyelerini listeleyen tablo belirecektir.*

---

## **4. Adım 2: C++ ile Donanım Projesi Geliştirme (CMake Mimarisi)**

Profesyonel gömülü projelerde standart C++ ve CMake mimarisi kullanılır.

### **1. Proje Dizin Yapısı:**
```bash
mkdir -p ~/projects/gpio-cpp/src && cd ~/projects/gpio-cpp
```

### **2. `CMakeLists.txt` Dosyasını Oluşturun:**
```cmake
cmake_minimum_required(VERSION 3.10)
project(OrangePi_Hardware_Control CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# wiringPi/wiringOP kütüphanesini bağlayın
find_library(WIRINGOP_LIB wiringPi PATHS /usr/local/lib /usr/lib)

add_executable(hardware_app src/main.cpp)
target_link_libraries(hardware_app PRIVATE ${WIRINGOP_LIB} pthread)
```

### **3. C++ Kaynak Kodu (`src/main.cpp`):**
Pin 7 (wiringOP Pin 2 / GPIO1_C6) üzerine bağlı bir LED'i yakıp söndüren ve Pin 11 (wiringOP Pin 5 / GPIO4_B2) üzerindeki buton durumunu okuyan kod:

```cpp
#include <iostream>
#include <chrono>
#include <thread>
#include <wiringPi.h>

#define LED_PIN    2   // Fiziksel Pin 7 (GPIO1_C6 - wiringOP 2)
#define BUTTON_PIN 5   // Fiziksel Pin 11 (GPIO4_B2 - wiringOP 5)

int main() {
    std::cout << "--- Orange Pi 5 Donanım Kontrolü (C++) ---" << std::endl;

    // 1. wiringOP motorunu başlat
    if (wiringPiSetup() == -1) {
        std::cerr << "wiringPi başlatılamadı!" << std::endl;
        return 1;
    }

    // 2. Pin yönlerini belirle
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT);
    pullUpDnControl(BUTTON_PIN, PUD_UP); // Dahili Pull-Up direncini aç

    std::cout << "LED ve Buton döngüsü başladı. Çıkmak için Ctrl+C." << std::endl;

    for (int i = 0; i < 10; ++i) {
        // Buton basılı mı kontrol et (Pull-up olduğu için basılınca 0 döner)
        int btn_state = digitalRead(BUTTON_PIN);
        if (btn_state == LOW) {
            std::cout << "Butona basıldı!" << std::endl;
        }

        // LED'i yak
        digitalWrite(LED_PIN, HIGH);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        // LED'i söndür
        digitalWrite(LED_PIN, LOW);
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }

    return 0;
}
```

### **4. Derleme ve Çalıştırma:**
```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Donanım pin erişimi için sudo ile çalıştırın:
sudo ./hardware_app
```

---

## **5. Adım 3: Modern Linux Çekirdek Standardı: Python ve `libgpiod`**

Sistemde harici kütüphane derlemeden, en güncel Linux çekirdeği standardıyla GPIO kontrolü:

```bash
sudo apt update && sudo apt install -y gpiod libgpiod-dev python3-libgpiod
```

### **Python ile Pin Kontrolü (`led_control.py`):**
```python
import gpiod
import time

# RK3588S GPIO1 çipi (/dev/gpiochip1)
CHIP_NUM = 1
# GPIO1_C6 = 22. line (Fiziksel Pin 7)
LINE_NUM = 22

chip = gpiod.Chip(f"gpiochip{CHIP_NUM}")
line = chip.get_line(LINE_NUM)

# Çıkış modu olarak ayarla
config = gpiod.line_request()
config.consumer = "LED_Test"
config.request_type = gpiod.line_request.DIRECTION_OUTPUT

line.request(config)

try:
    print("LED kontrolü aktif (libgpiod)...")
    for _ in range(5):
        line.set_value(1) # HIGH (3.3V)
        time.sleep(0.5)
        line.set_value(0) # LOW (0V)
        time.sleep(0.5)
finally:
    line.release()
    chip.close()
    print("Pin serbest bırakıldı.")
```

### **Python Betiğini Çalıştırın:**
```bash
# Donanım gpiochip karakter aygıtına erişim için sudo ile çalıştırın:
sudo python3 led_control.py
```

---

## **6. I2C Sensörlerini ve Cihazlarını Aktifleştirme**

I2C veri yolunu (örneğin bir sıcaklık sensörü veya 0.96" OLED ekran) kullanmak için Linux donanım ağacı (Device Tree Overlay) aktif olmalıdır:

```bash
# 1. I2C donanım paketlerini kurun:
sudo apt install -y i2c-tools

# 2. Bağlı I2C cihazlarını tarayın (Bus 1 veya Bus 5):
sudo i2cdetect -y -r 1
```

*Ekranda `0x3c` (OLED) veya `0x68` (MPU6050 jiroskop) gibi adresler listelendiğinde sensörünüz doğrudan kullanıma hazırdır.*

---

## **7. Özet**

* C++ projelerinde yüksek hızlı döngüler ve düşük gecikme için **wiringOP + CMake** tercih edin.
* Standart sistem servisleri ve Python betiklerinde çekirdek güvenliği için **libgpiod** kullanın.
* Tüm donanım pin operasyonları için ilgili kullanıcının `gpio` grubuna dahil olduğundan veya uygulamanın `sudo` ile başlatıldığından emin olun.

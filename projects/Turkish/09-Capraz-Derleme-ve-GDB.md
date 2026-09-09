# **Orange Pi 5 (RK3588S) Çapraz Derleme (Cross-Compilation) ve Uzaktan Hata Ayıklama Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar ve kodlar **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)** üzerinde bizzat fiziksel donanımda test edilmiş ve onaylanmıştır.

Bu rehber; x86_64 mimarili bir geliştirici bilgisayarı (Ubuntu Linux veya WSL2) üzerinde kod yazıp, **ARM64 (aarch64) GNU toolchain** ve **CMake** ile Orange Pi 5 (RK3588S) için saniyeler içinde derleme yapmayı, ikili dosyayı (binary) otomatik olarak karta yüklemeyi ve **gdbserver / VS Code** ile uzaktan satır satır hata ayıklamayı (remote debugging) anlatır.

---

## **1. Neden Çapraz Derleme (Cross-Compilation)?**

Gömülü Linux dünyasında doğrudan hedef kart üzerinde derleme yapmak (native compilation) büyük projelerde ciddi darboğazlar yaratır:

* **Derleme Hızı:** Güçlü bir x86_64 masaüstü işlemcisi (Intel i7/i9 veya AMD Ryzen), büyük C/C++ projelerini veya OpenCV gibi kütüphaneleri Orange Pi 5'in ARM çekirdeklerine kıyasla 5 ila 15 kat daha hızlı derler.
* **NVMe / SD Kart Ömrü:** Saatler süren devasa derlemeler, kartın flaş depolama biriminde yüksek okuma/yazma aşınmasına (TBW tüketimine) yol açar.
* **Mühendislik İş Akışı:** Savunma sanayii, otomotiv ve robotik sektörlerindeki gömülü yazılım takımlarının %95'i kodu x86 host üzerinde derler ve karta otomatik gönderip test eder.

```
┌────────────────────────────────────────────────────────┐
│  Geliştirici Bilgisayarı (x86_64 Host: Linux / WSL2)   │
│  - Kodlama (VS Code / CLion)                           │
│  - aarch64-linux-gnu-g++ (Cross Toolchain)             │
│  - CMake (Toolchain File) -> ARM64 ELF Binary Üretimi  │
└──────────────────────────┬─────────────────────────────┘
                           │ 
                           │ 1. Otomatik Dağıtım (rsync / ssh)
                           │ 2. Uzaktan Hata Ayıklama (GDB Port 2000)
                           ▼
┌────────────────────────────────────────────────────────┐
│  Hedef Cihaz (Orange Pi 5: RK3588S ARM64 Target)       │
│  - gdbserver :2000 ./app                               │
│  - Donanım & Sensör Kontrolü / Doğrulama               │
└────────────────────────────────────────────────────────┘
```

---

## **2. Kritik Mühendislik Tuzağı: `glibc` Sürüm Uyuşmazlığı**

Çapraz derlemeye başlamadan önce bilinmesi gereken **en kritik kural**:
* **Kural:** Host (PC) üzerindeki çapraz derleyicinin bağlandığı `glibc` sürümü, hedefteki (Orange Pi 5) `glibc` sürümünden **daha yeni olamaz**.
* **Senaryo:** Hem host bilgisayarınızda hem Orange Pi 5'inizde **Ubuntu 24.04 LTS (glibc 2.39)** kuruluysa derlenen binary tam uyumla çalışır. Ancak hedef kartınızda eski bir sistem (örn: Ubuntu 22.04 glibc 2.35) varken host'ta 24.04 kullanırsanız; derlediğiniz binary kartta şu hatayla patlar:
  ```
  ./app: /lib/aarch64-linux-gnu/libc.so.6: version 'GLIBC_2.38' not found (required by ./app)
  ```
* **Doğrulama Adımı:** Orange Pi 5 terminalinde şu komutla kurulu glibc sürümünü öğrenin:
  ```bash
  ldd --version
  ```
  *(Örn: Ubuntu 24.04 üzerinde `ldd (Ubuntu GLIBC 2.39-0ubuntu8.x) 2.39` dönecektir; host geliştirme ortamınızın da Ubuntu 24.04 LTS veya eşdeğer WSL2/Docker olması önerilir).*

---

## **3. Adım 1: Host PC Üzerinde Çapraz Derleme Araçlarını Kurma**

Geliştirici bilgisayarınızda (Ubuntu 24.04 LTS veya eşdeğer WSL2/Linux) çapraz derleme paketlerini kurun:

```bash
# Paket listesini güncelleyin
sudo apt update

# aarch64 C/C++ derleyicisi, çoklu mimari GDB ve rsync kurulumu
sudo apt install -y build-essential \
                    gcc-aarch64-linux-gnu \
                    g++-aarch64-linux-gnu \
                    gdb-multiarch \
                    cmake \
                    rsync \
                    ssh
```

Kurulumu doğrulayın:
```bash
aarch64-linux-gnu-g++ --version
```
*Çıktıda `aarch64-linux-gnu-g++ (Ubuntu ...) x.x.x` satırını görmelisiniz.*

---

## **4. Adım 2: CMake Toolchain Dosyası ve Donanım Bayrakları**

Orange Pi 5'in RK3588S işlemcisi, 4 adet yüksek performanslı **Cortex-A76** ve 4 adet verimlilik odaklı **Cortex-A55** çekirdeğine (ARMv8.2-A mimarisi) sahiptir. Derleme sırasında işlemcinin FP16 (Half-Precision) ve Neon SIMD birimlerini tam kapasite kullanması için özel optimizasyon bayrakları tanımlanmalıdır.

### **1. Proje Dizinini Hazırlayın (Host PC):**
```bash
mkdir -p ~/orangepi_ws/cross_demo/src
cd ~/orangepi_ws/cross_demo
```

### **2. `aarch64-toolchain.cmake` Dosyasını Oluşturun:**
```cmake
# aarch64-toolchain.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Çapraz derleyicilerin yolları
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

# RK3588S ARMv8.2-A Donanım Optimizasyon Bayrakları
# Neon SIMD, Donanımsal FP16 ve big.LITTLE Cortex-A76 / A55 çekirdek ayarı
set(OPTIMIZATION_FLAGS "-march=armv8.2-a+crypto+fp16 -mtune=cortex-a76.cortex-a55 -O3")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OPTIMIZATION_FLAGS}" CACHE STRING "" FORCE)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OPTIMIZATION_FLAGS}" CACHE STRING "" FORCE)

# Arama davranışını sadece hedef kütüphanelerle sınırlandır
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

---

## **5. Adım 3: C++ Test Uygulaması ve `CMakeLists.txt`**

İşlemci mimarisini ve çekirdek bilgilerini doğrulayan modern bir C++17 uygulaması oluşturalım.

### **1. `src/main.cpp`:**
```cpp
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <sys/utsname.h>

int main() {
    std::cout << "==================================================" << std::endl;
    std::cout << " Orange Pi 5 (RK3588S) Çapraz Derleme Testi       " << std::endl;
    std::cout << "==================================================" << std::endl;

    // Sistem mimarisini oku
    struct utsname sys_info;
    if (uname(&sys_info) == 0) {
        std::cout << "[+] Sistem:     " << sys_info.sysname << " " << sys_info.release << std::endl;
        std::cout << "[+] Mimari:     " << sys_info.machine << std::endl;
        std::cout << "[+] Hostname:   " << sys_info.nodename << std::endl;
    }

    // Donanımsal çekirdek kapasitesi
    unsigned int cores = std::thread::hardware_concurrency();
    std::cout << "[+] CPU Çekirdek Sayısı: " << cores << " (Cortex-A76 + Cortex-A55)" << std::endl;

    // Basit bir matematiksel hesaplama (FP16 / Neon testi için)
    double sum = 0.0;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 10'000'000; ++i) {
        sum += (i * 0.0001);
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> elapsed = end - start;

    std::cout << "[+] Hesaplama Sonucu: " << sum << std::endl;
    std::cout << "[+] Geçen Süre: " << elapsed.count() << " ms" << std::endl;
    std::cout << "==================================================" << std::endl;

    return 0;
}
```

### **2. `CMakeLists.txt`:**
```cmake
cmake_minimum_required(VERSION 3.16)
project(OrangePi_CrossCompile_Demo CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(opi5_app src/main.cpp)
target_link_libraries(opi5_app PRIVATE pthread)
```

---

## **6. Adım 4: Host Üzerinde Derleme ve İkili Dosya Doğrulama**

```bash
# Derleme klasörünü oluşturun
cd ~/orangepi_ws/cross_demo
mkdir build && cd build

# Toolchain dosyası ile CMake'i yapılandırın
cmake -DCMAKE_TOOLCHAIN_FILE=../aarch64-toolchain.cmake ..

# Derlemeyi başlatın
make -j$(nproc)
```

### **Mimari Doğrulama (Kritik Adım):**
Üretilen ikili dosyanın gerçekten ARM64 mimarisine ait olduğunu host üzerinde `file` komutu ile doğrulayın:
```bash
file opi5_app
```
**Beklenen Çıktı:**
```text
opi5_app: ELF 64-bit LSB pie executable, ARM aarch64, version 1 (SYSV), dynamically linked, ... for GNU/Linux 3.7.0, not stripped
```
*(Eğer çıktıda `x86-64` görüyorsanız toolchain dosyası parametresi verilmemiş demektir).*

---

## **7. Adım 5: Otomatik Dağıtım (Deployment Script)**

Derlenen ikili dosyanın tek bir komutla Orange Pi 5'e gönderilmesi için bir dağıtım betiği oluşturalım:

```bash
# build dizinindeyken deploy.sh oluşturun
cat << 'EOF' > deploy.sh
#!/bin/bash
TARGET_IP="192.168.1.150"    # Orange Pi 5'inizin IP adresi
TARGET_USER="orangepi"       # Kullanıcı adınız
TARGET_DIR="~/apps"          # Hedef dizin

if [ ! -f "opi5_app" ]; then
    echo "[-] Hata: opi5_app ikili dosyası bulunamadı! Önce 'make' çalıştırın."
    exit 1
fi

echo "[*] Hedef karta yükleniyor: ${TARGET_USER}@${TARGET_IP}:${TARGET_DIR} ..."
ssh ${TARGET_USER}@${TARGET_IP} "mkdir -p ${TARGET_DIR}"
rsync -avz --progress opi5_app ${TARGET_USER}@${TARGET_IP}:${TARGET_DIR}/

echo "[+] Yükleme tamamlandı. Çalıştırmak için:"
echo "    ssh ${TARGET_USER}@${TARGET_IP} '${TARGET_DIR}/opi5_app'"
EOF

chmod +x deploy.sh
```

*(Kendi Orange Pi 5 IP adresinizi ve kullanıcı adınızı yazıp `./deploy.sh` ile doğrudan yükleyebilirsiniz).*

---

## **8. Adım 6: Uzaktan Hata Ayıklama (Remote Debugging with GDB)**

Gömülü cihazlarda oluşan bellek sızıntıları, `segmentation fault` veya mantık hatalarını doğrudan host bilgisayarınızdaki IDE üzerinden satır satır debug edebilirsiniz.

### **1. Orange Pi 5 Üzerinde `gdbserver` Kurulumu ve Başlatılması:**
Hedef kartta (Orange Pi 5 terminalinde):
```bash
sudo apt update && sudo apt install -y gdbserver

# Uygulamayı 2000 portu üzerinden hata ayıklama modunda başlatın:
gdbserver :2000 ~/apps/opi5_app
```
*Terminalde `Process ~/apps/opi5_app created; pid = ...` ve `Listening on port 2000` satırı bekleyecektir.*

---

### **2. Host PC Üzerinden `gdb-multiarch` ile Bağlantı:**
Host bilgisayarınızda (derleme yaptığınız `build` dizininde):
```bash
gdb-multiarch opi5_app
```

GDB terminalinde şu komutları sırasıyla çalıştırın:
```text
(gdb) target remote 192.168.1.150:2000
(gdb) break main
(gdb) continue
```
*Program Orange Pi 5 üzerinde çalışmaya başlar ve `main` fonksiyonunun ilk satırında durur. Host terminalinden `next`, `step`, `print sys_info` gibi komutlarla donanım üzerindeki değişkenleri canlı canlı inceleyebilirsiniz!*

---

### **3. Profesyonel Yöntem: VS Code ile Tek Tuşla (F5) Debug Yapılandırması**

Host bilgisayarınızdaki VS Code'da `.vscode/launch.json` dosyasına şu bloğu ekleyerek görsel arayüz üzerinden breakpoint koyup F5 ile hata ayıklayabilirsiniz:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Orange Pi 5 Remote Debug (C++)",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/build/opi5_app",
            "miDebuggerServerAddress": "192.168.1.150:2000",
            "miDebuggerPath": "/usr/bin/gdb-multiarch",
            "cwd": "${workspaceFolder}",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "GDB pretty-printing aç",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ]
        }
    ]
}
```

---

## **9. İleri Düzey: Harici Kütüphaneleri (Sysroot) Çapraz Bağlama**

Eğer uygulamanız Orange Pi 5 üzerindeki harici kütüphanelere (örneğin `wiringOP`, `librknpu2` veya `OpenCV`) ihtiyaç duyuyorsa, host makinenin bu kütüphanelerin header ve `.so` dosyalarını görmesi gerekir.

### **Sysroot Senkronizasyonu (Host PC):**
```bash
# 1. Host üzerinde bir sysroot klasörü oluşturun
mkdir -p ~/orangepi_sysroot

# 2. Kartın kütüphane ve header dizinlerini hosta kopyalayın
rsync -avz --safe-links orangepi@192.168.1.150:/lib ~/orangepi_sysroot/
rsync -avz --safe-links orangepi@192.168.1.150:/usr/include ~/orangepi_sysroot/usr/
rsync -avz --safe-links orangepi@192.168.1.150:/usr/lib ~/orangepi_sysroot/usr/
```

### **`aarch64-toolchain.cmake` Güncellemesi:**
Toolchain dosyanıza `CMAKE_SYSROOT` yolunu ekleyin:
```cmake
set(CMAKE_SYSROOT /home/KULLANICI_ADINIZ/orangepi_sysroot)
```
*Böylece host derleyicisi, Orange Pi 5 üzerindeki tüm yüklü kütüphaneleri sanki kendi yerelinde kuruluymuş gibi hatasız bağlar (link eder).*

---

## **10. Sık Karşılaşılan Hatalar ve Çözüm Tablosu**

| Hata Mesajı | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| `GLIBC_X.XX not found` | Host'un glibc sürümü Orange Pi'den daha yeni. | Host'u Orange Pi ile aynı Ubuntu sürümüne (örn: 22.04 LTS) çekin veya Docker içinde derleyin. |
| `cannot execute binary file: Exec format error` | Yanlışlıkla x86_64 için derlendi. | `file <binary>` çıktısını kontrol edin, `CMAKE_TOOLCHAIN_FILE` yolunun doğru verildiğinden emin olun. |
| `Connection refused` (gdbserver) | Hedef kartta `gdbserver` başlatılmamış veya güvenlik duvarı portu engelliyor. | Orange Pi'de `gdbserver :2000 ./app` komutunu çalıştırın ve `sudo ufw allow 2000` uygulayın. |
| `cannot open shared object file: No such file or directory` | Kart üzerinde gerekli runtime `.so` dosyası kurulu değil. | Eksik kütüphaneyi Orange Pi üzerinde `sudo apt install` ile kurun veya derleme sırasında `-static-libstdc++` kullanın. |

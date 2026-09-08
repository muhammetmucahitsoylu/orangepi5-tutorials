# 🍊 Orange Pi 5 (RK3588S) Field Notes & Tutorials

[Türkçe](#türkçe) | [English](#english)

---

## Türkçe

Orange Pi 5 (Rockchip RK3588S) tek kart bilgisayarı için sahada bizzat test edilmiş, teknik neden-sonuç analizleriyle zenginleştirilmiş kurtarma protokolleri, bootloader onarımları ve kurulum rehberleri.

### 📚 Kılavuzlar ve Rehberler

| Kılavuz | Açıklama |
| :--- | :--- | 
| [**SPI Flash & U-Boot Kurtarma / NVMe Boot**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Kurtarma%20ve%20Kurulum%20Kılavuzu.md) | EDK2 UEFI kilitlenmesinden resmi U-Boot'a dönüş, MaskROM onarımı ve M.2 NVMe SSD'ye doğrudan ağ üzerinden yazım. |
| [**Donanım & Aksesuar Uyumluluk Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Donanım%20ve%20Aksesuar%20Uyumluluk%20Kılavuzu.md) | 5V/4A güç beslemesi, M.2 PCIe 2.0 x1 hat sınırları, uyumlu NVMe modelleri ve termal çözümler. |
| [**Donanım Doğrulama & Stres Testi Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Donanım%20Doğrulama%20ve%20Stres%20Testi%20Kılavuzu.md) | CPU tepe güç ölçümü, RAM bant genişliği, fio ile NVMe hız testi ve termal kararlılık doğrulama protokolü. |
| [**Tarayıcı & Video Hızlandırma Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Tarayıcı%20ve%20Donanımsal%20Video%20Hızlandırma%20Kılavuzu.md) | Chromium'da donanımsal VPU hızlandırma açma, 4K YouTube takılmalarını önleme ve CPU yükünü düşürme. |
| [**Sabit MAC & IP Yapılandırma Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Sabit%20MAC%20Adresi%20ve%20IP%20Yapılandırma%20Rehberi.md) | Her yeniden başlamada rastgele değişen MAC adresi sorununu çözme ve NetworkManager ile kalıcı statik IP atama. |
| [**Ekransız (Headless) Sunucu Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Ekransız%20Sunucu%20ve%20İlk%20Kurulum%20Optimizasyon%20Rehberi.md) | 7/24 ev sunucusu için GUI kapatma (500MB+ RAM kazanımı), ZRAM sıkıştırılmış takas alanı, NTP ve kalıcı governor servisi. |
| [**Docker & Donanım Hızlandırma Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Docker%20Kurulumu%20ve%20Donanım%20Hızlandırma%20Rehberi.md) | Temiz Docker kurulumu, cgroup bellek uyarısı çözümü ve Jellyfin/Plex için VPU/GPU donanımsal transcode izinleri. |
| [**Uzaktan Erişim & Masaüstü Bağlantı Rehberi**](guides/Turkish/Orange%20Pi%205%20(RK3588S)%20Uzaktan%20Erişim%20ve%20Masaüstü%20Bağlantı%20Rehberi.md) | SSH/CMD terminal bağlantısı, şifresiz SSH anahtarı, UART seri port (1.5M baud) ve Windows RDP/VNC/NoMachine ile masaüstü kontrolü. |

### 🚀 Yazılımcı Projeleri ve Yapay Zeka Rehberleri

| Proje / Rehber | Açıklama |
| :--- | :--- | 
| [**IDE ve Geliştirme Ortamı Kurulumu**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20Yazılımcılar%20İçin%20IDE%20ve%20Geliştirme%20Ortamı%20Kurulumu.md) | VS Code Remote - SSH, tarayıcı tabanlı Code-Server, Python sanal ortamı (venv) ve proje mimarisi. |
| [**NPU Aktivasyonu & RKNN Kurulumu**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20NPU%20Aktivasyonu%20ve%20RKNN%20Çalışma%20Ortamı%20Kurulumu.md) | 3 çekirdekli 6 TOPS NPU'yu uyandırma, librknpu2 entegrasyonu, RKNN-Lite2 ve 3 çekirdek telemetri testi. |
| [**İlk Yapay Zeka Projesi: YOLOv8 NPU**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20İlk%20Yapay%20Zeka%20Projesi%20ve%20YOLOv8%20NPU%20Çıkarımı.md) | Bilgisayarda ONNX/RKNN derleme, 3 çekirdekli NPU ile 70+ FPS nesne tanıma ve donanım kıyaslaması. |
| [**Donanım Kontrolü ve GPIO / C++**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20Donanım%20Kontrolü%20ve%20GPIO-C++%20Geliştirme%20Rehberi.md) | 26-pin başlık şeması, wiringOP ile C++/CMake mimarisi, buton/LED kontrolü, libgpiod ve I2C sensörleri. |
| [**NPU ile Yerel Dil Modeli (RKLLM / Qwen)**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20NPU%20ile%20Yerel%20Dil%20Modeli%20(RKLLM%20ve%20Qwen)%20Kurulumu.md) | 6 TOPS NPU üzerinde internetsiz Qwen-1.5B/3B çalıştırma, W4A16 kuantizasyon, 18+ token/s akıcı sohbet. |
| [**Çevrimdışı Sesli Asistan (Whisper & Piper)**](projects/Turkish/Orange%20Pi%205%20(RK3588S)%20Çevrimdışı%20Sesli%20Asistan%20(Whisper%20ve%20Piper%20TTS)%20Projesi.md) | %100 yerel sesli asistan: faster-whisper (STT) + RKLLM zekası + Piper TTS doğal Türkçe ses sentezi (<1s gecikme). |

### 🛠️ Kılavuz Yazım İlkeleri

* **Bizzat Doğrulanmış Çözümler:** Yalnızca teorik değil, doğrudan donanım üzerinde karşılaşılan ve çözüme kavuşturulan senaryolar.
* **Firmware ve Donanım Analizi:** Sorunun sadece nasıl çözüleceği değil; MaskROM, PCIe hatları ve SPI Flash mimarisi seviyesindeki teknik nedenleri.
* **Doğrudan Uygulanabilirlik:** Hızlı ve güvenli kopyala-çalıştır komut blokları.

### 📁 Dizin Yapısı

```
OrangePi5_Tutorials/
├── .gitignore
├── LICENSE
├── README.md
├── guides/
│   ├── English/
│   │   ├── Orange Pi 5 (RK3588S) Recovery and Installation Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Hardware and Accessory Compatibility Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Hardware Verification and Stress Testing Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Browser and Hardware Video Acceleration Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Headless Server and Initial Optimization Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide.md
│   │   └── Orange Pi 5 (RK3588S) Remote Access and Desktop Connection Guide.md
│   ├── Turkish/
│   │   ├── Orange Pi 5 (RK3588S) Kurtarma ve Kurulum Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Donanım ve Aksesuar Uyumluluk Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Donanım Doğrulama ve Stres Testi Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Tarayıcı ve Donanımsal Video Hızlandırma Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi.md
│   │   ├── Orange Pi 5 (RK3588S) Ekransız Sunucu ve İlk Kurulum Optimizasyon Rehberi.md
│   │   ├── Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi.md
│   │   └── Orange Pi 5 (RK3588S) Uzaktan Erişim ve Masaüstü Bağlantı Rehberi.md
│   └── assets/
└── projects/
    ├── English/
    │   ├── Orange Pi 5 (RK3588S) IDE and Development Environment Setup for Developers.md
    │   ├── Orange Pi 5 (RK3588S) NPU Activation and RKNN Runtime Setup Guide.md
    │   ├── Orange Pi 5 (RK3588S) First AI Project and YOLOv8 NPU Inference Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware Control and GPIO-C++ Development Guide.md
    │   ├── Orange Pi 5 (RK3588S) Local LLM on NPU with RKLLM and Qwen Guide.md
    │   └── Orange Pi 5 (RK3588S) Offline Voice Assistant with Whisper and Piper TTS Guide.md
    └── Turkish/
        ├── Orange Pi 5 (RK3588S) Yazılımcılar İçin IDE ve Geliştirme Ortamı Kurulumu.md
        ├── Orange Pi 5 (RK3588S) NPU Aktivasyonu ve RKNN Çalışma Ortamı Kurulumu.md
        ├── Orange Pi 5 (RK3588S) İlk Yapay Zeka Projesi ve YOLOv8 NPU Çıkarımı.md
        ├── Orange Pi 5 (RK3588S) Donanım Kontrolü ve GPIO-C++ Geliştirme Rehberi.md
        ├── Orange Pi 5 (RK3588S) NPU ile Yerel Dil Modeli (RKLLM ve Qwen) Kurulumu.md
        └── Orange Pi 5 (RK3588S) Çevrimdışı Sesli Asistan (Whisper ve Piper TTS) Projesi.md
```

### 📄 Lisans

Bu projedeki tüm kılavuzlar ve içerikler **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International ([CC BY-NC-ND 4.0](LICENSE))** lisansı ile korunmaktadır.
* **Kişisel Kullanım & Uygulama:** Serbesttir.
* **Paylaşım:** Yazar (`Muhammet Mücahit Soylu`) ve orijinal depo bağlantısı belirtilerek serbesttir.
* **Türev İçerik Üretimi & Ticari Kullanım:** Yasaktır (içerik değiştirilerek başka platformlarda kendi eseri gibi yayımlanamaz veya ticari amaçla kullanılamaz).

## English

Field-tested recovery protocols, bootloader restorations, and setup guides enriched with technical root-cause analyses for the Orange Pi 5 (Rockchip RK3588S) single-board computer.

### 📚 Guides & Tutorials

| Guide | Description |
| :--- | :--- | 
| [**SPI Flash & U-Boot Recovery / NVMe Boot**](guides/English/Orange%20Pi%205%20(RK3588S)%20Recovery%20and%20Installation%20Guide.md) | Restoring official U-Boot from EDK2 UEFI lockups, MaskROM recovery, and direct network streaming to M.2 NVMe SSD. |
| [**Hardware & Accessory Compatibility Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Hardware%20and%20Accessory%20Compatibility%20Guide.md) | 5V/4A power supply requirements, M.2 PCIe 2.0 x1 bus limits, compatible NVMe SSDs, and thermal solutions. |
| [**Hardware Verification & Stress Testing Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Hardware%20Verification%20and%20Stress%20Testing%20Guide.md) | CPU prime compute, RAM bandwidth, fio NVMe throughput testing, and thermal saturation verification protocol. |
| [**Browser & Video Acceleration Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Browser%20and%20Hardware%20Video%20Acceleration%20Guide.md) | Enabling VPU hardware acceleration in Chromium, fixing 4K YouTube stutter, and reducing CPU load. |
| [**Fixed MAC & Static IP Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Fixed%20MAC%20Address%20and%20Static%20IP%20Guide.md) | Resolving randomized MAC addresses on boot and pinning persistent local static IP via NetworkManager. |
| [**Headless Server & Optimization Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Headless%20Server%20and%20Initial%20Optimization%20Guide.md) | 24/7 server setup: disabling GUI (reclaiming 500MB+ RAM), ZRAM swap setup, NTP sync, and boot performance service. |
| [**Docker & Hardware Acceleration Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Docker%20Installation%20and%20Hardware%20Acceleration%20Guide.md) | Clean upstream Docker setup, fixing cgroup memory limits, and passing VPU/GPU nodes into containers (Jellyfin/Plex). |
| [**Remote Access & Desktop Connection Guide**](guides/English/Orange%20Pi%205%20(RK3588S)%20Remote%20Access%20and%20Desktop%20Connection%20Guide.md) | Terminal access via SSH/CMD, passwordless SSH keys, UART serial (1.5M baud), and Windows RDP/VNC/NoMachine graphical desktop streaming. |

### 🚀 Developer Projects & AI Guides

| Project / Guide | Description |
| :--- | :--- | 
| [**IDE & Development Environment Setup**](projects/English/Orange%20Pi%205%20(RK3588S)%20IDE%20and%20Development%20Environment%20Setup%20for%20Developers.md) | VS Code Remote - SSH workflow, browser-based Code-Server, isolated Python venvs, and build toolchains. |
| [**NPU Activation & RKNN Runtime Setup**](projects/English/Orange%20Pi%205%20(RK3588S)%20NPU%20Activation%20and%20RKNN%20Runtime%20Setup%20Guide.md) | Waking up the 3-core 6 TOPS NPU, librknpu2 integration, RKNN-Lite2, and multi-core telemetry validation. |
| [**First AI Project: YOLOv8 NPU**](projects/English/Orange%20Pi%205%20(RK3588S)%20First%20AI%20Project%20and%20YOLOv8%20NPU%20Inference%20Guide.md) | Host-side ONNX/RKNN compilation, 3-core NPU deployment, 70+ FPS object detection, and hardware benchmarks. |
| [**Hardware Control & GPIO / C++**](projects/English/Orange%20Pi%205%20(RK3588S)%20Hardware%20Control%20and%20GPIO-C++%20Development%20Guide.md) | 26-pin header diagram, wiringOP with C++/CMake, button/LED interfacing, libgpiod, and I2C peripherals. |
| [**Local LLM on NPU (RKLLM / Qwen)**](projects/English/Orange%20Pi%205%20(RK3588S)%20Local%20LLM%20on%20NPU%20with%20RKLLM%20and%20Qwen%20Guide.md) | Running offline Qwen-1.5B/3B on the 6 TOPS NPU, W4A16 quantization, and 18+ tokens/sec streaming response. |
| [**Offline Voice Assistant (Whisper & Piper)**](projects/English/Orange%20Pi%205%20(RK3588S)%20Offline%20Voice%20Assistant%20with%20Whisper%20and%20Piper%20TTS%20Guide.md) | 100% private voice assistant: faster-whisper (STT) + RKLLM reasoning + Piper TTS neural synthesis (<1s round-trip). |

### 🛠️ Guide Principles

* **Field-Verified Solutions:** Practical scenarios encountered and resolved directly on physical hardware, rather than purely theoretical steps.
* **Firmware & Hardware Analysis:** Explanations that cover not only how to solve the problem, but also the underlying technical root causes across MaskROM, PCIe lanes, and SPI Flash architecture.
* **Direct Execution:** Fast, safe, and copy-paste-ready command blocks.

### 📁 Directory Structure

```
OrangePi5_Tutorials/
├── .gitignore
├── LICENSE
├── README.md
├── guides/
│   ├── English/
│   │   ├── Orange Pi 5 (RK3588S) Recovery and Installation Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Hardware and Accessory Compatibility Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Hardware Verification and Stress Testing Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Browser and Hardware Video Acceleration Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Headless Server and Initial Optimization Guide.md
│   │   ├── Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide.md
│   │   └── Orange Pi 5 (RK3588S) Remote Access and Desktop Connection Guide.md
│   ├── Turkish/
│   │   ├── Orange Pi 5 (RK3588S) Kurtarma ve Kurulum Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Donanım ve Aksesuar Uyumluluk Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Donanım Doğrulama ve Stres Testi Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Tarayıcı ve Donanımsal Video Hızlandırma Kılavuzu.md
│   │   ├── Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi.md
│   │   ├── Orange Pi 5 (RK3588S) Ekransız Sunucu ve İlk Kurulum Optimizasyon Rehberi.md
│   │   ├── Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi.md
│   │   └── Orange Pi 5 (RK3588S) Uzaktan Erişim ve Masaüstü Bağlantı Rehberi.md
│   └── assets/
└── projects/
    ├── English/
    │   ├── Orange Pi 5 (RK3588S) IDE and Development Environment Setup for Developers.md
    │   ├── Orange Pi 5 (RK3588S) NPU Activation and RKNN Runtime Setup Guide.md
    │   ├── Orange Pi 5 (RK3588S) First AI Project and YOLOv8 NPU Inference Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware Control and GPIO-C++ Development Guide.md
    │   ├── Orange Pi 5 (RK3588S) Local LLM on NPU with RKLLM and Qwen Guide.md
    │   └── Orange Pi 5 (RK3588S) Offline Voice Assistant with Whisper and Piper TTS Guide.md
    └── Turkish/
        ├── Orange Pi 5 (RK3588S) Yazılımcılar İçin IDE ve Geliştirme Ortamı Kurulumu.md
        ├── Orange Pi 5 (RK3588S) NPU Aktivasyonu ve RKNN Çalışma Ortamı Kurulumu.md
        ├── Orange Pi 5 (RK3588S) İlk Yapay Zeka Projesi ve YOLOv8 NPU Çıkarımı.md
        ├── Orange Pi 5 (RK3588S) Donanım Kontrolü ve GPIO-C++ Geliştirme Rehberi.md
        ├── Orange Pi 5 (RK3588S) NPU ile Yerel Dil Modeli (RKLLM ve Qwen) Kurulumu.md
        └── Orange Pi 5 (RK3588S) Çevrimdışı Sesli Asistan (Whisper ve Piper TTS) Projesi.md
```

### 📄 License

All guides and documentation in this repository are protected under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International ([CC BY-NC-ND 4.0](LICENSE))** license.
* **Personal Learning & Execution:** Free and open.
* **Sharing:** Allowed only with clear attribution to the author (`Muhammet Mücahit Soylu`) and original repository link.
* **Derivative Works & Commercial Exploitation:** Strictly prohibited (materials may not be remixed, altered, republished as personal content, or used for commercial purposes).

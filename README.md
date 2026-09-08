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
└── guides/
    ├── English/
    │   ├── Orange Pi 5 (RK3588S) Recovery and Installation Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware and Accessory Compatibility Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware Verification and Stress Testing Guide.md
    │   ├── Orange Pi 5 (RK3588S) Browser and Hardware Video Acceleration Guide.md
    │   ├── Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide.md
    │   ├── Orange Pi 5 (RK3588S) Headless Server and Initial Optimization Guide.md
    │   ├── Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide.md
    │   └── Orange Pi 5 (RK3588S) Remote Access and Desktop Connection Guide.md
    ├── Turkish/
    │   ├── Orange Pi 5 (RK3588S) Kurtarma ve Kurulum Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Donanım ve Aksesuar Uyumluluk Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Donanım Doğrulama ve Stres Testi Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Tarayıcı ve Donanımsal Video Hızlandırma Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi.md
    │   ├── Orange Pi 5 (RK3588S) Ekransız Sunucu ve İlk Kurulum Optimizasyon Rehberi.md
    │   ├── Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi.md
    │   └── Orange Pi 5 (RK3588S) Uzaktan Erişim ve Masaüstü Bağlantı Rehberi.md
    └── assets/
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
└── guides/
    ├── English/
    │   ├── Orange Pi 5 (RK3588S) Recovery and Installation Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware and Accessory Compatibility Guide.md
    │   ├── Orange Pi 5 (RK3588S) Hardware Verification and Stress Testing Guide.md
    │   ├── Orange Pi 5 (RK3588S) Browser and Hardware Video Acceleration Guide.md
    │   ├── Orange Pi 5 (RK3588S) Fixed MAC Address and Static IP Guide.md
    │   ├── Orange Pi 5 (RK3588S) Headless Server and Initial Optimization Guide.md
    │   ├── Orange Pi 5 (RK3588S) Docker Installation and Hardware Acceleration Guide.md
    │   └── Orange Pi 5 (RK3588S) Remote Access and Desktop Connection Guide.md
    ├── Turkish/
    │   ├── Orange Pi 5 (RK3588S) Kurtarma ve Kurulum Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Donanım ve Aksesuar Uyumluluk Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Donanım Doğrulama ve Stres Testi Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Tarayıcı ve Donanımsal Video Hızlandırma Kılavuzu.md
    │   ├── Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi.md
    │   ├── Orange Pi 5 (RK3588S) Ekransız Sunucu ve İlk Kurulum Optimizasyon Rehberi.md
    │   ├── Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi.md
    │   └── Orange Pi 5 (RK3588S) Uzaktan Erişim ve Masaüstü Bağlantı Rehberi.md
    └── assets/
```

### 📄 License

All guides and documentation in this repository are protected under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International ([CC BY-NC-ND 4.0](LICENSE))** license.
* **Personal Learning & Execution:** Free and open.
* **Sharing:** Allowed only with clear attribution to the author (`Muhammet Mücahit Soylu`) and original repository link.
* **Derivative Works & Commercial Exploitation:** Strictly prohibited (materials may not be remixed, altered, republished as personal content, or used for commercial purposes).

# 🍊 Orange Pi 5 (RK3588S) Field Notes & Tutorials

[Türkçe](#türkçe) | [English](#english)

---

## Türkçe

Orange Pi 5 (Rockchip RK3588S) tek kart bilgisayarı için sahada bizzat test edilmiş, teknik neden-sonuç analizleriyle zenginleştirilmiş kurtarma protokolleri, bootloader onarımları ve kurulum rehberleri.

### 📚 Kılavuzlar ve Rehberler

| Kılavuz | Açıklama | Seviye | Durum |
| :--- | :--- | :---: | :---: |
| [**SPI Flash & U-Boot Kurtarma / NVMe Boot**](guides/orangepi5-spi-uboot-recovery.md) | EDK2 UEFI kilitlenmesinden resmi U-Boot'a dönüş, MaskROM onarımı ve M.2 NVMe SSD'ye doğrudan ağ üzerinden yazım. | İleri | Doğrulandı ✅ |

### 🛠️ Kılavuz Yazım İlkeleri

* **Bizzat Doğrulanmış Çözümler:** Yalnızca teorik değil, doğrudan donanım üzerinde karşılaşılan ve çözüme kavuşturulan senaryolar.
* **Firmware ve Donanım Analizi:** Sorunun sadece nasıl çözüleceği değil; MaskROM, PCIe hatları ve SPI Flash mimarisi seviyesindeki teknik nedenleri.
* **Doğrudan Uygulanabilirlik:** Hızlı ve güvenli kopyala-çalıştır komut blokları.

### 📁 Dizin Yapısı

OrangePi5_Tutorials/
├── .gitignore
├── LICENSE
├── README.md
└── guides/
    ├── orangepi5-spi-uboot-recovery.md
    └── assets/
    

## English

Field-tested recovery protocols, bootloader restorations, and setup guides enriched with technical root-cause analyses for the Orange Pi 5 (Rockchip RK3588S) single-board computer.

### 📚 Guides & Tutorials

| Guide | Description | Level | Status |
| :--- | :--- | :---: | :---: |
| [**SPI Flash & U-Boot Recovery / NVMe Boot**](guides/orangepi5-spi-uboot-recovery.md) | Restoring official U-Boot from EDK2 UEFI lockups, MaskROM recovery, and direct network streaming to M.2 NVMe SSD.

### 🛠️ Guide Principles

* **Field-Verified Solutions:** Practical scenarios encountered and resolved directly on physical hardware, rather than purely theoretical steps.
* **Firmware & Hardware Analysis:** Explanations that cover not only how to solve the problem, but also the underlying technical root causes across MaskROM, PCIe lanes, and SPI Flash architecture.
* **Direct Execution:** Fast, safe, and copy-paste-ready command blocks.

### 📁 Directory Structure

OrangePi5_Tutorials/
├── .gitignore
├── LICENSE
├── README.md
└── guides/
    ├── orangepi5-spi-uboot-recovery.md
    └── assets/

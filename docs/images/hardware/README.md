# 📸 Orange Pi 5 (V1.3.2) Physical Hardware Photography & Annotated Schematics

Bu dizin, **Orange Pi 5 (RK3588S V1.3.2)** donanımına ait yüksek çözünürlüklü, oklarla etiketlenmiş fiziksel fotoğrafları ve resmi pin bağlantı şemalarını içerir.

This directory contains high-resolution, arrow-annotated hardware photography and official pinout schematics for the **Orange Pi 5 (Rockchip RK3588S V1.3.2)**.

---

## 📷 Donanım Fotoğraf & Şema Kataloğu | Hardware Visual Catalog

| Görsel / Preview | Dosya / File | Açıklama & Etiketler (TR) | Description & Annotations (EN) |
| :---: | :--- | :--- | :--- |
| <img src="opi5_front.png" width="260" alt="Orange Pi 5 Front" /> | [`opi5_front.png`](opi5_front.png) | **Ön Yüz (Top View) - Oklarla Etiketli:**<br>• RK3588S 8-Çekirdek 2.4GHz SoC<br>• 2GB/4GB/8GB LPDDR4/4X RAM<br>• PMU (RK806-1 Güç Yönetimi)<br>• **MaskROM Butonu** (Kurtarma modu)<br>• **RECOVERY Butonu**<br>• **16MB SPI FLASH** (U-Boot belleği)<br>• 3-Pin Debug TTL UART (TX, RX, GND)<br>• 26-Pin GPIO Başlığı<br>• 1x GbE LAN (YT8531C Kontrolcü)<br>• USB 3.0 / USB 2.0 Portları<br>• USB 3.1 Type-C + 5V/4A Type-C Güç Girişi<br>• HDMI Çıkışı, 3.5mm Ses Jakı, Mikrofon<br>• CAM1 & CAM3 MIPI Kamera, LCD2 Ekran<br>• 5V Fan ve MicroSD Kart Yuvası | **Front View - Annotated with Arrows:**<br>• Rockchip RK3588S Octa-core 2.4GHz SoC<br>• 2GB/4GB/8GB LPDDR4/4X RAM<br>• RK806-1 Power Management IC (PMU)<br>• **MaskROM Key** (Hardware recovery)<br>• **RECOVERY Key**<br>• **16MB SPI FLASH** (U-Boot storage)<br>• 3-Pin Dedicated Debug TTL UART<br>• 26-Pin Multi-function GPIO Header<br>• 1x GbE LAN (YT8531C controller)<br>• USB 3.0 / USB 2.0 Ports<br>• USB 3.1 Type-C + Type-C DC-IN (5V/4A)<br>• HDMI OUT, 3.5mm Audio In/Out, MIC<br>• CAM1 & CAM3 MIPI CSI, LCD2 MIPI DSI<br>• 5V Fan Connector, MicroSD Slot |
| <img src="opi5_rear.png" width="260" alt="Orange Pi 5 Rear" /> | [`opi5_rear.png`](opi5_rear.png) | **Arka Yüz (Bottom View) - Oklarla Etiketli:**<br>• **M.2 PCIe 2.0 M-Key Yuvası** (2242 NVMe SSD desteği)<br>• **ES8388 Ses Kodek Çipi** (Everest Semi)<br>• **RTC Batarya Bağlantısı** (Gerçek Zaman Saati)<br>• **LCD1 MIPI DSI Ekran Portu**<br>• **Camera2 (CAM2 MIPI CSI Portu)**<br>• Kart Fiziksel Boyutları: **100mm x 62mm** | **Rear View - Annotated with Arrows:**<br>• **M.2 PCIe 2.0 M-Key Slot** (Supports 2242 NVMe SSD)<br>• **ES8388 Audio Codec IC** (Everest Semiconductor)<br>• **RTC Connector** (Real-Time Clock battery circuit)<br>• **LCD1 MIPI DSI Display Port**<br>• **Camera2 (CAM2 MIPI CSI Port)**<br>• Physical Board Dimensions: **100mm x 62mm** |
| <img src="opi5_pin_definition.png" width="260" alt="Orange Pi 5 Pinout" /> | [`opi5_pin_definition.png`](opi5_pin_definition.png) | **Resmi Pin Tanımlama Şeması:** 26-Pin GPIO ve 3-Pin Debug UART portlarının renk kodlu fonksiyon ve sinyal haritası. | **Official Pin Definition Diagram:** Full color-coded signal and multiplexing pinout for 26-pin header and 3-pin UART. |
| <img src="opi5_angle_lan.png" width="260" alt="Orange Pi 5 LAN Angle" /> | [`opi5_angle_lan.png`](opi5_angle_lan.png) | **45° LAN / USB Açısı:** RJ45 Gigabit Ethernet, çift katlı USB 3.0/2.0 konnektörü ve pin yerleşimi. | **45° Isometric View (LAN / USB):** Gigabit RJ45 LAN, stacked USB 3.0/2.0 jack, and header layout. |
| <img src="opi5_angle_hdmi.png" width="260" alt="Orange Pi 5 HDMI Angle" /> | [`opi5_angle_hdmi.png`](opi5_angle_hdmi.png) | **45° HDMI / Type-C Açısı:** DC-IN güç portu, OTG Type-C, HDMI ve 3.5mm ses jakı yerleşimi. | **45° Isometric View (HDMI / Type-C):** DC-IN power jack, OTG Type-C, HDMI OUT, and 3.5mm audio socket. |

---

### ⚖️ Yasal Feragatname & Atıf | Legal Disclaimer & Fair Use

* **Ticari Markalar:** *Orange Pi™*, Shenzhen Xunlong Software CO., Limited'ın tescilli ticari markasıdır. *Rockchip™*, Rockchip Electronics Co., Ltd.'nin tescilli ticari markasıdır.
* **Adil Kullanım:** Bu dizindeki anakart görselleri ve pin şemaları, donanım kullanıcılarına ve geliştiricilerine açık kaynaklı teknik dokümantasyon, kurtarma kılavuzu ve eğitim materyali sunmak amacıyla dönüştürülerek (oklar, fonksiyon etiketleri ve şemalar eklenerek) **Adil Kullanım (Fair Use - 17 U.S.C. § 107)** ilkeleri doğrultusunda kullanılmıştır.
* **Trademarks & Fair Use:** *Orange Pi™* is a registered trademark of Shenzhen Xunlong Software CO., Limited. All hardware photos and schematics in this catalog are annotated and provided strictly for non-commercial, educational documentation, and hardware interoperability purposes under Fair Use.



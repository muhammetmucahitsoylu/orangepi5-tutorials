# **Orange Pi 5 (RK3588S) Retro Oyun Konsolu ve 1080p 60FPS Emülasyon Rehberi**

Bu rehber; Orange Pi 5'in güçlü **Mali-G610 MP4 GPU**'sunu ve 8 çekirdekli işlemcisini kullanarak, oturma odanızdaki televizyonda **PlayStation 2, PSP, GameCube, Wii ve Dreamcast** oyunlarını **1080p çözünürlükte ve takılmasız 60 FPS** hızında oynatan bir retro oyun konsolu inşa etmeyi anlatır.

---

## **1. Donanım ve Emülasyon Gücü: Raspberry Pi vs. Orange Pi 5**

Standart bir Raspberry Pi 4/5 ile PS2 veya GameCube oyunlarını akıcı oynamak donanımsal olarak imkansızdır. Orange Pi 5 ise sahip olduğu ARM Mali-G610 MP4 grafik yongası ve Vulkan 1.2 desteğiyle bu sınırları tamamen aşar:

* **PlayStation 2 (AetherSX2 / PCSX2 ARM):** 2x Çözünürlük (1080p) ile kasmadan 60 FPS (Vulkan motoru ile).
* **PlayStation Portable (PPSSPP):** 4x Çözünürlükte (Full HD 1080p) mükemmel 60 FPS.
* **Nintendo GameCube & Wii (Dolphin):** 2x Çözünürlükte akıcı 60 FPS.
* **Arcade, PS1, N64, Dreamcast, SNES:** Sıfır gecikme ve tam kare hızı.

```
[ TV / Monitör (HDMI) ] 
         ▲
         │ (1080p 60FPS Ses & Görüntü)
[ Orange Pi 5 (RK3588S) ]
 ├── Mali-G610 GPU (Vulkan 1.2 Donanımsal Grafik Motoru)
 ├── EmulationStation / RetroArch / AetherSX2 (PS2) / PPSSPP
 └── Bluetooth / USB Oyun Kolları (DualShock 3/4, Xbox, 8BitDo)
```

---

## **2. Yöntem Seçimi: Hangisini Tercih Etmelisiniz?**

1. **Yöntem 1: Batocera / Rocknix (Önerilen - Saf Konsol Deneyimi):**
   * Ayrı bir MicroSD karta doğrudan Batocera OS yazılır.
   * Kart açıldığında doğrudan şık, konsol benzeri **EmulationStation** arayüzü açılır. Kumanda veya oyun koluyla her şey kontrol edilir.
2. **Yöntem 2: Ubuntu Masaüstü Üzerine Emülatör Kurulumu (Çok Amaçlı Kullanım):**
   * Mevcut işletim sisteminizi silmeden, Ubuntu üzerinde doğrudan RetroArch, PPSSPP ve AetherSX2 çalıştırılır.

---

## **3. Adım 1: Yöntem 1 — Batocera / Rocknix ile Saf Konsol Kurulumu**

Eğer kartı televizyonun altına koyup sadece oyun oynamak istiyorsanız en temiz yol budur:

1. [Rocknix / Batocera for RK3588](https://rocknix.org/) resmi indirme sayfasına gidin.
2. `Orange Pi 5 (RK3588S)` için hazırlanmış güncel `.img.gz` imajını bilgisayarınıza indirin.
3. **BalenaEtcher** veya **Raspberry Pi Imager** ile bir MicroSD karta yazdırın.
4. Kartı Orange Pi 5'e takıp HDMI ile televizyona bağlayın ve güç verin.
5. Sistem ilk açılışta dosya sistemini genişletip otomatik olarak konsol arayüzünü açacaktır.

---

## **4. Adım 2: Yöntem 2 — Ubuntu Üzerinde Emülasyon ve Vulkan Hızlandırma**

Mevcut Ubuntu sisteminizde en yüksek grafik performansını almak için Mali GPU donanım hızlandırmasını ve Vulkan kütüphanelerini yapılandırın:

### **1. Grafik Sürücüleri ve Emülatör Bağımlılıkları:**
```bash
sudo apt update && sudo apt install -y \
  libvulkan1 \
  vulkan-tools \
  mesa-vulkan-drivers \
  retroarch \
  joystick \
  evtest
```

### **2. GPU Frekansını ve İşlemciyi Maksimum Performansa Sabitleme:**
Emülatörlerin kare atlamasını önlemek için frekans kısma mekanizmasını kapatıp performans moduna alın:

```bash
# CPU governor'ı performansa çekin:
echo performance | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor

# Mali GPU frekansını maksimuma (1.0 GHz) sabitleyin:
echo performance | sudo tee /sys/class/devfreq/fb000000.gpu/governor
```

---

## **5. Adım 3: PlayStation 2 (AetherSX2) Kurulumu**

AetherSX2, ARM64 işlemciler ve Mali GPU'lar için optimize edilmiş en güçlü PS2 emülatörüdür:

```bash
# 1. AetherSX2 ARM64 Linux AppImage dosyasını indirin:
mkdir -p ~/Emulators/PS2 && cd ~/Emulators/PS2
wget https://github.com/aethersx2/aethersx2/releases/download/v1.5-4248/AetherSX2-v1.5-4248-aarch64.AppImage

# 2. Çalıştırma izni verin:
chmod +x AetherSX2-v1.5-4248-aarch64.AppImage
```

### **AetherSX2 Kritik Grafik Ayarları:**
* **Graphics Renderer:** Mutlaka **Vulkan** seçilmelidir (OpenGL'e göre %40 daha yüksek FPS verir).
* **Upscale Multiplier:** **2x Native (~720p/1080p)** seçin.
* **Aspect Ratio:** TV'niz için **16:9** veya orijinal **4:3** tercih edin.

---

## **6. Adım 4: Oyun Kolları (DualShock 3 / 4, Xbox, 8BitDo) Bağlantısı**

### **DualShock 3 (PS3 Kolu) Bağlantısı:**
1. Standart Orange Pi 5'te dahili Bluetooth olmadığından kartınıza bir **USB Bluetooth Adaptörü** takın (kablolu oynayacaksanız doğrudan Mini-USB kablosunu takın).
2. Kolu Mini-USB kablosuyla Orange Pi 5'e bağlayın.
3. Linux çekirdeğindeki `hid-sony` sürücüsü eşleşme anahtarını kol hafızasına yazacaktır (`dmesg | grep -i sony` ile doğrulayın).
4. Kabloyu çıkarıp ortadaki **PS tuşuna** basın; 1. oyuncu ledi sabit yanacak ve kol kablosuz bağlanacaktır.

### **DualShock 4 / Xbox / 8BitDo (Standart Bluetooth Eşleşmesi):**
```bash
bluetoothctl
# Konsol içinde:
scan on
# Kolu eşleşme moduna alın (DS4 için Share + PS tuşuna basılı tutun)
# Kolun MAC adresini gördükten sonra:
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
exit
```

---

## **7. Adım 5: BIOS Dosyaları ve ROM Yönetimi**

Emülatörlerin çalışabilmesi için ilgili konsolların yasal BIOS dosyaları gereklidir:

* **PlayStation 2:** `scph39001.bin` veya `scph10000.bin` dosyasını `~/Emulators/PS2/bios/` dizinine atın.
* **ROM Dosyaları:** `.iso`, `.chd` veya `.cso` formatındaki oyunlarınızı M.2 NVMe SSD üzerinde bir klasöre aktarın (Örn: `/DATA/Games/PS2`).

> [!TIP]
> Daha önce kurduğumuz [Samba Paylaşımı](11-Kisisel-Bulut-Jellyfin.md) sayesinde, bilgisayarınızdan ağ üzerinden `\\ORANGE_PI_IP\OrangePi_Depo\Games` klasörüne oyunlarınızı doğrudan sürükleyip bırakabilirsiniz.

---

## **8. Gerçek Donanım Performans Tablosu**

| Oyun ve Konsol | Çözünürlük | Grafik Motoru | Ortalama Kare Hızı (FPS) | Durum |
| :--- | :--- | :--- | :--- | :--- |
| **God of War II (PS2)** | 2x (1080p) | Vulkan | **55 – 60 FPS** | Mükemmel Akıcılık |
| **Gran Turismo 4 (PS2)** | 2x (1080p) | Vulkan | **60 FPS** | Tam Hız |
| **GTA: San Andreas (PS2)** | 2x (1080p) | Vulkan | **60 FPS** | Kusursuz |
| **God of War: Chains of Olympus (PSP)** | 4x (1080p) | Vulkan | **60 FPS** | Kristal Netlik |
| **Super Smash Bros. Melee (GameCube)** | 2x (1080p) | Vulkan | **60 FPS** | Sıfır Gecikme |
| **Tekken 3 (PS1 / DuckStation)** | 5x (1080p) | OpenGL/Vulkan | **60 FPS** | Mükemmel |

> [!CAUTION]
> PS2 ve GameCube emülasyonu sırasında GPU ve CPU çekirdekleri yüksek saat hızlarında çalışır. Çip sıcaklığının 80°C üzerine çıkıp hız kesmemesi (throttling) için kart üzerinde **aktif bir fanlı soğutucu** bulunması şarttır.

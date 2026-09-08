# **Orange Pi 5 (RK3588S) Kişisel Bulut ve Jellyfin Donanımsal Medya Sunucusu**

Bu rehber; Orange Pi 5'inizi Google Drive, Google Photos ve Netflix'e bağımlılığı ortadan kaldıran, M.2 NVMe SSD üzerinde çalışan ve 4K filmleri Rockchip VPU donanımıyla televizyon veya telefonlara sıfır CPU yüküyle aktaran **profesyonel bir ev bulutuna (NAS & Media Server)** dönüştürme adımlarını kapsar.

---

## **1. Mimari ve Donanım Avantajı**

Orange Pi 5'in bu görev için standart bir Raspberry Pi 4/5'e kıyasla ezici avantajları vardır:
* **8K 10-bit VPU Donanım Motoru:** 4K HEVC/H.265 filmleri işlemciyi yormadan doğrudan donanımda dönüştürür (Hardware Transcoding).
* **M.2 NVMe PCIe Hattı:** USB üzerinden bağlı harici disklerin aksine 400 MB/s+ kesintisiz veri yolu sunar; aynı anda 10 cihaz veri yazıp okurken darboğaz yaşanmaz.
* **CasaOS Ekosistemi:** Hantal Linux komutları yerine; telefon veya tarayıcıdan tek tıkla uygulama kurabileceğiniz modern, görsel ve şık bir yönetim paneli sağlar.

```
[ İnternet / Ev Ağı ] 
       │
       ▼
[ Orange Pi 5 (RK3588S) ]
 ├── CasaOS Web Yönetim Paneli (Port 80)
 ├── Nextcloud: Telefon fotoğraflarını arka planda otomatik yedekleme (Google Photos alternatifi)
 ├── Jellyfin: 4K HDR filmleri VPU ile çözüp TV/tablete yayınlama (Netflix alternatifi)
 └── Samba (SMB): Windows/Mac dosya gezgininde yerel ağ sürücüsü olarak görme
```

---

## **2. Adım 1: M.2 NVMe Depolama Alanını Yapılandırma**

> [!TIP]
> **NVMe Boot ile Başlatanlar İçin:** Eğer sisteminizi [Rehber 01](../../guides/Turkish/01-Kurtarma-ve-NVMe-Kurulum.md) adımlarını uygulayarak doğrudan NVMe SSD üzerine kurduysanız, kök dizininiz (`/`) zaten ultra hızlı NVMe üzerindedir. `/etc/fstab` düzenlemesine gerek yoktur; sadece `sudo mkdir -p /DATA/AppData /DATA/Media /DATA/Documents` komutunu çalıştırıp doğrudan Adım 2'ye geçin.

İşletim sistemini MicroSD karttan çalıştırıp NVMe SSD'yi **ikinci bir harici veri depolama diski** olarak bağlayacak olanlar için:

```bash
# 1. NVMe veri diskinin UUID numarasını öğrenin:
sudo blkid
# Örnek çıktı: /dev/nvme0n1p1: UUID="a1b2c3d4-xxxx" TYPE="ext4"

# 2. Kalıcı bağlama noktası oluşturun:
sudo mkdir -p /DATA/AppData /DATA/Media /DATA/Documents

# 3. /etc/fstab dosyasına ekleyin:
echo "UUID=a1b2c3d4-xxxx /DATA ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab

# 4. Bağlantıyı test edin:
sudo mount -a
```

---

## **3. Adım 2: CasaOS Kurulumu (Modern Web Paneli)**

CasaOS, Docker tabanlı çalışan ve tüm servisleri tek bir merkezden yöneten son derece hafif ve modern bir ev bulutu işletim katmanıdır:

```bash
curl -fsSL https://get.casaos.io | sudo bash
```

*Kurulum 2-3 dakika içinde tamamlanır. Bilgisayarınızın veya telefonunuzun tarayıcısından `http://ORANGE_PI_IP` adresine girdiğinizde CasaOS karşılama ekranı açılacaktır.*

1. Bir yönetici kullanıcı adı ve şifresi belirleyin.
2. Ana ekranda işlemci sıcaklığı, RAM kullanımı ve bağlı NVMe diskinizin doluluk oranını canlı olarak göreceksiniz.

---

## **4. Adım 3: Nextcloud ile Otomatik Telefon Yedekleme**

CasaOS ana panelinde **App Store (Uygulama Mağazası)** simgesine tıklayın ve **Nextcloud** uygulamasını seçin.

### **Nextcloud Ayarları:**
1. **Kurulum:** Mağazadan tek tıkla "Install" butonuna basın.
2. **Depolama Yolu:** Veri dizini olarak NVMe diskinizi (`/DATA/Documents`) seçin.
3. **Mobil Uygulama Entegrasyonu:**
   * Android veya iPhone telefonunuza **Nextcloud** uygulamasını indirin.
   * Sunucu adresi olarak `http://ORANGE_PI_IP:8080` yazın ve giriş yapın.
   * **Ayarlar -> Otomatik Yükleme (Auto Upload)** seçeneğini açın.
   * *Artık telefonunuzla çektiğiniz her fotoğraf ve video, eve gelip Wi-Fi'ye bağlandığınız an Orange Pi 5'in M.2 SSD'sine yedeklenir.*

---

## **5. Adım 4: Jellyfin ve Rockchip VPU Donanımsal Transcode (4K Yayın)**

Jellyfin, kişisel film ve dizi arşivinizi Netflix benzeri bir arayüzle organize eder. Buradaki en kritik nokta; **RK3588S'in dahili VPU video hızlandırıcısını Jellyfin konteynerine tanıtmaktır.**

### **1. Gerekli Donanım İzinlerini Ayarlayın:**
```bash
# 1. VPU ve grafik düğümlerine erişim izinlerini verin:
sudo chmod 666 /dev/mpp_service /dev/rga /dev/dri/*

# 2. KRİTİK ADIM: Yeniden başlatmalarda izinlerin sıfırlanmaması için kalıcı udev kuralı tanımlayın:
sudo tee /etc/udev/rules.d/99-rockchip-permissions.rules <<EOF
KERNEL=="mpp_service", MODE="0666"
KERNEL=="rga", MODE="0666"
KERNEL=="renderD*", MODE="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### **2. Docker Compose ile Donanım Hızlandırmalı Jellyfin Kurulumu:**
CasaOS ana ekranında `Custom Install` seçeneğini açın veya terminalden şu `docker-compose.yml` dosyasını çalıştırın:

```yaml
version: "3.8"
services:
  jellyfin:
    image: nyanmisaka/jellyfin:latest  # Rockchip MPP optimizasyonlu özel sürüm
    container_name: jellyfin
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /DATA/AppData/Jellyfin/config:/config
      - /DATA/AppData/Jellyfin/cache:/cache
      - /DATA/Media:/media
    devices:
      - /dev/dri:/dev/dri                      # GPU Hızlandırma
      - /dev/mpp_service:/dev/mpp_service      # Rockchip VPU Donanımsal Kod Çözücü
      - /dev/rga:/dev/rga                      # 2D Grafik Hızlandırıcı
    restart: unless-stopped
```

Başlatın:
```bash
docker compose up -d
```

### **3. Jellyfin Panelinde VPU'yu Aktifleştirme:**
1. Tarayıcınızdan `http://ORANGE_PI_IP:8096` adresine gidin.
2. Yönetici paneline girip **Dashboard (Yönetim Paneli) -> Playback (Oynatma) -> Transcoding** menüsüne gidin.
3. **Hardware Acceleration:** `Rockchip MPP (RKMPP)` veya `VAAPI` seçeneğini işaretleyin.
4. Donanımsal kod çözme listesinde **H.264, HEVC (H.265), VP9, AV1** seçeneklerinin tamamını tikleyin.

---

## **6. Adım 5: Windows / Mac İçin Yerel Ağ Paylaşımı (Samba / SMB)**

Orange Pi 5 üzerindeki arşivinize Windows "Bu Bilgisayar" ekranından bir hard disk gibi erişmek için:

```bash
# 1. Samba servisini kurun:
sudo apt install -y samba

# 2. Yapılandırma dosyasına (/etc/samba/smb.conf) en alta ekleyin:
sudo tee -a /etc/samba/smb.conf <<EOF

[OrangePi_Depo]
   path = /DATA
   browseable = yes
   writable = yes
   guest ok = no
   create mask = 0775
   directory mask = 0775
EOF

# 3. Samba kullanıcısı ve şifresi oluşturun:
sudo smbpasswd -a $USER

# 4. Servisi yeniden başlatın:
sudo systemctl restart smbd
```

* **Windows'tan Bağlanma:** Dosya Gezgini'ni açıp üst adres çubuğuna `\\ORANGE_PI_IP\OrangePi_Depo` yazın.
* **Mac'ten Bağlanma:** Finder'da `Cmd + K` yapıp `smb://ORANGE_PI_IP/OrangePi_Depo` yazın.

---

## **7. Performans ve Güç Tüketimi Kıyaslaması**

| Senaryo | Donanımsız Standart SBC (Pi 4/5) | Orange Pi 5 (RK3588S VPU) |
| :--- | :--- | :--- |
| **4K HEVC -> 1080p Transcoding** | Oynatamaz (Slayt gösterisi, CPU %100) | **Akıcı 60 FPS (CPU <%15, VPU Aktif)** |
| **Aynı Anda İndirme + Fotoğraf Yedekleme** | USB darboğazı nedeniyle yavaşlama | **M.2 NVMe ile 400 MB/s tam hız** |
| **7/24 Açık Kalma Güç Tüketimi** | ~8 – 12 Watt | **~3.5 – 6.5 Watt (Ayda ~15-20 TL elektrik)** |

> [!TIP]
> Bu sistem sayesinde Google One ve Netflix aboneliklerine her ay yüzlerce lira ödemek yerine, evinizde tamamen sizin kontrolünüzde olan, elektrik faturasını neredeyse hiç etkilemeyen üst düzey bir dijital ekosisteme sahip olursunuz.

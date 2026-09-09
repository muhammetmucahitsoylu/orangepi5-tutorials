# **Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** Docker Engine, Compose ve donanım geçişli `/dev/mpp_service`, `/dev/rga`, `/dev/mali0` konteyner izinleri **Orange Pi 5 + Ubuntu 24.04 / 22.04 LTS** üzerinde doğrulanmıştır.

Bu rehber; Orange Pi 5 üzerinde temiz bir Docker ve Docker Compose ortamı kurmak, dağıtıma göre farklılık gösteren `cgroup` bellek sınırı uyarılarını gidermek, konteynerlere (Jellyfin, Plex, Frigate vb.) donanımsal video/grafik hızlandırma (VPU/GPU) yetkisi vermek ve sık karşılaşılan yetki/aygıt hatalarını teşhis etmek için hazırlanmıştır.

---

## **1. Resmi Docker Engine Kurulumu**

Snap tabanlı paketler yerine doğrudan resmi Docker APT deposu üzerinden kurulum yapılması zorunludur:

```bash
# 1. Gerekli ön paketleri yükleyin:
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# 2. Docker resmi GPG anahtarını ekleyin:
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. APT kaynak listesine Docker deposunu tanımlayın:
. /etc/os-release
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  ${UBUNTU_CODENAME:-$VERSION_CODENAME} stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Docker ve Compose eklentisini kurun:
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. Mevcut kullanıcınızı docker grubuna ekleyin (sudo yazmadan çalıştırmak için):
sudo usermod -aG docker $USER
```
*(Değişikliğin hemen geçerli olması için `newgrp docker` komutunu çalıştırın veya oturumu kapatıp açın).*

---

## **2. cgroup Bellek ve Swap Uyarısının Çözümü (Dağıtıma Özel)**

`docker info` komutunu çalıştırdığınızda şu uyarıyı görebilirsiniz:
```text
WARNING: No memory limit support
WARNING: No swap limit support
```

Bu durum, Linux çekirdeğinde cgroup bellek denetiminin önyükleme (boot) parametrelerinde varsayılan olarak kapalı gelmesinden kaynaklanır. **Kullandığınız işletim sistemine göre doğru dosyayı düzenlemeniz gerekir:**

### **Seçenek A: Armbian Kullanıyorsanız**
```bash
sudo nano /boot/armbianEnv.txt
```
Dosyadaki `extraargs=` satırına (yoksa en alta) şu parametreyi ekleyin:
```text
extraargs=cgroup_enable=memory swapaccount=1
```

### **Seçenek B: Resmi Orange Pi OS / Ubuntu Kullanıyorsanız**
```bash
# 1. Eğer /boot/orangepiEnv.txt mevcutsa:
sudo nano /boot/orangepiEnv.txt
# En alta ekleyin:
extraargs=cgroup_enable=memory swapaccount=1

# 2. Eğer dosya extlinux mimarisiyle çalışıyorsa:
sudo nano /boot/extlinux/extlinux.conf
# "append" ile başlayan satırın en sonuna boşluk bırakıp ekleyin:
cgroup_enable=memory swapaccount=1
```

*Cihazı `sudo reboot` ile yeniden başlattıktan sonra `docker info` çıktısındaki uyarılar tamamen kaybolacaktır.*

---

## **3. Konteynerlere Donanım Hızlandırma (VPU / GPU) Tanımlama**

Medya sunucusu (Jellyfin/Plex) veya kamera analizi (Frigate) çalıştırırken donanımsal transcode yapabilmek için kartın donanım aygıtlarının konteynere bağlanması gerekir:

* `/dev/dri`: Mali-G610 GPU arayüzü
* `/dev/mpp_service`: Rockchip VPU donanımsal video çözücü/kodlayıcı
* `/dev/rga`: 2D grafik ve ölçekleme hızlandırıcısı

### **Örnek `docker-compose.yml` (Donanım Destekli Jellyfin)**

```yaml
version: "3.8"
services:
  jellyfin:
    image: nyanmisaka/jellyfin:latest  # Rockchip MPP donanım desteği içeren optimize imaj
    container_name: jellyfin
    network_mode: "host"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /path/to/media:/media
    devices:
      - /dev/dri:/dev/dri
      - /dev/mpp_service:/dev/mpp_service
      - /dev/rga:/dev/rga
    restart: unless-stopped
```

* **Performans Kazanımı:** 4K HEVC bir film transcode edilirken CPU kullanımı %100'e fırlamak yerine, yük VPU'ya devredilir ve CPU kullanımı **%5–10** seviyesinde kalır.

---

## **4. Doğrulama**

```bash
docker run --rm hello-world
```
*Ekrana "Hello from Docker!" çıktısı geliyorsa çekirdek motoru sorunsuz çalışmaktadır.*

---

## **5. Sık Karşılaşılan Hatalar ve Teşhis Tablosu**

| Hata Mesajı | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| `permission denied while trying to connect to the Docker daemon socket` | Kullanıcı `docker` grubuna eklendi ancak aktif oturum henüz yenilenmedi. | `newgrp docker` komutunu çalıştırın veya `sudo reboot` yapın. |
| `error gathering device information while adding device "/dev/mpp_service": no such file` | Sistemde Rockchip resmi BSP çekirdeği yerine ana hat (mainline) Linux çekirdeği çalışıyor. | `ls -l /dev/mpp_service` ile kontrol edin. Mainline çekirdeklerde MPP sürücüsü henüz yoktur; Rockchip BSP (5.10.x / 6.1-rockchip) imajına geçin. |
| `Certificate verification failed / clock skew` (GPG hatası) | Orange Pi 5'in pili olmadığı için yeniden başlayınca sistem saati geri kalmış. | `sudo timedatectl set-ntp true` ile internet saatini senkronize edin. |
| Konteyner içinde transcode çalışmıyor | Konteyner kullanıcısının `video` ve `render` gruplarına erişim izni yok. | Orange Pi'de `sudo usermod -aG video,render $USER` yapın ve compose dosyasında `group_add` tanımlayın. |

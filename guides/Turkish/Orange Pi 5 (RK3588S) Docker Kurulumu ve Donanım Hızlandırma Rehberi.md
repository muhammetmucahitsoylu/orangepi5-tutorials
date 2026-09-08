# **Orange Pi 5 (RK3588S) Docker Kurulumu ve Donanım Hızlandırma Rehberi**

Bu rehber; Orange Pi 5 üzerinde temiz bir Docker ve Docker Compose ortamı kurmak, bellek sınırı uyarılarını gidermek ve konteynerlere (Jellyfin, Plex, Frigate vb.) donanımsal video/grafik hızlandırma (VPU/GPU) yetkisi vermek için hazırlanmıştır.

---

## **1. Resmi Docker Engine Kurulumu**

Snap tabanlı yavaş paketler yerine doğrudan resmi Docker APT deposu üzerinden kurulum yapılması önerilir:

```bash
# 1. Gerekli ön paketleri yükleyin:
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# 2. Docker resmi GPG anahtarını ekleyin:
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. APT kaynak listesine Docker deposunu tanımlayın:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Docker ve Compose eklentisini kurun:
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 5. Mevcut kullanıcınızı docker grubuna ekleyin (sudo yazmadan çalıştırmak için):
sudo usermod -aG docker $USER
```
*(Değişikliğin geçerli olması için oturumu kapatıp tekrar açın veya `newgrp docker` komutunu çalıştırın).*

---

## **2. cgroup Bellek ve Swap Uyarısının Çözümü**

`docker info` komutunu çalıştırdığınızda şu uyarıyı görebilirsiniz:
`WARNING: No memory limit support / WARNING: No swap limit support`

Bu durum, Linux çekirdeğinde cgroup bellek denetiminin varsayılan olarak kapalı gelmesinden kaynaklanır.

* **Çözüm:** `/boot/armbianEnv.txt` (veya kullandığınız dağıtımın boot dosyasındaki `extraargs` satırına) şu parametreleri ekleyin:
  ```text
  extraargs=cgroup_enable=memory swapaccount=1
  ```
* Cihazı yeniden başlattıktan sonra uyarı tamamen kalkacaktır.

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
    image: nyanmisaka/jellyfin:latest  # Rockchip donanım desteği içeren optimize imaj
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

* **Sonuç:** Bu sayede 4K yüksek bit-rate bir film farklı bir cihaza aktarılırken işlemci (CPU) %100 yük altına girmek yerine video doğrudan VPU tarafından çözülür ve CPU kullanımı **%5–10** seviyesinde kalır.

---

## **4. Doğrulama**

Docker servisinin durumunu kontrol etmek için:

```bash
docker run --rm hello-world
```

Konteyner başarıyla çalışıp ekrana "Hello from Docker!" çıktısı veriyorsa kurulum sorunsuz tamamlanmıştır.

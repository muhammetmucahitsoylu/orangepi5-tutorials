# **Orange Pi 5 (RK3588S) Ekransız (Headless) Sunucu ve Optimizasyon Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** ZRAM sıkıştırma, GUI devre dışı bırakma (500MB+ RAM tasarrufu) ve systemd governor servisi **Orange Pi 5 + Ubuntu 24.04 / 22.04 LTS** üzerinde 7/24 test edilerek onaylanmıştır.

Bu rehber; Orange Pi 5'i monitör, klavye veya fare bağlamadan (ekransız / headless) 7/24 çalışan bir ev sunucusu, Docker ana makinesi veya ağ cihazı olarak yapılandırmak isteyenler için temel ilk kurulum ve optimizasyon adımlarını içerir.

---

## **1. İlk SSH Bağlantısı ve Güvenlik**

Cihazı yerel ağ kablosuyla (Ethernet) modeme bağlayıp başlattıktan sonra yerel ağdaki IP adresini bulun:

```bash
# İlk SSH bağlantısı (Resmi imajlarda varsayılan kullanıcı: root veya orangepi, şifre: orangepi):
ssh root@ORANGE_PI_IP
```

### **Güvenlik İçin Yeni Kullanıcı Oluşturma**
Doğrudan `root` kullanıcısı ile çalışmak yerine `sudo` yetkisine sahip kendi kullanıcınızı oluşturun:

```bash
# 1. Yeni kullanıcı oluşturun:
adduser kullanici_adiniz

# 2. Kullanıcıya sudo (yönetici) yetkisi verin:
usermod -aG sudo kullanici_adiniz
```

---

## **2. Masaüstü Arayüzünü Kapatarak RAM Tasarrufu Sağlama**

Eğer cihazınıza masaüstü içeren bir Ubuntu imajı kurduysanız, monitör bağlamayacağınız için arka planda çalışan grafik motoru boş yere **500 – 700 MB RAM** harcar. Sunucu moduna geçmek için grafik arayüzü kapatabilirsiniz:

```bash
# Grafik arayüzü (GUI) devre dışı bırakıp saf sunucu (CLI) moduna geçin:
sudo systemctl set-default multi-user.target

# İleride tekrar masaüstünü açmak isterseniz:
# sudo systemctl set-default graphical.target
```

---

## **3. ZRAM Yapılandırması: RAM ve Disk Ömrü Koruma**

Kart üzerinde ağır derlemeler yaparken veya birden fazla Docker konteyneri çalıştırırken bellek dolarsa sistem donabilir. SSD'ye sürekli swap (takas alanı) yazıp diski yıpratmak yerine RAM'in bir kısmını sıkıştırılmış takas alanı (**ZRAM**) olarak kullanmak en verimli çözümdür:

```bash
# 1. zram-tools paketini kurun:
sudo apt install -y zram-tools

# 2. Yapılandırma dosyasını açıp RAM'in %50'sini ZRAM olarak tanımlayın:
sudo tee -a /etc/default/zramswap <<EOF
ALGO=zstd
PERCENT=50
PRIORITY=100
EOF

# 3. ZRAM servisini yeniden başlatın:
sudo systemctl restart zramswap

# 4. Doğrulama:
zramctl
```

---

## **4. Saat Senkronizasyonu (NTP / Zaman Doğrulama)**

Orange Pi 5 üzerinde harici bir RTC pili takılı değilse, elektrik kesintisinde kart saati geride kalabilir. Hatalı saat; SSL bağlantılarının, paket güncellemelerinin (`apt`) ve güvenlik sertifikalarının bozulmasına neden olur.

```bash
# 1. systemd zaman senkronizasyonunu aktif edin:
sudo timedatectl set-ntp true

# 2. Türkiye saat dilimini ayarlayın:
sudo timedatectl set-timezone Europe/Istanbul

# 3. Doğrulama:
timedatectl status
```
*(Çıktıda `NTP service: active` ve `System clock synchronized: yes` ibarelerini görmelisiniz).*

---

## **5. Kalıcı Performans Modu (Sistem Servisi)**

Sunucunun gelen ağ isteklerine gecikmesiz yanıt vermesi için işlemci frekansını açılışta otomatik olarak performans moduna sabitleyen küçük bir `systemd` servisi tanımlayabilirsiniz:

```bash
sudo tee /etc/systemd/system/cpu-performance.service <<EOF
[Unit]
Description=Set CPU and DMC to Performance Mode
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor && echo performance | tee /sys/class/devfreq/dmc/governor'

[Install]
WantedBy=multi-user.target
EOF

# Servisi aktifleştirin:
sudo systemctl daemon-reload
sudo systemctl enable --now cpu-performance.service
```

---

## **6. Özet Kontrol Listesi**

* [x] `root` yerine şifreli normal kullanıcı oluşturuldu.
* [x] Gereksiz masaüstü servisleri kapatılarak bellek ferahlatıldı.
* [x] ZRAM ile bellek taşmaları ve disk yıpranması önlendi.
* [x] Saat dilimi ve otomatik NTP eşitlemesi yapıldı.
* [x] Açılışta performans modu otomatikleşti.

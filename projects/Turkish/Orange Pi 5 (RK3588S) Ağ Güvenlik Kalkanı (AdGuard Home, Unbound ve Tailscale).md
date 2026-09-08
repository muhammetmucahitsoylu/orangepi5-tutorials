# **Orange Pi 5 (RK3588S) Ağ Güvenlik Kalkanı (AdGuard Home, Unbound ve Tailscale)**

Bu rehber; Orange Pi 5'inizi tüm ev veya ofis ağı için **reklamları, izleyicileri ve zararlı yazılımları kökünden engelleyen**, internet servis sağlayıcınızın (İSS) DNS kayıtlarını tutmasını imkansız kılan ve dışarıdayken bile evinize güvenle bağlanmanızı sağlayan **kurumsal düzeyde bir ağ güvenlik merkezine** dönüştürme adımlarını anlatır.

---

## **1. Güvenlik ve Gizlilik Mimarisi**

Sistem, evinizdeki hiçbir cihaza (Akıllı TV, iPhone, Android, PC) ekstra uygulama yüklemeden, modem seviyesinde merkezi bir filtreleme uygular:

```
[ Ev Cihazları (Telefon, TV, PC) ]
               │ (DNS Sorgusu: "reklam.com nedir?")
               ▼
[ 1. AdGuard Home (Orange Pi 5: Port 53) ] ──> Reklam ve takipçi listeleriyle eşleşirse ENGELLER (0.1 ms)
               │ (Temiz alan adı sorgusu: "google.com")
               ▼
[ 2. Unbound DNS Resolver (Port 5335) ] ──> Google/Cloudflare'e sormadan doğrudan kök DNS sunucularına sorar
               │
               ▼
[ İnternet Kök Sunucuları (.) ] (Servis sağlayıcınız nereye girdiğinizi asla göremez)

+ [ 3. Tailscale Mesh VPN ] ──> Dışarıdayken hücresel veri trafiğinizi eve tüneller, mobil reklamları engeller.
```

---

## **2. Adım 1: Port 53 Çakışmasını Çözme (`systemd-resolved`)**

Ubuntu üzerinde `systemd-resolved` servisi DNS portu olan 53'ü varsayılan olarak işgal eder. AdGuard'ın çalışabilmesi için bu port serbest bırakılmalıdır:

```bash
# 1. systemd-resolved yapılandırma dosyasını düzenleyin:
sudo sed -r -i.orig 's/#?DNSStubListener=yes/DNSStubListener=no/g' /etc/systemd/resolved.conf

# 2. Sistem DNS çözümleyicisini güncelleyin:
sudo systemctl restart systemd-resolved
```

---

## **3. Adım 2: AdGuard Home Kurulumu**

AdGuard Home, ağ genelinde reklamları engelleyen modern ve Türkçe destekli bir DNS sunucusudur:

```bash
# Resmi kurulum scriptini çalıştırın:
curl -s -S -L https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh | sudo sh -s -- -v
```

### **İlk Yapılandırma:**
1. Bilgisayarınızın tarayıcısından `http://ORANGE_PI_IP:3000` adresine gidin.
2. **Yönetim Arayüzü:** Port `80` veya `8080` olarak seçin.
3. **DNS Sunucusu:** Port `53` olarak seçin ve devam edin.
4. Yönetici kullanıcı adı ve şifrenizi belirleyin.
5. Kurulum bittiğinde yönetim paneli `http://ORANGE_PI_IP` üzerinde aktif hale gelecektir.

---

## **4. Adım 3: Unbound ile %100 Gizli Kök DNS Çözümleyici Kurulumu**

Standart olarak DNS sorgularınız Google (8.8.8.8) veya Cloudflare (1.1.1.1) sunucularına gider ve hangi sitelere girdiğiniz loglanabilir. **Unbound**, üçüncü tarafları aradan çıkarıp doğrudan kök DNS sunucularına (Root Anchors) bağlanır:

```bash
# 1. Unbound servisini kurun:
sudo apt update && sudo apt install -y unbound

# 2. Optimize edilmiş yapılandırma dosyasını oluşturun:
sudo tee /etc/unbound/unbound.conf.d/adguard.conf <<EOF
server:
    verbosity: 1
    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    do-ip6: no

    # Güvenlik ve Gizlilik
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    use-caps-for-id: no

    # Performans ve Önbellek
    edns-buffer-size: 1232
    prefetch: yes
    num-threads: 4
    so-rcvbuf: 4m
    so-sndbuf: 4m
EOF

# 3. Unbound servisini başlatın:
sudo systemctl restart unbound
sudo systemctl enable unbound
```

### **Unbound Testi:**
```bash
dig @127.0.0.1 -p 5335 google.com
```
*`status: NOERROR` ve geçerli bir IP adresi dönüyorsa Unbound yerel olarak çalışmaktadır.*

---

## **5. Adım 4: AdGuard Home'u Unbound'a Bağlama**

1. AdGuard Home arayüzünü açın (`http://ORANGE_PI_IP`).
2. **Ayarlar -> DNS Ayarları (DNS Settings)** menüsüne gidin.
3. **Yukarı Akış DNS Sunucuları (Upstream DNS Servers)** kutusundaki tüm adresleri silin ve şunu yazın:
   ```text
   127.0.0.1:5335
   ```
4. **Uygula (Apply)** butonuna basın.
*Artık tüm DNS sorgularınız yerel Unbound motoru tarafından gizlilikle çözülür.*

---

## **6. Adım 5: Tailscale ile Dışarıdan Güvenli Tünel (Exit Node)**

Evin dışındayken (mobil hücresel veri veya halka açık güvensiz Wi-Fi ağlarında) telefonunuzun trafiğini Orange Pi 5 üzerinden geçirmek ve reklamları engellemeye devam etmek için:

```bash
# 1. Tailscale kurulumu:
curl -fsSL https://tailscale.com/install.sh | sudo sh

# 2. Linux IP yönlendirmesini (IP Forwarding) açın:
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# 3. Orange Pi 5'i Ev Ağı Yönlendiricisi ve Çıkış Düğümü (Exit Node) olarak başlatın:
# (Örnek yerel IP bloğunuz 192.168.1.0/24 ise):
sudo tailscale up --advertise-routes=192.168.1.0/24 --advertise-exit-node
```

* Ekranda çıkan linke tarayıcınızdan tıklayarak cihazı Tailscale hesabınıza bağlayın.
* [Tailscale Admin Konsolu](https://login.tailscale.com/admin/machines) üzerinden Orange Pi 5'in yanındaki **...** simgesine tıklayın, **Edit route settings** diyerek `Exit node` ve yerel ağı onaylayın.
* *Telefonunuza Tailscale uygulamasını kurup "Use exit node" dediğinizde, dünyanın öbür ucunda bile olsanız evinizin internetinden ve reklam engelleyicisinden çıkış yaparsınız.*

---

## **7. Adım 6: Modemi Orange Pi 5'e Yönlendirme**

Tüm evdeki televizyon, tablet ve telefonların otomatik korunması için:
1. Evinizdeki modemin arayüzüne girin (genellikle `192.168.1.1`).
2. **DHCP Sunucusu -> Birincil DNS (Primary DNS)** kutusuna **Orange Pi 5'inizin Sabit IP Adresini** yazın.
3. Ayarları kaydedip modemi yeniden başlatın.

---

## **8. Özet ve Kazanımlar**

* **Akıllı TV Reklamları:** YouTube veya dizi sitelerindeki sinir bozucu reklam ve veri toplama trafiği daha televizyona ulaşmadan engellenir.
* **Sıfır Batarya Kaybı:** Telefonlarda arka planda çalışan VPN uygulamalarına gerek kalmaz; filtreleme doğrudan donanım seviyesinde gerçekleşir.
* **Gizlilik:** Ziyaret ettiğiniz siteler hiçbir telekomünikasyon şirketinin veya aracı firmanın loglarında yer almaz.

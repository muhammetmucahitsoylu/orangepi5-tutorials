# **Orange Pi 5 (RK3588S) Uzaktan Erişim ve Masaüstü Bağlantı Rehberi**

Bu rehber; Orange Pi 5'e harici bir monitör veya klavye bağlamadan, dizüstü veya masaüstü bilgisayarınız üzerinden hem komut satırı (CMD / Terminal) hem de grafik masaüstü ekranı ile uzaktan bağlanma yöntemlerini içerir.

---

## **BÖLÜM 1: Komut Satırı (Terminal / CMD) ile Bağlantı**

### **1. Yöntem: Standart SSH Bağlantısı (Ağ Üzerinden)**

Orange Pi 5 ve bilgisayarınız aynı yerel ağa (Wi-Fi veya Ethernet) bağlı olduğunda ek bir yazılıma gerek kalmadan doğrudan bağlanabilirsiniz.

* **Windows (CMD veya PowerShell), macOS veya Linux Terminalinde:**
  ```bash
  ssh kullanici_adiniz@ORANGE_PI_IP
  ```
  *(Varsayılan kullanıcı genellikle `orangepi` veya `root`, şifre: `orangepi`)*

### **2. Yöntem: Şifresiz SSH Girişi (SSH Key)**
Her seferinde şifre yazmamak ve güvenliği artırmak için bilgisayarınızdaki açık anahtarı Orange Pi 5'e kopyalayabilirsiniz:

* **Windows PowerShell üzerinden tek komutla aktarım:**
  ```powershell
  # Bilgisayarınızda anahtar yoksa oluşturun:
  ssh-keygen -t ed25519

  # Anahtarı Orange Pi'ye yükleyin:
  type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh kullanici_adiniz@ORANGE_PI_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
  ```

### **3. Yöntem: UART Seri Konsol (Ağ ve Ekran Olmadan Doğrudan Kablo ile)**
Ağ bağlantısı çöktüğünde, IP bilinmediğinde veya sistem bootloader aşamasında takıldığında en güvenilir donanımsal erişim yöntemidir.

* **Gereksinim:** USB-TTL dönüştürücü kablo (3.3V mantık seviyesinde çalışan CP2102 veya CH340).
* **Bağlantı Seçenekleri (V1.3.2 Donanım Şeması):**
  * **Önerilen: Özel 3-Pin Hata Ayıklama (Debug UART) Başlığı:**  
    26 pinlik başlığın hemen alt tarafında yer alan bağımsız 3 pinli gruptur (kare lehim pedi GND'dir):
    * USB-TTL **GND** -> Orange Pi 5 **GND** (Alttaki kare ped)
    * USB-TTL **RX** -> Orange Pi 5 **TX** (En üst pin)
    * USB-TTL **TX** -> Orange Pi 5 **RX** (Orta pin)
  * **Alternatif: 26-Pin Başlık Üzerinden (UART0):**
    * USB-TTL **GND** -> Pin 6 (GND)
    * USB-TTL **RX** -> Pin 8 (`GPIO4_A3` / `UART0_TX_M2`)
    * USB-TTL **TX** -> Pin 10 (`GPIO4_A4` / `UART0_RX_M2`)
* **Kritik Kural:** Rockchip RK3588 serisinin seri hata ayıklama konsolu baud hızı standart 115200 değil, **1.500.000 (1.5M)** baud'dur. PuTTY, minicom veya terminal programında hız mutlaka `1500000` olarak seçilmelidir. Detaylı pin şeması için [docs/GPIO_PINOUT.md](../../docs/GPIO_PINOUT.md) belgesini inceleyin.

---

## **BÖLÜM 2: Grafik Arayüze (Masaüstü Ekranına) Erişim**

### **1. Yöntem: Windows Uzak Masaüstü (RDP / xrdp) — En Pratik Çözüm**

Bilgisayarınıza hiçbir ek program yüklemeden doğrudan Windows'un dahili "Uzak Masaüstü Bağlantısı" aracını kullanabilirsiniz.

1. **Orange Pi 5 üzerinde xrdp servisini kurun:**
   ```bash
   sudo apt update && sudo apt install -y xrdp
   sudo systemctl enable --now xrdp
   ```
2. **Kullanıcı oturum izinlerini ayarlayın:**
   ```bash
   sudo adduser xrdp ssl-cert
   ```
3. **Bağlantı:**  
   Windows'ta `Win + R` tuşlarına basıp `mstsc` yazın. Açılan pencereye Orange Pi 5'in IP adresini girip **Bağlan** butonuna tıklayın. Kullanıcı adı ve şifrenizi girdiğinizde doğrudan masaüstü ekranı açılacaktır.

---

### **2. Yöntem: VNC Sunucusu (TigerVNC) — Hafif ve Esnek**

Düşük ağ hızlarında veya Linux/macOS laptoplardan bağlanırken tercih edilir.

1. **TigerVNC sunucusunu kurun:**
   ```bash
   sudo apt install -y tigervnc-standalone-server tigervnc-common
   ```
2. **VNC şifresi belirleyin:**
   ```bash
   vncpasswd
   ```
3. **VNC oturumunu başlatın:**
   ```bash
   vncserver :1 -geometry 1920x1080 -depth 24
   ```
4. **Bağlantı:** Laptopunuza **RealVNC Viewer** kurun ve adres kısmına `ORANGE_PI_IP:5901` yazarak bağlanın.

---

### **3. Yöntem: RustDesk / NoMachine — Yüksek FPS ve Düşük Gecikme**

YouTube videosu izlemek, ses aktarımı yapmak veya akıcı 60 FPS masaüstü deneyimi elde etmek için en gelişmiş çözümdür.

* **NoMachine (Önerilen):** NoMachine ARM64 `.deb` paketini Orange Pi 5'e, Windows sürümünü de laptopunuza kurun. Ağdaki Orange Pi'yi otomatik olarak bulur; donanımsal ekran kodlama ve ses iletimini sıfır ayarla sağlar.

---

### **4. Yöntem: SSH X11 Forwarding (Yalnızca Tek Bir Uygulama Açma)**

Tüm masaüstünü aktarmak yerine sadece tek bir grafik uygulamasını (örneğin bir kamera penceresini veya metin editörünü) doğrudan bilgisayarınızın ekranına yansıtmak için:

* **Bağlantı Komutu:**
  ```bash
  ssh -X kullanici_adiniz@ORANGE_PI_IP
  ```
* Terminal açıldıktan sonra örneğin `gedit` veya `galculator` yazdığınızda pencere doğrudan laptopunuzun ekranında bağımsız bir uygulama gibi açılır *(Windows için Xming veya VcXsrv kurulu olmalıdır)*.

---

## **3. Yöntem Karşılaştırma Tablosu**

| Yöntem | Tür | Gerekli Ek Yazılım | En Uygun Senaryo |
| :--- | :--- | :--- | :--- |
| **SSH (CMD/PowerShell)** | Terminal | Yok (Dahili) | Sunucu yönetimi, komut çalıştırma, paket kurulumu |
| **UART Seri Konsol** | Donanım Terminali | USB-TTL Kablo + PuTTY | Ağ çöktüğünde veya sistem açılmadığında kurtarma |
| **Windows RDP (xrdp)** | Masaüstü (GUI) | Yok (Windows Dahili) | Hızlı ve kurulumsuz uzaktan masaüstü ihtiyacı |
| **NoMachine** | Masaüstü (GUI) | NoMachine İstemcisi | Yüksek FPS, düşük gecikme ve ses aktarımı |
| **SSH X11 (-X)** | Tekil Pencere | X-Server (VcXsrv) | Sadece tek bir arayüzlü aracı çalıştırma |

# **Orange Pi 5 (RK3588S) Yazılımcılar İçin IDE ve Geliştirme Ortamı Kurulumu**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar ve kodlar **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)** üzerinde bizzat fiziksel donanımda test edilmiş ve onaylanmıştır.

Bu rehber; Orange Pi 5 üzerinde C/C++, Python veya yapay zeka projeleri geliştirmek isteyen yazılımcıların sıfırdan profesyonel bir çalışma ortamı kurabilmesi için hazırlanmıştır.

---

## **1. Geliştirme Felsefesi: Kodu Nerede Yazmalıyız?**

Tek kart bilgisayarlarda (SBC) kod geliştirirken iki yaygın yaklaşım vardır:

* **Yanlış/Yorucu Yaklaşım:** Orange Pi 5'e monitör bağlayıp kartın kendi masaüstünde ağır bir IDE (örneğin doğrudan VS Code veya PyCharm) çalıştırmak. Bu yöntem kartın RAM ve CPU kaynaklarını kod derleme ve test yerine arayüz işlemlerine harcar.
* **Profesyonel Yaklaşım (Önerilen):** Kendi dizüstü/masaüstü bilgisayarınızdaki VS Code üzerinden **Remote - SSH** eklentisiyle Orange Pi 5'e bağlanmaktır. Kodları laptopunuzun rahatlığında yazarsınız; ancak dosyalar, derleyici, Python ortamı ve terminal doğrudan Orange Pi 5 donanımı üzerinde çalışır.

---

## **2. Yöntem 1: VS Code Remote - SSH Kurulumu (Endüstri Standardı)**

### **Adım 1: Laptopunuzda Hazırlık**
1. Bilgisayarınızda **Visual Studio Code** uygulamasını açın.
2. Sol menüdeki **Extensions (Eklentiler)** simgesine tıklayın (veya `Ctrl + Shift + X`).
3. Arama kutusuna **Remote - SSH** yazın ve Microsoft tarafından yayımlanan eklentiyi kurun.

### **Adım 2: Karta Bağlanma**
1. `F1` tuşuna basıp (veya `Ctrl + Shift + P`) arama satırına `Remote-SSH: Connect to Host...` yazın.
2. Bağlantı dizesini girin:
   ```text
   kullanici_adiniz@ORANGE_PI_IP
   ```
3. Şifrenizi girdikten sonra sol alt köşede yeşil kutuda `SSH: ORANGE_PI_IP` ibaresini göreceksiniz.
4. **File -> Open Folder** diyerek Orange Pi 5 üzerindeki proje klasörünüzü (örneğin `/home/kullanici_adiniz/projects`) açın.

*Artık laptopunuzun ekranında kod yazarken, VS Code terminalinden çalıştırdığınız her komut doğrudan Orange Pi 5 üzerinde koşacaktır.*

---

## **3. Yöntem 2: Code-Server (Tarayıcıdan Çalışan VS Code)**

Eğer farklı cihazlardan (tablet, iş bilgisayarı vb.) sadece web tarayıcısı üzerinden Orange Pi 5 üzerinde kod yazmak isterseniz **Code-Server** kurabilirsiniz:

```bash
# 1. Code-Server kurulum scriptini çalıştırın:
curl -fsSL https://code-server.dev/install.sh | sh

# 2. Servisi sistem başlangıcına ekleyin ve başlatın:
sudo systemctl enable --now code-server@$USER

# 3. Giriş şifresini öğrenin:
cat ~/.config/code-server/config.yaml | grep password
```

*Tarayıcınızın adres çubuğuna `http://ORANGE_PI_IP:8080` yazıp şifrenizi girdiğinizde tam teşekküllü VS Code arayüzü tarayıcınızda açılacaktır.*

---

## **4. Adım 3: Temel Yazılım ve Derleme Araçlarının Kurulumu**

C/C++, Python ve donanım kütüphanelerini derleyebilmek için temel geliştirici paketlerini kurun:

```bash
sudo apt update && sudo apt install -y \
  build-essential \
  cmake \
  git \
  ninja-build \
  pkg-config \
  python3-dev \
  python3-pip \
  python3-venv \
  libopencv-dev
```

---

## **5. Adım 4: İlk Proje Dizin Mimarisi ve Python Virtual Environment (venv)**

Linux sistem paketlerini bozmamak ve temiz bir çalışma alanı sağlamak için her proje için izole bir Python sanal ortamı (`venv`) oluşturulmalıdır.

```bash
# 1. Projeler ana dizinini ve ilk projenizi oluşturun:
mkdir -p ~/projects/ilk-projem && cd ~/projects/ilk-projem

# 2. Standart proje klasör yapısını oluşturun:
mkdir -p src models data

# 3. Python sanal ortamını oluşturun:
python3 -m venv venv

# 4. Sanal ortamı aktifleştirin:
source venv/bin/activate
```

### **Örnek Standart Proje Ağacı**
```text
ilk-projem/
├── venv/                 # İzole Python ortamı
├── src/                  # Kaynak kodlar (.py, .cpp)
│   └── main.py
├── models/               # Model dosyaları (.onnx, .rknn)
├── data/                 # Test verileri, görseller
├── requirements.txt      # Gerekli kütüphaneler
└── README.md             # Proje dokümantasyonu
```

---

## **6. Hızlı Doğrulama: Donanım Kontrol Scripti**

Projenizin çalışabilirliğini doğrulamak için `src/main.py` dosyasını oluşturun:

```python
import platform
import os

print(f"--- Orange Pi 5 Donanım Doğrulaması ---")
print(f"İşlemci Mimarisi: {platform.machine()}")
print(f"Çekirdek Sayısı: {os.cpu_count()}")

# NPU durumu kontrolü
npu_freq_path = "/sys/class/devfreq/fdab0000.npu/cur_freq"
if os.path.exists(npu_freq_path):
    with open(npu_freq_path, "r") as f:
        freq = int(f.read().strip()) / 1_000_000
    print(f"NPU Çekirdeği: Aktif ({freq:.0f} MHz)")
else:
    print("NPU Çekirdeği: Algılanamadı (BSP Kernel kurulu olduğundan emin olun)")
```

Çalıştırma:
```bash
python3 src/main.py
```

*Tebrikler! Geliştirme ortamınız hazır. Artık C++ ve Python ile kartın tüm işlemci, bellek ve NPU yeteneklerini kullanacak projeler geliştirmeye başlayabilirsiniz.*

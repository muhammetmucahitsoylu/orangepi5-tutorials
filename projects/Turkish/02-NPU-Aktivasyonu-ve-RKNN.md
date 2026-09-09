# **Orange Pi 5 (RK3588S) NPU Aktivasyonu ve RKNN Çalışma Ortamı Kurulumu**

Bu rehber; Rockchip RK3588S işlemcisinde yer alan 3 çekirdekli ve **6 TOPS** işlem gücüne sahip Nöral İşlem Birimi'ni (NPU) uyandırmak, çekirdek sürücü uyumluluğunu doğrulamak ve Python ile yapay zeka modellerini çalıştırmak için gerekli çalışma ortamını kurmayı anlatır.

---

## **1. RK3588 NPU Çalışma Mantığı: Neden Standart PyTorch Çalışmaz?**

* **Genel Yanılgı:** Tek kart bilgisayara `pip install torch` yapıldığında yapay zeka modellerinin NPU üzerinde çalışacağı sanılır. Ancak standart PyTorch yalnızca CPU veya Nvidia CUDA GPU destekler; RK3588'in özel NPU donanımını tanımaz.
* **Rockchip İş Akışı:**
  1. Model (YOLO, ResNet, MobileNet vb.) bilgisayarınızda eğitilir veya `.onnx` formatında dışa aktarılır.
  2. Model, Rockchip'in derleyicisi ile NPU'nun anlayacağı **`.rknn`** formatına dönüştürülür (quantization).
  3. Orange Pi 5 üzerinde **RKNN-Toolkit-Lite2** çalışma motoru (runtime) kullanılarak model doğrudan 6 TOPS gücündeki NPU çekirdeklerine yüklenir ve milisaniyeler içinde çıkarım (inference) yapılır.

---

## **2. Adım 1: NPU Çekirdek Sürücüsünü Doğrulama**

NPU sürücüsünün çekirdekte aktif olup olmadığını kontrol edin:

```bash
# 1. NPU sürücü versiyonunu kontrol edin:
dmesg | grep -i rknpu
```
*Beklenen çıktı:* `RKNPU: Driver version: 0.9.x` veya üzeri.

> [!IMPORTANT]
> **KRİTİK VERSİYON SABİTLEME & UYUMLULUK KURALI:**  
> Rockchip ekosisteminde model derleyicisi (`rknn-toolkit2`), kart çalışma motoru (`librknnrt.so`) ve çekirdek sürücüsü (`rknpu.ko`) **aynı sürüm ailesine** kilitli olmak zorundadır:
> * **Bu Repodaki Doğrulanmış Referans:** RKNPU Sürücüsü: **`v0.9.8`**, Runtime & Toolkit: **`v2.3.2`**.
> * Sürücü versiyonunu doğrudan kontrol edin: `cat /sys/kernel/debug/rknpu/version`
> * Detaylı uyumluluk matrisi ve sürüm çatışmalarını çözmek için [docs/COMPATIBILITY.md](../../docs/COMPATIBILITY.md) kılavuzunu inceleyin.

```bash
# 2. NPU frekans yöneticisini kontrol edin:
cat /sys/class/devfreq/*npu*/cur_freq
```
*Beklenen çıktı:* `1000000000` (NPU'nun 1.0 GHz tepe saat hızında olduğunu doğrular).

---

## **3. Adım 2: Sistem C Runtime Kütüphanesini (`librknnrt.so`) Yükleme**

Python veya C++ uygulamalarının NPU ile iletişim kurabilmesi için resmi donanım çalışma kütüphanesinin sistemde bulunması gerekir:

```bash
# Yöntem 1: Doğrudan ve Hızlı İndirme (Önerilen)
sudo curl -sL -o /usr/lib/librknnrt.so https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig

# Yöntem 2: Git Deposu Üzerinden (Alternatif)
cd /tmp
git clone --depth 1 https://github.com/rockchip-linux/rknpu2.git
sudo cp rknpu2/runtime/RK3588/Linux/librknn_api/aarch64/librknnrt.so /usr/lib/
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig
rm -rf /tmp/rknpu2
```

---

## **4. Adım 3: Python İçin RKNN-Toolkit2-Lite Kurulumu**

Python sürümünüze göre doğru paketi kurmanız şarttır. Önce Python sürümünüzü öğrenin:
```bash
python3 --version
```

### **Sanal Ortamı Hazırlayın ve Yükleyin:**
```bash
mkdir -p ~/projects/npu-env && cd ~/projects/npu-env
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install numpy opencv-python pillow
```

### **Sürümünüze Göre Doğru Wheel Paketini Seçin:**
* **Python 3.10 İçin (Ubuntu 22.04 LTS):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```
* **Python 3.11 İçin (Debian Bookworm):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```
* **Python 3.12 İçin (Ubuntu 24.04):**
  ```bash
  pip install https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
  ```

---

## **5. Adım 4: "Hello NPU" — 3 Çekirdeği Birden Uyandırma Testi**

> [!NOTE]
> RKNN-Toolkit-Lite2 mimarisinde `rknn.init_runtime()` donanım oturumunu açabilmek için önceden derlenmiş bir `.rknn` modelinin belleğe alınmasını (`load_rknn`) şart koşar. Aşağıdaki script, resmi örnek modeli otomatik indirip 3 çekirdeği (6 TOPS) devreye sokar.

`test_npu.py` dosyasını oluşturun:

```python
import os
import urllib.request
import subprocess
from rknnlite.api import RKNNLite

MODEL_FILE = "resnet18_for_rk3588.rknn"
MODEL_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/resnet18_for_rk3588.rknn"

# 1. Örnek RKNN modelini temin et
if not os.path.exists(MODEL_FILE):
    print(f"[*] Referans NPU modeli indiriliyor: {MODEL_FILE}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)

print("--- Orange Pi 5 RKNN NPU Test Başlatılıyor ---")
rknn = RKNNLite()

# 2. Modeli yükle
ret = rknn.load_rknn(MODEL_FILE)
if ret != 0:
    print(f"[HATA] Model yüklenemedi! Hata kodu: {ret}")
    exit(ret)

# 3. 3 Çekirdeği birden (Core 0, Core 1, Core 2) tam 6 TOPS olarak devreye sok:
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[BAŞARILI] 3 NPU Çekirdeği de donanımsal olarak uyandırıldı (Core 0, 1, 2)!")
    print("\n--- Sürücü ve API Versiyon Bilgisi ---")
    rknn.get_sdk_version()
    try:
        telemetry = subprocess.check_output("cat /sys/kernel/debug/rknpu/load 2>/dev/null || true", shell=True).decode()
        if telemetry.strip():
            print("\n--- Anlık NPU Çekirdek Telemetrisi ---")
            print(telemetry.strip())
    except Exception:
        pass
else:
    print(f"[HATA] NPU başlatılamadı! Hata kodu: {ret}")

rknn.release()
```

### **Testi Çalıştırın:**
```bash
# Sanal ortam aktifken çalıştırın:
python3 test_npu.py
```

**Beklenen Çıktı:**
```text
--- Orange Pi 5 RKNN NPU Test Başlatılıyor ---
[BAŞARILI] 3 NPU Çekirdeği de donanımsal olarak uyandırıldı (Core 0, 1, 2)!

--- Sürücü ve API Versiyon Bilgisi ---
==============================================
RKNN VERSION:
  API: 2.3.2
  DRV: 0.9.7 (veya 0.9.8)
==============================================
```

---

## **6. Sık Karşılaşılan Hatalar ve Teşhis Tablosu**

| Hata Mesajı / Belirti | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| `rknn_init, RKNN driver version(0.8.2) is not match with runtime version(2.x.x)` | Çekirdekteki RKNPU kernel modülü eski (v0.8), indirilen RKNN-Lite ise yeni (v2.x). | `sudo apt update && sudo apt upgrade` ile kerneli güncelleyin veya Rockchip BSP 5.10.110+ imajı yükleyin. |
| `ImportError: librknnrt.so: cannot open shared object file` | Adım 2'deki C kütüphanesi sisteme kopyalanmadı veya `ldconfig` çalıştırılmadı. | `sudo cp librknnrt.so /usr/lib/` yapıp `sudo ldconfig` komutunu uygulayın. |
| `is not a supported wheel on this platform` | Sistemdeki Python sürümü (örn: 3.12) ile indirilen `.whl` paketi (örn: cp310) uyuşmuyor. | `python3 --version` çıktısına göre Adım 3'teki uygun `cp310`, `cp311` veya `cp312` paketini seçin. |
| `Permission denied: /dev/rknpu` | Normal kullanıcının NPU aygıt düğümüne erişim izni yok. | `sudo chmod 666 /dev/rknpu*` uygulayın veya kullanıcıyı ilgili gruba ekleyin. |

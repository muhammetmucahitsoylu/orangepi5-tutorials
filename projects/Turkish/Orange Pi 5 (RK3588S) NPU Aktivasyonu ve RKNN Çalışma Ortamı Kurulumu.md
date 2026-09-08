# **Orange Pi 5 (RK3588S) NPU Aktivasyonu ve RKNN Çalışma Ortamı Kurulumu**

Bu rehber; Rockchip RK3588S işlemcisinde yer alan 3 çekirdekli ve **6 TOPS** işlem gücüne sahip Nöral İşlem Birimi'ni (NPU) uyandırmak, donanım sürücülerini doğrulamak ve Python ile yapay zeka modellerini çalıştırmak için gerekli çalışma ortamını kurmayı anlatır.

---

## **1. RK3588 NPU Çalışma Mantığı: Neden Standart PyTorch Çalışmaz?**

* **Genel Yanılgı:** Tek kart bilgisayara `pip install torch` yapıldığında yapay zeka modellerinin NPU üzerinde çalışacağı sanılır. Ancak standart PyTorch yalnızca CPU veya Nvidia CUDA GPU destekler; RK3588'in özel NPU donanımını tanımaz.
* **Rockchip İş Akışı:**
  1. Model (YOLO, ResNet, MobileNet vb.) bilgisayarınızda eğitilir veya `.onnx` formatında dışa aktarılır.
  2. Model, Rockchip'in derleyicisi ile NPU'nun anlayacağı **`.rknn`** formatına dönüştürülür (quantization).
  3. Orange Pi 5 üzerinde **RKNN-Toolkit-Lite2** çalışma motoru (runtime) kullanılarak model doğrudan 6 TOPS gücündeki NPU çekirdeklerine yüklenir ve milisaniyeler içinde çıkarım (inference) yapılır.

---

## **2. Adım 1: NPU Çekirdek Sürücüsünü Doğrulama**

Ubuntu 24.04 (Linux 6.1-rockchip) kernelında NPU sürücüsü varsayılan olarak yüklü gelir. Terminalde sürücünün aktif olduğunu doğrulayın:

```bash
# 1. NPU sürücü versiyonunu kontrol edin:
dmesg | grep -i rknpu
```
*Beklenen çıktı:* `RKNPU: Driver version: 0.9.x` veya üzeri.

```bash
# 2. NPU saat hızını kontrol edin:
cat /sys/class/devfreq/fdab0000.npu/cur_freq
```
*Beklenen çıktı:* `1000000000` (NPU'nun 1.0 GHz tepe hızında olduğunu doğrular).

---

## **3. Adım 2: Sistem C Runtime Kütüphanesini (`librknnrt.so`) Yükleme**

Python veya C++ uygulamalarının NPU ile iletişim kurabilmesi için resmi donanım çalışma kütüphanesinin sistemde bulunması gerekir:

```bash
# 1. Resmi Rockchip rknpu2 deposunu klonlayın:
cd /tmp
git clone --depth 1 https://github.com/rockchip-linux/rknpu2.git

# 2. 64-bit ARM kütüphanesini sistem dizinine kopyalayın:
sudo cp rknpu2/runtime/Linux/librknn_api/aarch64/librknnrt.so /usr/lib/

# 3. İzinleri ayarlayın ve kütüphane önbelleğini güncelleyin:
sudo chmod 755 /usr/lib/librknnrt.so
sudo ldconfig

# 4. Geçici klasörü temizleyin:
rm -rf /tmp/rknpu2
```

---

## **4. Adım 3: Python İçin RKNN-Toolkit2-Lite Kurulumu**

Orange Pi 5 gibi uç (edge) cihazlarda model çalıştırmak için hafif sürüm olan `rknn-toolkit-lite2` kullanılır.

1. Proje dizininize gidin ve sanal ortamınızı aktifleştirin:
   ```bash
   cd ~/projects/ilk-projem
   source venv/bin/activate
   ```

2. Temel Python matematik ve görsel kütüphanelerini kurun:
   ```bash
   pip install --upgrade pip
   pip install numpy opencv-python pillow
   ```

3. Python sürümünüze uygun (Python 3.10 veya 3.11) resmi RKNN-Lite paketini kurun:
   ```bash
   # Python 3.10 için (Ubuntu 22.04):
   pip install https://github.com/airockchip/rknn-toolkit2/releases/download/v2.3.0/rknn_toolkit_lite2-2.3.0-cp310-cp310-linux_aarch64.whl

   # VEYA Python 3.11/3.12 için doğrudan PyPI deposundan:
   pip install rknn-toolkit-lite2
   ```

---

## **5. Adım 4: "Hello NPU" — 3 Çekirdeği Birden Uyandırma Testi**

Kurulumun doğruluğunu test etmek ve NPU çekirdeklerinin çalıştığını görmek için bir test scripti hazırlayın:

`src/test_npu.py` dosyasını oluşturun:

```python
from rknnlite.api import RKNNLite
import subprocess

print("--- Orange Pi 5 RKNN NPU Başlatılıyor ---")

# RKNN-Lite motorunu başlat
rknn = RKNNLite()

# NPU'yu 3 çekirdeği birden (Core 0, Core 1, Core 2) kullanacak şekilde yapılandır
# RK3588'de RKNNLite.NPU_CORE_0_1_2 seçeneği tam 6 TOPS gücü açar
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[BAŞARILI] 3 NPU Çekirdeği de donanımsal olarak uyandırıldı!")
    
    # Canlı çekirdek telemetrisini oku
    try:
        telemetry = subprocess.check_output("sudo cat /sys/kernel/debug/rknpu/load", shell=True).decode()
        print("\n--- Anlık NPU Çekirdek Durumu ---")
        print(telemetry.strip())
    except Exception as e:
        print("Telemetri okunamadı (root izni gerekebilir).")
else:
    print(f"[HATA] NPU başlatılamadı! Hata kodu: {ret}")

rknn.release()
```

### **Testi Çalıştırma:**
```bash
sudo $(which python3) src/test_npu.py
```

*Beklenen Çıktı:*
```text
--- Orange Pi 5 RKNN NPU Başlatılıyor ---
[BAŞARILI] 3 NPU Çekirdeği de donanımsal olarak uyandırıldı!

--- Anlık NPU Çekirdek Durumu ---
NPU load:  Core0: 0%, Core1: 0%, Core2: 0%
```

---

## **6. Özet ve Sonraki Adım**

Artık Orange Pi 5'inizin 6 TOPS gücündeki donanımsal yapay zeka hızlandırıcısı kullanıma hazırdır. 

Bir sonraki adımda:
* Bilgisayarınızdaki bir **YOLOv8** veya **MobileNet** modelini `.rknn` formatına dönüştürüp, Orange Pi 5 üzerinde kamera veya video akışında saniyede 60+ FPS ile gerçek zamanlı nesne tanıma yaptırabilirsiniz.

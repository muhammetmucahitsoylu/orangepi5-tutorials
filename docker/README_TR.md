[🇹🇷 Türkçe](./README_TR.md) | [🇬🇧 English](./README.md)

---

# Konteynerleştirilmiş RKNN-Toolkit-Lite2 Ortamı (Orange Pi 5)

> Doğrudan donanım köprüsü kullanarak **Orange Pi 5 / 5B / 5 Plus (RK3588 / RK3588S)** üzerindeki Yapay Zeka İşlemcisinde (NPU) izole, kararlı ve tekrarlanabilir yapay görme çıkarımı gerçekleştirin.

---

## 🧠 Orange Pi 5 Üzerinde Gömülü Yapay Zeka Nasıl Çalışır? (Mühendislik Hattı)

Derin öğrenme modellerini işlemciyi (CPU) boğmadan, aşırı ısınma ve tek haneli kare hızları yaşamadan çalıştırmak için çip üzerindeki **6 TOPS 3 Çekirdekli NPU** kullanılır.

Model geliştirmeden fiziksel NPU çıkarımına kadar olan uçtan uca akış:

```text
[ 1. Bilgisayar / Ekran Kartı ]           [ 3. Orange Pi 5 Donanımı ]
+-------------------------------+         +-----------------------------------------+
| PyTorch / Ultralytics YOLO    |         |  Docker: opi5_rknn_workspace            |
| Format: FP32 (32-bit Float)   |         |                                         |
+---------------+---------------+         |  +-----------------------------------+  |
                |                         |  | 4. Python Görüntü Hattı (OpenCV)  |  |
    [ 2. RKNN-Toolkit2 ]                  |  |    - BGR -> RGB Renk Dönüşümü     |  |
    (Model Dönüştürme &                   |  |    - Resize (224x224 / 640x640)   |  |
     INT8 Kuantizasyon)                   |  +-----------------+-----------------+  |
                |                         |                    |                    |
                v                         |  +-----------------v-----------------+  |
+-------------------------------+         |  | rknn-toolkit-lite2 (librknnrt.so) |  |
|  model.rknn İkili Dosyası     |         |  +-----------------+-----------------+  |
|  (Hedef Çip: RK3588)          | =======>|                    | Sıfır Kopyalama DMA|
+-------------------------------+         |  +-----------------v-----------------+  |
                                          |  | Kernel Sürücüsü: /dev/dri/renderD129 |
                                          +--+-----------------+-----------------+--+
                                                               |
                                          +--------------------v--------------------+
                                          |  RK3588S 3 Çekirdekli NPU Silikonu      |
                                          |  ⚡ 2.8 ms Gecikme (~350+ FPS)          |
                                          +-----------------------------------------+
```

1. **Model Kaynağı (FP32):** Standart yapay zeka modelleri 32-bit kayan noktalı sayılarla çalışır. Bunu gömülü ARM CPU'da çalıştırmak hem yavaştır (~3-5 FPS) hem de aşırı güç harcar.
2. **Kuantizasyon ve Derleme (RKNN-Toolkit2):** Rockchip'in derleyicisi bu ondalıklı ağırlıkları 8-bit tam sayılara (**INT8**) sıkıştırır. NPU donanımındaki silikon çarpıcılar bu tamsayıları ışık hızında işler.
3. **Donanım Dağıtımı (RKNN-Toolkit-Lite2):** Kart üzerinde hafif çalışma motoru `.rknn` dosyasını doğrudan NPU belleğine DMA ile eşler.
4. **Çekirdek Hızlandırma:** Linux Kernel 6.1+ üzerinde sürücü DRM alt sistemi (`/dev/dri/renderD129`) üzerinden 3 NPU çekirdeğini aynı anda tam güçte devreye sokar.

---

## 🚀 Hızlı Başlangıç (Tek Adımda Başlatma)

Orange Pi 5 terminalinde depo kök dizininden:

```bash
cd docker
docker compose up -d --build
```

### 1. Donanım Doğrulama Testi
Linux çekirdek sürücüsünün ve 3 NPU çekirdeğinin Docker içinden erişilebilir olduğunu test edin:
```bash
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_npu.py
```

Beklenen çıktı:
```text
[*] Initializing runtime with core_mask=NPU_CORE_0_1_2 (Tri-Core 6 TOPS)...
I RKNN: librknnrt version: 2.3.2
I RKNN: RKNN Driver Information, version: 0.9.7
[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!
[PASSED] Physical RK3588 NPU passthrough verified 100% inside Docker!
```

---

## 🔬 Çalışmaya Hazır Yapay Görme Demoları

### A. Gerçek Zamanlı Görüntü Sınıflandırma (`test_image_ai.py`)
Fotoğrafları 1000 kategori arasında **~2.8 milisaniyede (~350+ FPS)** sınıflandırır. Teşhisi ve NPU hızını görsel üzerine HUD paneli olarak işler ve `classification_result.jpg` olarak kaydeder:

```bash
# Hazır testler: dog, monkey, plane, apple, fruits, shuttle, kangal
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_image_ai.py dog
docker exec -w /workspace/docker opi5_rknn_workspace python3 test_image_ai.py kangal
```

### B. Nesne Tespiti: YOLOv5 ve YOLOv8
3 çekirdekli NPU üzerinde hem resmi Çıpa Tabanlı (**YOLOv5**) hem de Çıpasız DFL (**YOLOv8**) mimarilerini destekliyoruz:

```bash
# 1. Resmi Yüksek Doğruluklu YOLOv5 (Tam COCO 330k veri seti @ ~31 ms / 32 FPS):
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolo_demo.py bus.jpg
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolo_demo.py kangal.jpg

# 2. Deneysel Çıpasız YOLOv8 (DFL mimarisi @ ~22 ms / 45 FPS):
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolov8.py bus.jpg
```

👉 **Ayrıntılı Teknik Karşılaştırma Rehberi:** Tam hız, doğruluk ve NPU silikon mimari analizi için [`YOLO_COMPARISON_TR.md`](./YOLO_COMPARISON_TR.md) dosyasını inceleyin.

---

## 🌐 Tarayıcı Üzerinden Görsel İnceleme

Testler SSH üzerinden komut satırında çalıştığı için oluşturulan kutucuklu görselleri doğrudan tarayıcınızda açabilirsiniz:

1. **Arka plan HTTP web sunucusunu** konteyner içinde başlatın:
   ```bash
   docker exec -d -w /workspace/docker opi5_rknn_workspace python3 -m http.server 8000
   ```

2. **Bilgisayarınızın tarayıcısında açın:**
   - Sınıflandırma çıktısı: `http://<ORANGE_PI_IP>:8000/classification_result.jpg`
   - YOLO tespit çıktısı: `http://<ORANGE_PI_IP>:8000/yolo_result.jpg`
   - Tüm dosyalar: `http://<ORANGE_PI_IP>:8000/`

---

## ⚙️ Docker Mimarisi ve Donanım Geçişi (Passthrough)

* **Doğrudan Cihaz Geçişi:** `docker-compose.yml`, `/dev/dri` ve `/dev/dma_heap` aygıtlarını konteyner içine bağlar.
  * **Kernel 6.1+ (Ubuntu 24.04 Noble / Debian Bookworm):** Rockchip RKNPU sürücüsü DRM alt sisteminde `/dev/dri/renderD129` (NPU hızlandırıcı) ve `/dev/dri/renderD128` (Mali GPU) olarak tanımlanır.
  * **Eski Kernel 5.10 (Ubuntu 22.04 Jammy):** `/dev/rknpu` aygıtını kullanır.
* **SoC Donanım Tanıma:** RKNN motoru çip uyumluluğunu `/proc/device-tree/compatible` dosyasından okur. Docker varsayılanda `/proc` dizinini kısıtladığı için `privileged: true` ve salt okunur bağlama (`/proc/device-tree/compatible:...:ro`) kullanılmıştır.
* **Paylaşılan Bellek (IPC Host):** `ipc: host` ayarı, Linux kamera yayınları (V4L2/GStreamer) ile konteynerdeki yapay zeka modelleri arasında sıfır kopyalama performansı sağlar.
* **Ana Ağ Modu (Network Mode Host):** Konteyner içinde açılan portları (HTTP, RTSP, Flask vb.) doğrudan kartın kendi yerel IP'sine bağlar.

[🇹🇷 Türkçe](./YOLO_COMPARISON_TR.md) | [🇬🇧 English](./YOLO_COMPARISON.md)

---

# Orange Pi 5 Üzerinde YOLOv5 ve YOLOv8 Karşılaştırması (RK3588 NPU Benchmark)

> Rockchip RK3588S Yapay Zeka İşlemcisi (NPU) üzerinde **Çıpa Tabanlı (Anchor-Based - YOLOv5)** ve **Çıpasız / DFL (Anchor-Free - YOLOv8)** nesne tespit mimarilerinin donanımsal karşılaştırma ve başa baş benchmark analizi.

---

## 📊 Başa Başa Karşılaştırma Matrisi (Benchmark)

Aşağıdaki sonuçlar fiziksel **Orange Pi 5 (8 GB RAM, Ubuntu 24.04 Kernel 6.1)** donanımında, 3 NPU çekirdeği birden (`NPU_CORE_0_1_2` @ 6 TOPS) kullanılarak ölçülmüştür:

| Kriter / Metrik | YOLOv5s (Resmi Rockchip Modeli) | YOLOv8n (Deneysel DFL Modeli) | Analiz & Kazanan |
|---|---|---|---|
| **Çalıştırma Betiği** | `run_yolo_demo.py` | `run_yolov8.py` | — |
| **Model Boyutu** | **8.47 MB** (`yolov5s-640-640.rknn`) | **3.48 MB** (`yolov8_80class.rknn`) | YOLOv8 (Daha küçük dosya boyutu) |
| **NPU İşlem Süresi** | **30.74 ms** | **22.54 ms** | **YOLOv8 (~44.4 FPS vs 32.5 FPS)** |
| **Çıkış Katmanı Mimarisi** | **Anchor-Based** (3 ölçek × 3 çıpa) | **Anchor-Free** (DFL 16-bin regresyon) | YOLOv8 matematiksel olarak daha yeni |
| **Aktivasyon Fonksiyonu**| ReLU (RKNN grafiğine gömülü) | ReLU (SiLU yerine özel NPU uyarlaması) | İkisi de INT8 için optimize |
| **Eğitim Veri Seti** | **Tam MS COCO (330.000 Görsel)** | **COCO-128 Alt Kümesi (128 Görsel)** | **YOLOv5s (Üretim Düzeyi Doğruluk)** |
| **Doğruluk Skoru (`bus.jpg`)** | **İnsan (%87), Otobüs (%71)** | Düşük / Aşırı Öğrenme (Eşik >0.15 ister) | **YOLOv5s (%85+ Yüksek Güvenilirlik)** |
| **RK3588 Silikon Uyumu** | **%100 Donanımsal Silikon Uyumu** | CPU DFL / Softmax Ek Hesaplama Yükü | **YOLOv5s (Sıfır İşlemci Yükü)** |

---

## 🧠 Neden Gömülü Donanımda "YOLOv8 > YOLOv5" Kuralı Her Zaman Geçerli Değildir?

Masaüstü bilgisayarlardaki güçlü ekran kartlarında (örneğin NVIDIA RTX 4090) YOLOv8 tartışmasız üstündür; çünkü masaüstü GPU'lar devasa FP16/FP32 matris ünitelerine sahiptir ve dinamik matematiksel işlemleri kolayca çözer.

Ancak **Gömülü NPU Donanımlarında (Rockchip, Raspberry Pi AI, Hailo)** performansı belirleyen 3 kritik mühendislik gerçeği vardır:

### 1. Silikon Tasarım Tarihi Uyumu
* **Rockchip RK3588 / RK3588S** çipinin donanımı **2021–2022** yıllarında tasarlandı ve fabrikadan çıktı.
* **Ultralytics YOLOv8** ise **Ocak 2023** tarihinde yayınlandı.
* RK3588 çipinin içindeki donanımsal çarpıcılar, o dönemin altın standardı olan **YOLOv5'in C3 konvolüsyonel katmanlarına** doğrudan donanım hızlandırması verecek şekilde silikona işlenmiştir.

### 2. DFL (Distribution Focal Loss) ve INT8 Kuantizasyonu
* YOLOv5 nesne kutularını $(x, y, w, h)$ doğrusal ölçekleme ve sabit çıpalarla (anchors) doğrudan tahmin eder. Bu da NPU'nun doğrudan sevdiği basit tamsayı çarpımıdır.
* YOLOv8 ise koordinatları 16 ayrık bölme üzerinde olasılık dağılımı olarak çözen **DFL** ve ardından Softmax katmanı kullanır.
* NPU'lar INT8 hassasiyetinde dinamik kanallar arası Softmax işlemlerinde zorlanır. Bu hesaplama ya ARM ana işlemcisine (CPU) aktarılır (gecikme yaratır) ya da yaklaşıklık formülleri kullanılarak doğrulukta sapmalara yol açar.

### 3. Kuantizasyon Kalibrasyon Veri Seti
* Bir INT8 yapay zeka modelinin doğruluğu, kuantize edilirken (sıkıştırılırken) kullanılan veri setinin kalitesine doğrudan bağlıdır.
* **`yolov5s-640-640.rknn`**, Rockchip mühendisleri tarafından **330.000 fotoğraflık tam MS COCO veri setiyle** eğitilmiş resmi bir fabrika modelidir.
* Topluluk tarafından dönüştürülen deneysel YOLOv8 `.rknn` modelleri ise genellikle COCO-128 gibi minyatür veri setleriyle kavram kanıtlama (PoC) amacıyla üretildiğinden, gerçek dünya fotoğraflarında düşük güven skorları verir.

---

## 🚀 Orange Pi 5 Üzerinde Testleri Çalıştırma

Her iki model de Docker ortamında kullanıma hazırdır:

### A. YOLOv5s Testi (Resmi Yüksek Doğruluk)
```bash
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolo_demo.py bus.jpg
```
* Tarayıcıdan görüntüle: `http://<ORANGE_PI_IP>:8000/yolo_result.jpg`

### B. YOLOv8n Testi (Çıpasız Deneysel Model)
```bash
docker exec -w /workspace/docker opi5_rknn_workspace python3 run_yolov8.py bus.jpg
```
* Tarayıcıdan görüntüle: `http://<ORANGE_PI_IP>:8000/yolov8_result.jpg`

---

## 🎯 Mühendislik Sonucu & Öneri

* **Üretim Projeleri, Akıllı Güvenlik Kameraları ve Robotik:** Orange Pi 5 üzerinde en yüksek kararlılık, sıfır hatalı pozitif ve %85+ doğruluk için **YOLOv5s** tartışmasız en iyi seçenektir.
* **Akademik Araştırma ve Yüksek FPS Deneyleri:** **YOLOv8**, kendi alanınıza özel veri setiyle sıfırdan eğitilip tam kuantize edildiğinde geleceğin mimarisini temsil eder.

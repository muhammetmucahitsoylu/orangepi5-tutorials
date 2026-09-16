# **Orange Pi 5 (RK3588S) Yapay Zeka Destekli Akıllı Zoom ve Süper Çözünürlük Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar, modeller ve web sunucusu **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS (Rockchip BSP Kernel 6.1)** üzerinde bizzat fiziksel donanımda (A4Tech FHD 1080P USB Kamera) test edilmiş ve canlı olarak doğrulanmıştır.

Bu rehber; Orange Pi 5 üzerinde çalışan bir kamera akışında **dijital zoom yapıldığında piksellerin bozulması ve bulanıklaşması problemini**, Derin Öğrenme tabanlı **Süper Çözünürlük (Super-Resolution - FSRCNN & ESPCN)** sinir ağları kullanarak gerçek zamanlı olarak çözen, bölünmüş ekran (side-by-side) karşılaştırması ve interaktif web paneli barındıran uçtan uca bir yapay zeka bilgisayarlı görü projesidir.

---

## **1. Temel Problem: Dijital Zoom Neden Kaliteyi Bozar?**

Optik zoom bulunmayan standart kameralarda (veya mesafenin uzak olduğu güvenlik/robotik senaryolarında) belirli bir nesneye (yüz, araç plakası, küçük metinler) dijital olarak yaklaşıldığında iki adım gerçekleşir:

1. **ROI (İlgilenilen Bölge) Kırpma:** Sensörün 1920x1080 pikselinin yalnızca ortadaki küçük bir parçası (örneğin 240x240 piksel) kırpılır.
2. **Yeniden Boyutlandırma (Geleneksel Enterpolasyon):** Kırpılan küçük parça ekrana sığması için 480x480 veya 960x960 piksele esnetilir.

```
Geleneksel Dijital Zoom Akışı (Kalite Kaybı):
[ Küçük ROI: 240x240 ] ──(Bicubic / Bilinear Esnetme)──> [ Bulanık & Pikselli Çıktı: 480x480 ]
*Piksel değerleri komşu piksellerin basit ortalamasıyla doldurulur; kayıp kenar detayları ve dokular asla kurtarılamaz!
```

Geleneksel yöntemlerin kısıtları:
* **Nearest Neighbor:** Pikselleri kutu kutu büyütür, merdiven etkisi (aliasing) ve aşırı piksellenme oluşturur.
* **Bilinear & Bicubic:** Pikseller arasındaki geçişleri yumuşatır, ancak görüntüyü aşırı flulaştırır (soft blur); ince detaylar ve metinler okunamaz hale gelir.
* **Lanczos:** Keskinleştirmeye çalışırken kenarlarda çınlama (ringing / halo artifact) üretir.

---

## **2. Yapay Zeka Çözümü: Derin Öğrenme ile Süper Çözünürlük**

Yapay Zeka Süper Çözünürlük (Neural Super-Resolution) modelleri, piksel esnetmek yerine **milyonlarca yüksek çözünürlüklü görüntü üzerinde eğitilmiş evrişimli sinir ağları (CNN)** kullanır. Düşük çözünürlüklü pikseller arasındaki boşlukları matematiksel bir tahminle değil; kenarların, dokuların ve desenlerin doğasını anlayarak **yüksek frekanslı detayları sıfırdan inşa ederek** doldurur.

```
Yapay Zeka Akıllı Zoom Akışı (Süper Çözünürlük):
                                    ┌──> Geleneksel Bicubic Zoom ──> [ Bulanık Referans ]
[ Canlı Kamera ] ──> [ ROI Kırpma ] ┤
                                    └──> Derin Öğrenme (FSRCNN)  ──> [ Jilet Keskinliğinde AI Çıktı ]
```

Bu projede kullanılan iki özel mimari:

### A) FSRCNN (Fast Super-Resolution Convolutional Neural Network)
* **Tasarım:** Orijinal SRCNN'in aksine, görüntüyü modelin başında büyütmek yerine düşük çözünürlüklü ham pikseller üzerinde çalışır (Feature Extraction ➔ Shrinking ➔ Mapping ➔ Expanding).
* **Büyütme:** En sonda ters evrişim (deconvolution) katmanıyla görüntüyü 2x / 4x büyütür.
* **Avantajı:** Yüksek görsel netlik, temiz kontrast ve keskin kenarlar.

### B) ESPCN (Efficient Sub-Pixel Convolutional Neural Network)
* **Tasarım:** Standart enterpolasyon veya deconvolution yerine **PixelShuffle (Sub-Pixel Convolution)** kullanır.
* **Çalışma Prensibi:** Kanallar boyunca özellik çıkarır ve son katmanda kanalları uzamsal piksellere dönüştürerek ($r^2$ kanal ➔ $r \times r$ piksel) doğrudan yüksek çözünürlüklü kare üretir.
* **Avantajı:** Olağanüstü düşük hesaplama maliyeti; Orange Pi 5 üzerinde **~23+ FPS** ile gerçek zamanlı canlı akış sağlar.

### C) Rockchip RK3588 Tri-Core NPU Donanım Hızlandırması (6.0 TOPS)
* **Tasarım:** Sub-Pixel CNN (ESPCN 3x) mimarisi ONNX formatından Rockchip NPU ikili formatına (`super_resolution_rk3588.rknn`) derlenmiştir.
* **Çalışma Prensibi:** Görüntünün Parlaklık (Y-Luminance) kanalı `[1, 1, 224, 224]` tensörüne dönüştürülerek doğrudan RK3588'in 3 çekirdekli NPU donanımına (`NPU_CORE_0_1_2`) verilir. NPU, 3x büyütülmüş `[1, 1, 672, 672]` parlaklık haritasını sıfır CPU yüküyle üretir. Renk kanalları (Cr/Cb) bikübik enterpolasyon ile eşleştirilerek birleştirilir.
* **Avantajı:** CPU çekirdeklerini tamamen serbest bırakır (yaklaşık %0 CPU yükü), **34.38 ms (~29.1 FPS)** ile ultra akıcı canlı donanım çıkarımı sunar.

---

## **3. Sistem Mimarisi**

```
┌────────────────────────────────────────────────────────────────────────┐
│             A4Tech FHD 1080P USB Kamera (/dev/video0)                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ 1920x1080 @ 30 FPS (FourCC MJPG)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  İş Parçacığı 1: Kamera Yakalama Motoru (CameraThread)                  │
│  - Donanım tamponunu sürekli tazeler (Sıfır Gecikme / Zero Latency)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Ham 1080p Kare)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  İş Parçacığı 2: Süper Çözünürlük İşleme Motoru (ProcessingThread)      │
│  - Dinamik Zoom Penceresi Kırpma (1.0x – 4.0x)                         │
│  - Motor Seçimi:                                                        │
│     ├─► [NPU Motoru]: Rockchip RK3588 3 Çekirdek NPU (ESPCN 3x, 6 TOPS) │
│     └─► [CPU Motoru]: OpenCV DNN (FSRCNN 2x/4x, ESPCN 2x/4x)           │
│  - Akıllı Netlik: CLAHE Mikro-Kontrast + Uyarlamalı Unsharp Mask       │
│  - Karşılaştırma: [Bicubic Baseline] vs [Akıllı Yapay Zeka Zoom]       │
│  - Ayrılmış Ekran (Split View) + Donanım Telemetrisi (FPS, Gecikme, C) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Dağıtım: Dahili Çoklu İş Parçacıklı HTTP Web Sunucusu (Port 5000)     │
│  - Tarayıcı üzerinden sıfır bağımlılıkla canlı MJPEG izleme             │
│  - Canlı Zoom (1.0x - 4.0x), Keskinlik ve Kontrast Kaydırıcıları        │
│  - Tek Tıkla NPU (6 TOPS) ve CPU modelleri arasında anlık geçiş        │
│  - Yüksek Çözünürlüklü Karşılaştırma Fotoğrafı Kaydetme (Snapshot)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **4. Donanım Benchmark Sonuçları (Orange Pi 5 Fiziksel Test)**

Aşağıdaki ölçümler, **Orange Pi 5 (RK3588S)** donanımı üzerinde doğrudan bağlı fiziksel USB kamera ile `benchmark_zoom.py` aracıyla bizzat test edilmiştir:

* **Giriş Çözünürlüğü:** 1920x1080 Full HD
* **Kırpılan ROI Boyutu:** 224x224 piksel
* **Büyütme Faktörü:** 2x / 3x Digital Zoom (Hedef Çıktı: 448x448 / 672x672 piksel)

| Yöntem / Algoritma | Çalışma Katmanı / Donanım | Ortalama Gecikme (ms) | Teorik FPS | Görsel Kalite & Karakteristik |
| :--- | :--- | :--- | :--- | :--- |
| **Nearest Neighbor** | Geleneksel (CPU) | **0.41 ms** | >2400 FPS | Aşırı merdiven etkisi, blok blok pikseller |
| **Bilinear** | Geleneksel (CPU) | **1.15 ms** | ~870 FPS | Yumuşatılmış ancak bariz şekilde bulanık |
| **Bicubic (Standart Zoom)**| Geleneksel Baseline (CPU)| **2.25 ms** | ~440 FPS | Endüstri standardı dijital zoom; flulaşma yüksek |
| **Lanczos-4** | Geleneksel Resampling | **1.96 ms** | ~510 FPS | Kenarlar daha belirgin fakat çınlama (ringing) var |
| **FSRCNN x2 (CPU AI)** | Derin Öğrenme (CPU DNN) | **82.81 ms** | **~12.1 FPS** | Maksimum yapısal sadakat ve net kenar onarımı |
| **ESPCN x2 (CPU AI)** | Derin Öğrenme (CPU DNN) | **42.57 ms** | **~23.5 FPS** | Canlı video için ideal gerçek zamanlı CPU çıkarımı |
| **RK3588 NPU (ESPCN 3x)** | **Rockchip NPU (6.0 TOPS)** | **34.38 ms** | **~29.1 FPS** | **Tri-Core NPU donanım hızlandırması, ~%0 CPU yükü** |
| **NPU + Smart Enhancer** | **NPU + CLAHE + Keskinlik** | **42.95 ms** | **~23.3 FPS** | **Jilet gibi net metinler ve devre yolları** |

> 🌡️ **Sıcaklık ve Enerji:** NPU çıkarımı CPU'yu meşgul etmediği için sürekli canlı akışta dahi SoC sıcaklığı **~49.9 °C** seviyesinde kalır; pasif alüminyum soğutucu ile termal kısma (throttling) yaşanmaz.

### **Fiziksel Donanım Karşılaştırma Görselleri (Orange Pi Kutusu Üzerinde 4.0x Zoom)**

A4Tech FHD 1080P kameramızla V4L2 1080p modunda doğrudan Orange Pi kutusunun yazı ve devre yolları üzerinde alınan gerçek donanım ekran yakalamaları:

##### FSRCNN (4x Smart AI Süper Çözünürlük + Kenar Keskinleştirme) vs. Klasik Bicubic Zoom
![FSRCNN 4x Yapay Zeka Zoom](../../assets/benchmarks/ai_zoom_fsrcnn_x4.jpg)

##### ESPCN (4x Sub-Pixel Süper Çözünürlük + Kenar Keskinleştirme) vs. Klasik Bicubic Zoom
![ESPCN 4x Sub-Pixel Zoom](../../assets/benchmarks/ai_zoom_espcn_x4.jpg)

##### FSRCNN (2x) ve ESPCN (2x) Akıllı Zoom Karşılaştırmaları (3.7x Zoom)
| FSRCNN 2x Smart AI Zoom | ESPCN 2x Smart AI Zoom |
| :---: | :---: |
| ![FSRCNN 2x](../../assets/benchmarks/ai_zoom_fsrcnn_x2.jpg) | ![ESPCN 2x](../../assets/benchmarks/ai_zoom_espcn_x2.jpg) |

> 💡 **Farkın Sırrı:** Sol taraftaki klasik Bicubic zoom pikselleri basit ortalama ile yayarak bulanıklaştırırken, sağ taraftaki **Smart AI** motoru Rockchip RK3588 Tri-Core NPU donanımında alt piksel evrişimi çalıştırıp, CLAHE mikro-kontrast ve uyarlamalı kenar keskinleştirme uygulayarak harf ve devre yollarını jilet gibi netleştirir.

---

## **5. Kurulum ve Çalıştırma**

### Adım 1: Hazır Derlenmiş Modelleri İndirme ve Doğrulama
Modeller repoya dahil edilmiş olarak gelir (`models/` altında). Dilerseniz modelleri tek tıkla aşağıdaki resmi Release bağlantılarından doğrudan indirebilir veya otomatik indiriciyi çalıştırabilirsiniz:

| Model Adı | Hedef Donanım / Çalışma Katmanı | Format | Boyut | Doğrudan İndirme Bağlantısı |
| :--- | :--- | :---: | :---: | :--- |
| **ESPCN (3x Süper Çözünürlük)** | **Rockchip RK3588 NPU (6 TOPS)** | `.rknn` | **512 KB** | [Doğrudan İndir `super_resolution_rk3588.rknn`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/super_resolution_rk3588.rknn) |
| **Sub-Pixel CNN (3x ONNX)** | Derleyici / ONNX Runtime | `.onnx` | 240 KB | [Doğrudan İndir `super-resolution-10.onnx`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/super-resolution-10.onnx) |
| **FSRCNN (2x Süper Çözünürlük)**| OpenCV DNN (CPU) | `.pb` | 39 KB | [Doğrudan İndir `FSRCNN_x2.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/FSRCNN_x2.pb) |
| **FSRCNN (4x Süper Çözünürlük)**| OpenCV DNN (CPU) | `.pb` | 42 KB | [Doğrudan İndir `FSRCNN_x4.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/FSRCNN_x4.pb) |
| **ESPCN (2x Süper Çözünürlük)** | OpenCV DNN (CPU) | `.pb` | 86 KB | [Doğrudan İndir `ESPCN_x2.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/ESPCN_x2.pb) |
| **ESPCN (4x Süper Çözünürlük)** | OpenCV DNN (CPU) | `.pb` | 100 KB | [Doğrudan İndir `ESPCN_x4.pb`](https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0/ESPCN_x4.pb) |

```bash
# Otomatik indirici ile tüm modelleri tek seferde çekin:
cd ~/orangepi5-tutorials/projects/14-AI-Smart-Zoom-Super-Resolution
python3 models/download_models.py
```

### Adım 2: (Opsiyonel) ONNX'ten RKNN İkili Modeline Derleme
Repoda RK3588 için derlenmiş `super_resolution_rk3588.rknn` hazır olarak bulunmaktadır. Modeli sıfırdan x86 PC veya WSL üzerinde derlemek isterseniz:

```bash
python3 models/convert_to_rknn.py
```

### Adım 3: CLI Benchmark ve Çok Panelli Karşılaştırma Görseli Üretme
Kameranızdan veya bir görselden kare alarak Klasik Enterpolasyon, CPU AI ve **RK3588 NPU** yöntemlerini yan yana kıyaslayan 6 panelli görsel oluşturur:

```bash
# 2x Dijital Zoom ve NPU Kıyaslaması:
python3 benchmark_zoom.py --source 0 --scale 2 --crop-size 224 --output zoom_comparison_2x.jpg
```

Oluşan `zoom_comparison_2x.jpg` dosyası her algoritmanın gecikme süresini (ms) ve FPS değerini başlık olarak üzerine basar.

### Adım 4: Canlı İnteraktif Web Yayınını Başlatma
Canlı kamera akışını yapay zeka zoom motoruyla birleştiren web sunucusunu başlatın:

```bash
python3 ai_zoom_stream.py --source 0 --port 5000
```

Tarayıcınızdan şu adrese gidin:
```
http://<ORANGE_PI_IP>:5000
```
Web panelindeki **"⚡ NPU ESPCN (3x 6-TOPS)"** butonuna tıklayarak RK3588 donanım hızlandırmasını devreye alabilirsiniz!

---

## **6. Web Arayüzü Özellikleri**

1. **Bölünmüş Ekran (Split Screen):** Sol tarafta kameranın klasik bulanık dijital zoom görüntüsü, sağ tarafta FSRCNN/ESPCN ile netleştirilmiş süper çözünürlüklü görüntü gerçek zamanlı yan yana akar.
2. **Dinamik Zoom Kaydırıcısı (1.0x – 4.0x):** Kaydırıcıyı hareket ettirdiğiniz anda kamera görüntüsü donmadan veya takılmadan hedef alana anlık odaklanır.
3. **Model Değiştirici:** Tek tıkla `FSRCNN (2x)`, `FSRCNN (4x)`, `ESPCN (2x)` ve `ESPCN (4x)` modelleri arasında geçiş yapabilirsiniz.
4. **Görünüm Modları:** İster yan yana bölünmüş ekran, ister sadece yapay zeka tam ekran, ister sadece geleneksel zoom modunda izleyin.
5. **Anlık Fotoğraf Kaydetme:** *"Capture High-Res Snapshot"* butonuna bastığınız anda o anki karşılaştırma karesi diske yüksek kalitede JPEG olarak yazılır.

---

## **7. Üretim ve Performans İpuçları**

1. **Giriş Çözünürlüğü ve ROI Dengesi:**
   Gerçek zamanlı derin öğrenme çıkarımında giriş tensör boyutu büyüdükçe FLOPS katlanarak artar. `ai_zoom_stream.py` içindeki otomatik boyut dengeleyici, kırpılan ROI'yi 320x240 piksel sınırında tutarak canlı yayında 20+ FPS akıcılık sağlar.
2. **Arka Planda Sürekli Çalıştırma (Systemd / Daemon):**
   Cihaz açıldığında AI Zoom sunucusunun otomatik başlaması için `nohup` veya `systemd` servisi olarak tanımlanabilir:
   ```bash
   nohup python3 ai_zoom_stream.py --source 0 --port 5000 > /tmp/ai_zoom.log 2>&1 &
   ```
3. **Sıfır Harici PIP Bağımlılığı:**
   Sunucu; Flask veya harici ağır framework'lere ihtiyaç duymadan, Python'un standart kütüphanesindeki `http.server` ve `socketserver.ThreadingMixIn` sınıflarıyla sıfır ek paketle çalışacak şekilde optimize edilmiştir.

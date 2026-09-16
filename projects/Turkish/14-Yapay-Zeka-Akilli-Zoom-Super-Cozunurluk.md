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
* **Avantajı:** Olağanüstü düşük hesaplama maliyeti; Orange Pi 5 üzerinde **~22+ FPS** ile gerçek zamanlı canlı akış sağlar.

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
                                    │ (Ham Kare)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  İş Parçacığı 2: Süper Çözünürlük İşleme Motoru (ProcessingThread)      │
│  - Dinamik Zoom Penceresi Kırpma (1.0x – 4.0x)                         │
│  - Paralel Karşılaştırma: [Bicubic Zoom] vs [FSRCNN / ESPCN AI Zoom]   │
│  - Ayrılmış Ekran (Split Screen) ve Telemetri Verisi (FPS, Gecikme, C) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Dağıtım: Dahili Çoklu İş Parçacıklı HTTP Web Sunucusu (Port 5000)     │
│  - Tarayıcı üzerinden sıfır bağımlılıkla canlı MJPEG izleme             │
│  - Canlı Zoom Kaydırıcısı (1.0x - 4.0x) ve Model Değiştirme Butonları   │
│  - Tek Tıkla Yüksek Çözünürlüklü Karşılaştırma Fotoğrafı Kaydetme      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **4. Donanım Benchmark Sonuçları (Orange Pi 5 Fiziksel Test)**

Aşağıdaki ölçümler, **Orange Pi 5 (RK3588S)** donanımı üzerinde doğrudan bağlı fiziksel USB kamera ile `benchmark_zoom.py` aracıyla bizzat test edilmiştir:

* **Giriş Çözünürlüğü:** 1920x1080 Full HD
* **Kırpılan ROI Boyutu:** 240x240 piksel
* **Büyütme Faktörü:** 2x Digital Zoom (Hedef Çıktı: 480x480 piksel)

| Yöntem / Algoritma | Mimari Türü | Ortalama Gecikme (ms) | Teorik FPS | Görsel Kalite Özeti |
| :--- | :--- | :--- | :--- | :--- |
| **Nearest Neighbor** | Geleneksel | **0.35 ms** | ~2886 FPS | Aşırı merdiven etkisi, blok blok pikseller |
| **Bilinear** | Geleneksel | **1.01 ms** | ~986 FPS | Yumuşatılmış ancak bariz şekilde bulanık |
| **Bicubic (Standart Zoom)**| Geleneksel Baseline | **2.00 ms** | ~499 FPS | Endüstri standardı dijital zoom; flulaşma yüksek |
| **Lanczos-4** | Geleneksel Resampling | **2.83 ms** | ~352 FPS | Kenarlar daha belirgin fakat çınlama (ringing) var |
| **ESPCN x2 (Yapay Zeka)** | **Derin Öğrenme (CNN)**| **44.95 ms** | **~22.2 FPS** | **Canlı video için ideal; pürüzsüz ve keskin kenarlar** |
| **FSRCNN x2 (Yapay Zeka)**| **Derin Öğrenme (CNN)**| **65.33 ms** | **~15.3 FPS** | **Maksimum netlik ve yüksek frekanslı doku onarımı** |

> 🌡️ **Sıcaklık Notu:** 15 ardışık derin öğrenme çıkarımı ve sürekli kamera akışı boyunca SoC sıcaklığı sadece **55.5 °C** ölçülmüştür; pasif soğutucu + 3.3V sessiz fan ile termal kısma (throttling) riski sıfırdır.

---

## **5. Kurulum ve Çalıştırma**

### Adım 1: Proje Dizinine Geçiş ve Model Kontrolü
Modeller repoya dahil edilmiş olarak gelir (`models/` altında). Dilerseniz otomatik indiriciyi de çalıştırabilirsiniz:

```bash
cd ~/orangepi5-tutorials/projects/14-AI-Smart-Zoom-Super-Resolution
python3 models/download_models.py
```

### Adım 2: CLI Benchmark ve Karşılaştırma Fotoğrafı Üretme
Kameranızdan tek bir kare alarak 4 farklı yöntemi (Bicubic, Lanczos, FSRCNN, ESPCN) yan yana kıyaslayan bir görsel oluşturur:

```bash
# 2x Dijital Zoom Kıyaslaması:
python3 benchmark_zoom.py --source 0 --scale 2 --crop-size 240 --output zoom_comparison_2x.jpg

# 4x Dijital Zoom Kıyaslaması:
python3 benchmark_zoom.py --source 0 --scale 4 --crop-size 160 --output zoom_comparison_4x.jpg
```

Oluşan `zoom_comparison_2x.jpg` dosyası her algoritmanın gecikme süresini (ms) ve FPS değerini başlık olarak üzerine basar.

### Adım 3: Canlı İnteraktif Web Yayınını Başlatma
Canlı kamera akışını yapay zeka zoom motoruyla birleştiren web sunucusunu başlatın:

```bash
python3 ai_zoom_stream.py --source 0 --port 5000
```

Tarayıcınızdan şu adrese gidin:
```
http://<ORANGE_PI_IP>:5000
```

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

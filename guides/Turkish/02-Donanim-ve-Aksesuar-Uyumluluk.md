# **Orange Pi 5 (RK3588S) Donanım ve Aksesuar Uyumluluk Kılavuzu**

Bu kılavuz, Orange Pi 5 (Rockchip RK3588S) için doğru güç kaynağı, M.2 SSD, soğutma ve çevre birimlerini seçmeniz amacıyla hazırlanmıştır. Yanlış donanım tercihinden kaynaklanan kilitlenme, yeniden başlama ve tanınmayan aygıt sorunlarını önlemek için gerekli pratik bilgileri içerir.

---

## **1. Güç Kaynağı Seçimi**

Orange Pi 5 kullanıcılarının yaşadığı ani yeniden başlama veya yük altında kilitlenme sorunlarının temel nedeni yetersiz güç kaynağı kullanımıdır.

* **Önerilen Değer:** **5V / 4A (20W) sabit Type-C güç adaptörü.**
* **Standart Telefon Şarj Aletleri Neden Kullanılmamalıdır?**  
  Telefon adaptörleri (5V 2A veya 5V 3A) masaüstü açılışında, paket güncellemesinde (`apt update`) veya işlemci yüke girdiği anda gerekli anlık akımı sağlayamaz. Voltaj düştüğü anda kart kendini korumaya alarak aniden kapanır ya da yeniden başlar.
* **Hızlı Şarj (PD) Adaptörleri:**  
  Çok portlu akıllı telefon/laptop hızlı şarj adaptörleri sabit voltaj sağlamada kararsızlık yaşayabilir ve sistemin donmasına neden olabilir.
* **Sonuç:** Sorunsuz bir kullanım için resmi Orange Pi 5V 4A adaptörü veya kaliteli 5V 4A sabit çıkışlı bir adaptör tercih edilmelidir.

---

## **2. M.2 SSD Uyumluluğu ve Hız Beklentisi**

Kartın alt yüzeyinde bir adet M.2 yuvası yer almaktadır. Disk seçiminde dikkat edilmesi gereken kritik noktalar şunlardır:

### **Fiziksel Boyut (Form Factor): M.2 2242 Standardı**
* **Dahili Vida Yuvası 2242'dir:** Kartın altındaki pirinç vida yuvası **M.2 2242 (22mm genişlik, 42mm uzunluk)** boyutuna göre konumlandırılmıştır.
* **Standart 2280 SSD Takılır mı?** Piyasadaki en yaygın SSD'ler **2280 (80mm)** boyutundadır. 2280 bir disk yuvaya oturur ve elektriksel olarak sorunsuz çalışır; ancak diskin arka kısmı kartın vida yuvasının dışına taşar. Diski sabitlemek için küçük bir **2242-2280 metal/PCB uzatma braketi** kullanılmalıdır:

```
                  ORANGE PI 5 M.2 FİZİKSEL MONTAJ ŞEMASI
                  
  [M-Key Yuva]    |<------- 42mm ------->|<------- 38mm ------->|
  +------------+  +----------------------+----------------------+
  | [][][][][] |  |  M.2 2242 NVMe SSD   | 2280 Uzatma Braketi  |
  +------------+  +----------------------+----------------------+
                  |                      ( O )                  ( O )
                                           ▲                      ▲
                                    Yerleşik Kart Vidası    2280 Sabitleme Vidası
```

* **Doğrudan Karta Oturan Modeller (2242):** Kioxia BG4, Western Digital SN530 (2242), Transcend 430S veya KingSpec 2242 NVMe.

### **Yalnızca NVMe (PCIe) Desteklenir**
* Bu yuvaya **kesinlikle M.2 SATA SSD takılmamalıdır**. Anakart üzerinde SATA veri hattı bulunmadığı için kart SATA diskleri algılamaz (`lsblk` komutunda disk görünmez).
* Yalnızca **M.2 NVMe (PCIe)** protokolünü kullanan diskler çalışır (M-Key).

### **Hız Sınırı (PCIe 2.0 x1)**
* Orange Pi 5'in M.2 yuvası donanımsal olarak **PCIe 2.0 x1** hattı ile sınırlıdır.
* Bu nedenle 7000 MB/s hız vadeden en üst seviye Gen4 SSD'yi de taksanız, görebileceğiniz maksimum sıralı okuma/yazma hızı **~410 – 420 MB/s** civarında olacaktır.
* Pahalı ve yüksek hızlı disklere bütçe ayırmanıza gerek yoktur; bütçe dostu standart bir NVMe SSD kartın veri yolu kapasitesini tamamen dolduracaktır.

### **Uyku Modu (ASPM) Kilitlenme Sorunu ve Çözümü**
Bazı SSD modellerinde (örneğin Kingston NV2 veya bazı Phison denetleyicili modeller) kart boştayken veya uyku moduna geçtiğinde sistem kilitlenebilir. Bu durum diskin güç tasarrufundan uyanamamasından kaynaklanır.
* **Çözüm:** `/boot/armbianEnv.txt` veya kullandığınız dağıtımın boot yapılandırma dosyasına şu satırı ekleyin:
  ```text
  extraargs=pcie_aspm=off
  ```

---

## **3. Soğutma Seçimi (Pasif vs. Aktif Fan)**

İşlemci sıcaklığı **80°C** seviyesine ulaştığında kart kendini korumak için çalışma hızını düşürür (thermal throttling), bu da doğrudan performans kaybına yol açar.

* **Pasif Alüminyum Blok:** Yalnızca hafif masaüstü kullanımı veya temel komut satırı işlemleri için yeterlidir. Sürekli yük altında sıcaklık 80°C'yi aşar ve frekans kısılır.
* **Aktif Fanlı Soğutucu (Kesinlikle Önerilen):** 5V fanlı alüminyum soğutucu blok, 8 çekirdek %100 yük altındayken bile sıcaklığı 70–75°C bandında tutar. 7/24 sunucu, derleme veya yapay zeka projelerinde zorunludur.
* **Bağlantı:** Kart üzerindeki 2-pin 5V fan soketine takılır.

---

## **4. Ağ ve Çevre Birimleri**

### **Dahili Wi-Fi / Bluetooth Bulunmaz**
* Standart Orange Pi 5 modelinde dahili kablosuz bağlantı modülü yoktur.
* İnternet bağlantısı için yerleşik **Gigabit Ethernet** portu kullanılmalı ya da Linux çekirdeği tarafından doğrudan tanınan (Realtek RTL8821CU veya RTL8811CU gibi) bir USB Wi-Fi adaptörü takılmalıdır.

### **USB 3.0 Kablosuz Parazit Sorunu**
* Mavi renkli USB 3.0 portuna harici bir disk veya yüksek hızlı bellek takıldığında, 2.4 GHz kablosuz frekansında parazit oluşabilir.
* **Belirti:** USB 3.0 portunun yanına takılan kablosuz klavye/fare alıcılarında takılma, atlama veya sinyal kopması görülür.
* **Çözüm:** Kablosuz klavye/fare alıcısını USB 2.0 portuna takın veya küçük bir USB uzatma kablosu kullanarak alıcıyı USB 3.0 portundan uzaklaştırın.

---

## **5. Kamera Uyumluluğu: USB UVC vs. MIPI CSI (Rockchip RKAIQ ISP Gerçeği)**

Orange Pi 5 üzerinde 3 adet MIPI CSI kamera konnektörü (CAM1, CAM2, CAM3) yer alır; ancak kamera seçiminde kritik bir mühendislik ayrımı vardır:

### **A. USB Web Kameraları (UVC - Tak ve Çalıştır / Önerilen)**
* Logitech C920, C270 veya herhangi bir UVC uyumlu USB kamera dahili bir görüntü işlemcisi (ISP) barındırır.
* Doğrudan `/dev/video0` olarak sisteme kaydolur ve OpenCV'de `cv2.VideoCapture(0)` ile sıfır konfigürasyonla çalışır. Hızlı prototipleme ve bilgisayarlı görü projeleri için en sorunsuz çözümdür.

### **B. MIPI CSI Kameralar (OV13850, IMX415 vb. - RKAIQ ISP Mayın Tarlası)**
* MIPI CSI sensörleri karta ham Bayer (RAW) piksel verisi aktarır.
* Renk üretimi, otomatik pozlama (AE), beyaz dengesi (AWB) ve netleme (AF) işlemlerini yapmak için Rockchip'in kapalı kaynak **RKAIQ 3A Server (`librkaiq.so` / `rkaiq_3A_server`)** arka plan servisi çalışmak zorundadır.
* **Kritik Saha Deneyimi:** RKAIQ servisi başlatılmadan `/dev/video11` doğrudan standart OpenCV ile açılırsa görüntü zifiri karanlık çıkar veya kare yakalanamaz. MIPI CSI sensörleri ancak GStreamer `v4l2src` pipeline'ı ve medya kontrolcüsü (`media-ctl`) yönlendirmesiyle stabil çalıştırılabilir.

---

## **6. Özet Donanım Tablosu**

| Bileşen | Önerilen Tercih | Kaçınılması Gereken |
| :--- | :--- | :--- |
| **Güç Kaynağı** | 5V / 4A sabit Type-C adaptör | Standart telefon şarj aletleri (5V 2A), kararsız PD cihazları |
| **M.2 Depolama** | M.2 NVMe PCIe SSD (2242 veya uzatmalı 2280) | M.2 SATA SSD'ler (kesinlikle çalışmaz) |
| **Soğutma** | 5V aktif fanlı alüminyum soğutucu | Soğutucusuz kullanım veya yetersiz küçük pasif pedler |
| **Kamera** | Standart USB UVC Web Kamerası | ISP yapılandırması bilinmeyen ham MIPI CSI sensörleri |
| **Ağ** | Gigabit Ethernet kablosu veya uyumlu USB Wi-Fi | Sürücüsü olmayan uyumsuz kablosuz adaptörler |
| **Fare/Klavye Dongle** | USB 2.0 portu veya uzatma kablosu | USB 3.0 portunun hemen bitişiğindeki yuva (parazit riski) |

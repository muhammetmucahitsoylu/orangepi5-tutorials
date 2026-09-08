# **Orange Pi 5 (RK3588S) Donanım Doğrulama ve Stres Testi Kılavuzu**

Bu kılavuz; yeni kurulan bir Orange Pi 5 sisteminde işlemci (CPU), bellek (RAM), M.2 NVMe SSD ve soğutma performansının tam kapasite çalışıp çalışmadığını doğrulamak için hazırlanmıştır. Rehberdeki testler doğrudan donanım üzerinde uygulanmış referans değerlerle desteklenmiştir.

---

## **1. Test Öncesi Hazırlık ve Frekans Sabitleme**

Dinamik frekans geçişlerinden kaynaklanan dalgalanmaları önlemek ve sistemin tepe performansını ölçebilmek için test araçlarının kurulması ve işlemci/bellek denetleyicilerinin performans moduna alınması gerekir.

### **Gerekli Test Paketlerinin Kurulumu**
```bash
sudo apt update && sudo apt install -y stress-ng s-tui p7zip-full sysbench lm-sensors mbw fio
```

### **CPU ve Bellek Denetleyicisini (DMC) Performans Moduna Alma**
İşlemci ve bellek denetleyicisini en yüksek saat hızına kilitlemek için aşağıdaki komutları çalıştırın:
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo performance | sudo tee /sys/class/devfreq/dmc/governor
```

* **Bellek Frekansı Doğrulama:**
  ```bash
  cat /sys/class/devfreq/dmc/cur_freq
  ```
  *Beklenen Çıktı:* `2112000000` (Bellek denetleyicisinin 2.112 GHz tepe saat hızında çalıştığını doğrular).

---

## **2. CPU Stres Testi ve Termal Kararlılık (10 Dakika)**

Bu test, tüm çekirdekleri %100 yük altına sokarak soğutma sisteminizin sıcaklığı dengede tutup tutamadığını ve kartın frekans kısıp kısmadığını (thermal throttling) denetler.

### **Stres Testi Komutu**
```bash
stress-ng --cpu 8 --cpu-method matrixprod --metrics-brief --timeout 10m
```
*(Görsel izleme için ayrı bir terminalde `s-tui` komutunu çalıştırabilirsiniz).*

### **Referans Sıcaklık Değerleri (10 Dakika Sonunda)**

| Bileşen / Sensör | Aktif Fanlı Soğutucu | Pasif / Yetersiz Soğutucu | Durum Değerlendirmesi |
| :--- | :--- | :--- | :--- |
| **A76 Çekirdek Sıcaklığı** | **76.7 °C** | > 85 °C | 80 °C üzerinde frekans kısma başlar |
| **SoC Genel Sıcaklık** | **73.9 °C** | > 80 °C | Kararlı çalışma aralığı: < 78 °C |
| **A76 Tepe Saat Hızı** | **2352 MHz** | 1400 – 1800 MHz | **2352 MHz korunuyorsa soğutma başarılıdır** |

* **Yorum:** 10 dakika sonunda büyük çekirdekler (A76) 2304–2352 MHz saat hızını kesintisiz koruyorsa soğutma sisteminiz tam verimle çalışmaktadır.

---

## **3. CPU Saf Hesaplama ve Çok Çekirdek Performansı**

### **Sysbench Prime Testi (8 Thread)**
İşlemcinin saf matematiksel hesaplama gücünü ölçer:
```bash
sysbench cpu --cpu-max-prime=20000 --threads=8 run
```
* **Referans Skor:** **~5.340 events/sec** (Ortalama gecikme: ~1.50 ms).  
* *Yorum:* 5.000 events/sec altındaki skorlar işlemcinin sıcaklıktan dolayı frekans kıstığını veya governor ayarının performans modunda olmadığını gösterir.

### **7-Zip Sıkıştırma ve Çekirdek Gücü Testi**
```bash
# 8 Çekirdek Tam Kapasite:
7z b -mmt=8

# Yalnızca 4 Adet Cortex-A76 Büyük Çekirdeği:
taskset -c 4,5,6,7 7z b -mmt=4
```
* **Referans Skorlar:**
  * 8 Çekirdek Toplamı: **~19.350 MIPS**
  * 4x Cortex-A76 Çekirdekleri: **~14.400 MIPS**
* *Yorum:* 4 adet A76 çekirdeği tek başına toplam işlem gücünün yaklaşık **%74**'ünü üretir.

---

## **4. LPDDR4X / LPDDR5 Bellek Bant Genişliği Testi**

Bellek denetleyicisinin 2.112 GHz hızındaki saf veri aktarım performansını doğrulamak için `mbw` aracı kullanılır:
```bash
mbw -n 5 512
```

### **Referans Bellek Hızları**
* **MCBLOCK (Blok Tabanlı Tepe Hız):** **~25.200 MiB/s (~25.2 GB/s)**
* **DUMB (Dizi Kopyalama):** **~9.100 MiB/s (~9.1 GB/s)**
* **MEMCPY (Standart C Fonksiyonu):** **~8.900 MiB/s (~8.9 GB/s)**

*Yorum:* Tepe blok hızınız 20.000 MiB/s altındaysa bellek denetleyicisi düşük frekansta çalışıyor demektir. Aşama 1'deki DMC governor komutunu kontrol edin.

---

## **5. M.2 NVMe SSD Depolama Hız Testi (fio)**

Bu test, NVMe SSD'nin kartın PCIe 2.0 x1 veri yolunu tam kapasite doyurup doyurmadığını asenkron I/O motoru (`libaio`) ile ölçer.

### **Sıralı Okuma Testi (1M Blok)**
```bash
fio --name=seq_read --filename=/tmp/fio_test --size=2G --rw=read --bs=1M --direct=1 --ioengine=libaio --iodepth=16 --numjobs=1 --time_based --runtime=20 --group_reporting && rm -f /tmp/fio_test
```
* **Referans Sıralı Hız:** **~418 MB/s**  
* *Yorum:* Bu değer Orange Pi 5'in PCIe 2.0 x1 hattının fiziksel pratik tavanıdır. 400–420 MB/s aralığındaki değerler SSD'nin tam kapasitede çalıştığını kanıtlar.

### **4K Rastgele Okuma Testi (IOPS)**
```bash
fio --name=rand_read --filename=/tmp/fio_test --size=1G --rw=randread --bs=4k --direct=1 --ioengine=libaio --iodepth=64 --numjobs=4 --time_based --runtime=20 --group_reporting && rm -f /tmp/fio_test
```
* **Referans IOPS Değeri:** **~90.900 IOPS (~372 MB/s)** (Ortalama gecikme: ~2.79 ms).

---

## **6. NPU ve Donanım Hazırlık Doğrulaması**

İşletim sistemi seviyesinde NPU çekirdeklerinin tanınıp tanınmadığını terminal üzerinden doğrulamak için:

```bash
# NPU Çalışma Frekansı (1.0 GHz olmalıdır):
cat /sys/class/devfreq/fdab0000.npu/cur_freq
# Beklenen Çıktı: 1000000000

# NPU 3 Çekirdek Telemetrisi:
sudo cat /sys/kernel/debug/rknpu/load
# Beklenen Çıktı: Core0, Core1, Core2 hazır durumdadır.
```

---

## **7. Doğrulama Özet Tablosu**

| Alt Sistem / Metrik | Test Edilen Bileşen | Referans Değer | Kararlılık Kriteri |
| :--- | :--- | :--- | :--- |
| **CPU Prime Gücü** | RK3588S (8 Çekirdek) | **5.342 ev/s** | > 5.000 ev/s (Sıfır kayıp) |
| **A76 Sıcaklık (Yük Altında)** | Cortex-A76 | **76.7 °C** | < 80 °C (Throttling yok) |
| **A76 Tepe Saat Hızı** | 4x A76 Çekirdeği | **2352 MHz** | 2304–2352 MHz sabit |
| **RAM Bant Genişliği** | LPDDR4x/5 @ 2.112 GHz | **~25.2 GB/s** | > 24 GB/s |
| **NVMe Sıralı Okuma** | PCIe 2.0 x1 M.2 Yuvası | **418 MB/s** | 400–425 MB/s (Hat doyumu) |
| **NVMe 4K IOPS** | 4K Rastgele Okuma | **90.900 IOPS** | Yüksek I/O tepkiselliği |
| **NPU Saat Hızı** | 3x NPU Çekirdeği | **1.000 MHz** | 1.0 GHz hazır |

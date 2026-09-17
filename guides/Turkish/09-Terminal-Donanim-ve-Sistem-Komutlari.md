# **Orange Pi 5 (RK3588S) Terminal Donanım, Sensör ve Sistem Yönetim Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** Bu rehberdeki tüm komutlar ve dosya yolları fiziksel **Orange Pi 5 (Rockchip RK3588S) + Ubuntu 24.04 / 22.04 LTS (Kernel 6.1 BSP)** üzerinde bizzat test edilip doğrulanmıştır.

Bu el kitabı, Orange Pi 5 üzerinde terminalden sıcaklık okuma, fan yönetimi, CPU frekans ayarları, 6 TOPS NPU teşhisi, bellek optimizasyonu ve kamera denetimini en doğru yöntemlerle gerçekleştirmek için hazırlanmıştır.

---

## 🚫 **ÖNEMLİ: Yasaklı Komutlar (Raspberry Pi vs Orange Pi 5)**

Yapay zeka modelleri ve internet forumları sıklıkla Orange Pi ile Raspberry Pi'yi karıştırır. Aşağıdaki komutlar **Orange Pi 5'te KESİNLİKLE ÇALIŞMAZ**:

| Hatalı / Yasak Komut | Neden Çalışmaz? | Orange Pi 5 (RK3588) Gerçek Karşılığı |
|:---|:---|:---|
| `vcgencmd measure_temp` | Sadece Raspberry Pi Broadcom VideoCore GPU'ya özeldir. | `paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) \| awk '{printf "%-20s: %.1f °C\n", $1, $2/1000}'` veya `sensors` |
| `raspi-config` | Raspberry Pi yapılandırma aracıdır. | `sudo orangepi-config` |
| `rpi.gpio` (Python) | Raspberry Pi BCM registerlarına özeldir. | `gpiod` (`python3-libgpiod`) veya `periphery` |
| `/boot/config.txt` | Raspberry Pi bootloader dosyasıdır. | `/boot/orangepiEnv.txt` veya `/boot/armbianEnv.txt` |

---

## 🌡️ **1. Sıcaklık ve Termal Sensörleri Okuma**

Rockchip RK3588S işlemcisi üzerinde **7 bağımsız termal sensör (thermal zone)** bulunur:
- `soc-thermal`: Çip çevresi / silikon periferi sensörü (`btop` genelde bunu okur).
- `bigcore0-thermal`: Cortex-A76 Büyük Çekirdek 0-1 (LLM yükünde ilk ısınan çekirdek).
- `bigcore1-thermal`: Cortex-A76 Büyük Çekirdek 2-3.
- `littlecore-thermal`: Cortex-A55 Enerji Tasarruf Çekirdekleri 0-3.
- `center-thermal`: Çip silikon merkezi.
- `gpu-thermal`: Mali-G610 MP4 Grafik Birimi.
- `npu-thermal`: 6 TOPS NPU Hızlandırıcı.

### **Yöntem 1: Tüm 7 Sensörü Tek Seferde Listeleme (En Temiz)**
Hiçbir ek paket kurmadan doğrudan Linux kernelinden okur:
```bash
paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp) | awk '{printf "%-22s: %.1f °C\n", $1, $2/1000}'
```

### **Yöntem 2: `sensors` (lm-sensors)**
```bash
sensors
```
Kernel 6.1 BSP sürücüsü tüm sensörleri `hwmon` aygıtı olarak doğrudan `sensors` çıktısına yansıtır.

### **Yöntem 3: Canlı Terminal Monitörü (`btop`)**
```bash
btop
```
CPU kutusunda frekans, sıcaklık ve çekirdek yüklerini grafik olarak izler.

---

## 💨 **2. Fan Kontrolü ve Soğutma Yönetimi**

Orange Pi 5 üzerindeki aktif PWM fan soğutma noktaları kernel thermal governor tarafından yönetilir.

### **Mevcut Fan Hızını Görme:**
```bash
cat /sys/class/thermal/cooling_device0/cur_state
```
*(Değerler: `0` = Kapalı, `1` = Düşük Hız, `2` = Orta Hız, `3` = %100 Tam Hız).*

### **Fan Hızını Manuel Olarak Maksimuma Sabitleme:**
```bash
echo 3 | sudo tee /sys/class/thermal/cooling_device0/cur_state
```

---

## ⚡ **3. CPU Frekansı ve Performans Governor Yönetimi**

RK3588S 8 çekirdeklidir:
- **Çekirdek 0-3 (Cortex-A55):** `policy0` (Azami 1.8 GHz)
- **Çekirdek 4-5 (Cortex-A76):** `policy4` (Azami 2.4 GHz)
- **Çekirdek 6-7 (Cortex-A76):** `policy6` (Azami 2.4 GHz)

### **Canlı Çekirdek Frekanslarını Görme:**
```bash
cat /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq
```

### **Tüm Çekirdekleri Performans Moduna Sabitleme (En Yüksek Hız):**
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### **Dinamik Enerji Tasarrufuna Geri Döndürme:**
```bash
echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

---

## 🧠 **4. NPU (6 TOPS) Teşhis ve Doğrulama**

### **NPU Aygıt Düğümünü ve İzinlerini Kontrol Etme:**
```bash
ls -l /dev/dri/renderD129
```
*Beklenen Çıktı:* `crw-rw----+ 1 root render ... /dev/dri/renderD129`

### **NPU İzinlerini Onarma (Erişim Hatası Alıyorsa):**
```bash
sudo usermod -aG video,render $USER && sudo chmod 666 /dev/dri/renderD129
```

### **Canlı NPU Yükünü İzleme:**
NPU çalışırken (örneğin YOLOv8 veya ESPCN çalışırken) 3 çekirdeğin yükünü canlı gösterir:
```bash
cat /sys/kernel/debug/rknpu/load
```

---

## 🧹 **5. Bellek (RAM) ve NVMe Swap Optimizasyonu**

### **Bellek Durumunu Görme:**
```bash
free -h
```

### **Linux RAM Önbelleğini Güvenle Boşaltma:**
```bash
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

---

## 📷 **6. Kamera ve Video Cihazları (V4L2)**

### **Bağlı Kameraları Listeleme:**
```bash
v4l2-ctl --list-devices
```

### **Kameranın Desteklediği Çözünürlük ve FPS Değerlerini Listeleme:**
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

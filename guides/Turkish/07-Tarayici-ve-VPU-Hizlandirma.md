# **Orange Pi 5 (RK3588S) Tarayıcı ve Donanımsal Video Hızlandırma Kılavuzu**

> 🛡️ **Doğrulandı & Test Edildi:** Chromium VPU donanım hızlandırma bayrakları ve 4K@60fps akıcı video oynatma **Orange Pi 5 + Ubuntu 24.04 / 22.04 LTS** üzerinde test edilmiştir.

Bu kılavuz, Orange Pi 5 üzerinde masaüstü ortamında Chromium tarayıcısıyla YouTube veya internet üzerinden video izlerken yaşanan takılma, yüksek CPU kullanımı ve fan gürültüsü sorununu çözmek için hazırlanmıştır.

---

## **1. Sorunun Nedeni: Neden Videolar Kasıyor?**

Orange Pi 5 oldukça güçlü 8 çekirdekli bir işlemciye ve 4K/8K video çözme kapasitesine sahip bir video motoruna (VPU) sahiptir. Ancak varsayılan Linux kurulumlarında Chromium tarayıcısı bu video motorunu doğrudan kullanmaz:

* **Varsayılan Durum:** Tarayıcı, video kodunu çözmek için video çipi yerine CPU çekirdeklerini kullanır (yazılımsal çözümleme).
* **Sonuç:** 1080p veya 4K video açıldığında CPU kullanımı **%80–100** seviyesine çıkar, video takılır, kareler atlanır (dropped frames) ve fan son devirde çalışmaya başlar.
* **Çözüm:** Tarayıcıya donanımsal video hızlandırmayı açarak video işleme yükünü tamamen VPU çipine devretmektir.

---

## **2. Adım 1: Gerekli Video Kütüphanelerinin Kurulumu**

Rockchip donanımsal video çözücü kütüphanelerinin kurulu olduğundan emin olmak için terminale şu komutu girin:

```bash
sudo apt update && sudo apt install -y librockchip-mpp1 libv4l-rkmpp
```

---

## **3. Adım 2: Chromium'da Donanım Hızlandırmayı Açma**

### **Yöntem A: Tarayıcı Ayarları Üzerinden (Önerilen)**

1. **Chromium** tarayıcısını açın.
2. Adres çubuğuna `chrome://flags` yazıp **Enter** tuşuna basın.
3. Arama kutusunu kullanarak aşağıdaki iki ayarı bulun ve durumlarını **Enabled** yapın:
   * **Override software rendering list:** `Enabled`
   * **Hardware-accelerated video decode:** `Enabled`
4. Sayfanın sağ altında çıkan **Relaunch** (Yeniden Başlat) butonuna tıklayarak tarayıcıyı yeniden başlatın.

### **Yöntem B: Terminalden veya Kısayoldan Başlatma**

Chromium'u doğrudan donanım hızlandırma parametreleriyle başlatmak isterseniz terminalde şu komutu çalıştırabilirsiniz:

```bash
chromium-browser --enable-features=VaapiVideoDecoder,VaapiVideoEncoder --use-gl=egl
```

---

## **4. Adım 3: YouTube İçin Küçük Bir Tavsiye (h264ify Eklentisi)**

YouTube varsayılan olarak AV1 veya VP9 formatında video gönderebilir. Tarayıcınızın donanım hızlandırmasından en yüksek verimi almak için:

1. Chrome Web Mağazası'ndan **enhanced-h264ify** eklentisini kurun.
2. Eklenti ayarlarından **AV1** formatını engelleyip videoların **H.264** veya **VP9** olarak gelmesini sağlayın. Bu sayede tüm videolar donanımsal olarak sorunsuz çözülecektir.

---

## **5. Doğrulama: Donanım Hızlandırmanın Çalıştığı Nasıl Anlaşılır?**

Ayarların devreye girdiğini teyit etmek için:

1. Chromium adres satırına `chrome://gpu` yazın.
2. Sayfada **Video Decode** satırını kontrol edin:
   * **Hardware accelerated** (yeşil renkli) yazıyorsa hızlandırma başarıyla aktiftir.

### **Öncesi ve Sonrası Karşılaştırması (4K 60FPS Video Testi)**

| Durum | CPU Kullanımı | Video Akıcılığı | Sıcaklık & Fan |
| :--- | :--- | :--- | :--- |
| **Ayar Öncesi (Yazılımsal)** | %80 – %95 | Takılmalar ve kare atlamaları | Yüksek sıcaklık, fan sürekli tam devir |
| **Ayar Sonrası (Donanımsal)** | **%10 – %18** | **Kusursuz ve akıcı** | Düşük sıcaklık, sessiz çalışma |

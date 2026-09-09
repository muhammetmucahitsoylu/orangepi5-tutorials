# **Orange Pi 5 (RK3588S) Kurtarma ve Kurulum Kılavuzu**

> 🛡️ **Doğrulandı & Test Edildi:** Bu rehberdeki kurtarma ve kurulum adımları **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS** üzerinde fiziksel donanım, SPI Flash ve MaskROM modunda test edilmiş ve onaylanmıştır.

*Bu kılavuz, Orange Pi 5 kartına EDK2 UEFI BIOS kurup cihazı boot döngüsüne soktuktan, çalışan sistemden SSD klonlama hatalarıyla saatler kaybettikten ve SPI Flash çipini boşaltıp kartı kilitledikten sonra deneme-yanılma ve teknik analizlerle çözüme ulaştığım süreci adım adım belgelemektedir. İnternetteki dağınık ve eksik anlatımların aksine, sıfırdan başlayanların aynı tuzaklara düşmemesi için tüm adımları ve teknik nedenleri derledim. Not: Bu sorunu Mobile HDD ile yaşadım MicroSD kart kullanılmamıştır.* 

## **1\. Giriş ve Temel Sorun Özeti**

Orange Pi 5 (RK3588S) kartımı yaptığım klonlamalar sonucunda NVMe SSD üzerinden çalıştıramadığım için NVMe SSD ile boot etme amacıyla anakart üzerindeki SPI Flash çipine EDK2 UEFI BIOS yükledim. Hedefim cihazı NVMe ile boot denemelerim başarısız olduktan sonra araştırmalarım sonucu birkaç kullanıcının da önerisiyle UEFI .iso formatında M.2 NVMe SSD üzerinden çalıştırmaktı. Ancak bu işlem; tanınmayan diskler, sürekli ağdan önyükleme (PXE loop) döngüleri ve donanımsal kilitlenmelerle sonuçlandı.  
Yaşadığım tüm kilitlenmelerin ardından çıkardığım en net sonuç şudur: Orange Pi 5 için EDK2 UEFI BIOS tamamen gereksiz bir maceradır. Kartın tam donanım desteğiyle, NPU/GPU hızlandırmasıyla ve en yüksek kararlılıkla çalışmasının tek yolu anakartta resmi Rockchip U-Boot bulundurmak ve işletim sistemini doğrudan bilgisayar üzerinden M.2 NVMe SSD'ye ham imaj (.img) olarak yazdırmaktır.

## **2\. Süreç Boyunca Düşülen 5 Kritik Tuzak ve Teknik Nedenleri**

### **Tuzak 1: EDK2 UEFI BIOS'a Klasik .img İmajı Başlattırmaya Çalışmak**

**Yaşanan Sorun:** GitHub üzerinden doğrudan indirdiğim loader dosyalarıyla RKDevTool'da sürekli Download Boot Fail ve iletişim hataları aldım.  
**Teknik Nedeni:** EDK2 UEFI BIOS, standart bir PC mantığında çalışır ve diskte mutlaka bir EFI Sistem Bölümü (ESP) ile \\EFI\\BOOT\\BOOTAA64.EFI dosyası arar. Tek kart bilgisayarlar için derlenen ham .img dosyaları ise klasik U-Boot mimarisine göre hazırlandığından bu bölüme sahip değildir.

### **Tuzak 2: Çalışan Canlı Sistem Üzerinden SSD Klonlamaya Çalışmak**

**Yaşanan Sorun:** Sistemi harici bir diskten geçici olarak açıp çalışan Linux içerisinden dd veya klonlama araçlarıyla NVMe SSD'ye kopyaladım; ancak SSD'den açılış kilitlendi.  
**Teknik Nedeni:** Canlı çalışan bir Linux ortamından kök dizin klonlandığında GPT bölümleri, UUID eşleşmeleri ve açılış sektörleri bozulur.  
**Nasıl Çözdüm?** Klonlama işi tamamen sakat çıktı ve çalışmadı; M.2 NVMe SSD'yi Orange Pi 5'e takılı bırakıp resmi .img dosyasını laptopumun terminalinden doğrudan SSH ağ akışı (stream dd) ile SSD'ye sıfırdan yazdırdım ve sorunsuz açıldı.

### **Tuzak 3: SPI Flash'ı Sıfırlayıp "Boş" Bırakmak (En Büyük Kilitlenme)**

**Yaşanan Sorun:** Server Linux sistemini .iso olarak depolama aygıtıma kurdum ve Ubuntu Server HWE kernel seçeneğiyle sistemi açıp terminale geçtim. Çipi sıfırlayan komut mtd-utils paketi içindeki donanımsal blok silici olan flash\_erase /dev/mtd0 0 0 komutuydu. Ancak hemen ardından U-Boot yüklemeyi unuttuğum için cihazı yeniden başlattığımda yeşil durum LED'i hiç yanmadı ve kart diski görmeyerek tamamen tepkisiz kaldı.  
**Teknik Nedeni:** Rockchip RK3588'in dahili MaskROM kodu yalnızca MicroSD kart ve eMMC kontrolcüsünü uyandırabilir. PCIe (M.2 NVMe) veya USB 3.0 kontrolcülerini başlatacak donanım kodları SPI Flash içindeki U-Boot'ta yer alır. SPI çipi boş kalınca kart M.2 hattına veri yolu sağlayamadı.

### **Tuzak 4: Dosya Kalabalığı ve Güvenilirlik**

**Yaşanan Sorun:** GitHub üzerinden doğrudan indirdiğim loader dosyalarıyla RKDevTool'da sürekli Download Boot Fail ve iletişim hataları aldım.  
**Nasıl Çözdüm?** Orange Pi 5 kaynaklarında bulduğum Google Drive klasöründeki doğrulanmış tam binary dosyaları (MiniLoaderAll.bin, rkspi\_loader.img ve resmi .cfg dosyası) herhangi bir sorun çıkartmadan çalıştı.

### **Tuzak 5: Windows Sürücü Çakışmaları ve Port Problemleri**

**Yaşanan Sorun:** RKDevTool kartı algılamadı veya işlem ortasında koptu.  
**Teknik Nedeni:** Windows üzerinde birden fazla driver kurulmuştu; bu yüzden çakışma yaşanıyordu. Hepsini terminalden pnputil ile kaldırıp DriverAssistant\_v5.12 uygulamasındakini sıfırdan kurdum. Böylelikle RKDevTool\_Release\_v3.15 kartı sorunsuz bir şekilde MASKROM olarak algılayabildi.

## **3\. Gerekli Araçlar ve Doğrulanmış Dosyalar**

| Bileşen / Dosya Adı | Görevi | Kritik Detay   |
| :---- | :---- | :---- |
| DriverAssistant\_v5.12 | Rockchip sürücü yükleme ve temizleme aracı | Windows çakışmalarını önlemek için temiz kurulum sağlar |
| RKDevTool (v3.15) | SPI Flash bellek yazma ve sıfırlama yazılımı | MaskROM modunda donanım seviyesinde işlem yapar |
| MiniLoaderAll.bin | İşlemcinin RAM ve bellek kontrolcüsünü uyandırır | Boyutu \~200-500 KB olmalıdır  |
| rk3588\_linux\_spiflash.cfg | Resmi SPI Flash adresleme yapılandırması | Dosya adreslerini elle girmek yerine otomatik ve hatasız yükler |
| rkspi\_loader.img | Resmi Rockchip SPI U-Boot imajı | M.2 PCIe (NVMe) ve USB hatlarını açılışta başlatır |
| **Geçici Depolama Aygıtı \+ Ağ (SSH) Bağlantısı** | SSD'yi sökmeden doğrudan karta ham imaj akıtma köprüsü | Canlı sistem klonlama bozulmalarını ve donanım sökme ihtiyacını tamamen ortadan kaldırır |
| Ubuntu 24.04 ARM64 (.img) | Orange Pi 5 uyumlu resmi Linux dağıtımı | Laptop üzerinden SSH ağ akışıyla doğrudan blok seviyesinde yazdırılır |

---

## **4. Adım Adım Kesin Çözüm Protokolü**

### **Aşama 1: NVMe SSD'yi Sökmeden Laptop Üzerinden Ağ ile Yazdırın**

1. **\[UYARI\]** M.2 NVMe SSD'yi Orange Pi 5'in altındaki M.2 yuvasına takıp sabitleme vidasını sıkın (karttan sökmenize gerek yoktur).  
> 2. Herhangi bir depolama aygıtına geçici bir Linux dağıtımı (Armbian, Ubuntu vb.) yazdırıp Orange Pi 5'e takın ve kartı başlatın.  
3. Orange Pi 5 ve laptopunuzun aynı yerel ağda (Wi-Fi veya Ethernet) olduğundan emin olun. Orange Pi 5 terminalinde SSD aygıt adını doğrulayın:  
   lsblk *(M.2 SSD genellikle /dev/nvme0n1 olarak listelenir.)*  
4. Laptopunuzda terminali açıp resmi ubuntu-24.04-preinstalled-desktop-arm64-orangepi-5.img dosyasının bulunduğu dizine gidin ve işletim sisteminize uygun komutla imajı doğrudan SSD'ye (/dev/nvme0n1) aktarın:  
   **Windows (CMD \- Komut İstemi):**  
   type ubuntu-24.04-preinstalled-desktop-arm64-orangepi-5.img | ssh root@ORANGE\_PI\_IP "dd of=/dev/nvme0n1 bs=4M status=progress conv=fsync"  
   **Windows (PowerShell 7+):**  
   Get-Content .\\ubuntu-24.04-preinstalled-desktop-arm64-orangepi-5.img \-AsByteStream \-Raw | ssh root@ORANGE\_PI\_IP "dd of=/dev/nvme0n1 bs=4M status=progress conv=fsync"  
> 5. Yazma işlemi bittiğinde Orange Pi 5'i kapatın (poweroff) ve geçici olarak kullandığınız **Depolama aygıtını çıkartın**.

### **Aşama 2: Windows Sürücü Çakışmalarını Temizleyin**

> 1. Windows Komut İstemi'ni (CMD) **Yönetici Olarak** çalıştırın.  
2. Eski çakışan sürücü paketlerini tamamen kaldırın:  
   pnputil /delete-driver oem\*.inf /uninstall /force  
3. DriverAssistant\_v5.12 klasöründen DriverInstall.exe uygulamasını çalıştırıp **Install Driver** seçeneğiyle temiz sürücüyü kurun.

### **Aşama 3: Kartı Donanımsal MaskROM Moduna Alın**

1. **[UYARI]** Orange Pi 5'in Power In (DC-IN) Type-C portuna orijinal 5V/4A şarj adaptörünü bağlayın.  
2. **[UYARI]** Bilgisayarınızın USB 3.0 çıkışını ise Orange Pi 5'in diğer Type-C (OTG) portuna takın.  
3. **Zorunlu MaskROM Tetikleme Prosedürü:**  
   * Eğer SPI Flash tamamen silinmişse, kart açılışta bootloader bulamadığı için **otomatik** olarak MaskROM moduna düşer.
   * **Kritik Durum (SPI Flash Bozuk/Döngüde Kilitli İse):** Kart otomatik MaskROM'a geçmezse; gücü tamamen kesin. Kartın üzerindeki **MaskROM butonuna** (RK3588S SoC'un sağında, MicroSD yuvası yakınında yer alan minik buton) basılı tutun. Butonu bırakmadan PC'ye bağlı Type-C OTG kablosunu takın, 3 saniye bekleyip butonu bırakın. *(Rev V1.1/V1.2 kartlarda buton 'BOOT' veya 'MaskROM' olarak etiketlidir; V1.3.2'de lehim butonudur).*
4. RKDevTool programını açın; pencerenin en altında **Found One MASKROM Device** yazısını doğrulayın.

### **Aşama 4: RKDevTool ile SPI Flash Onarımı ve U-Boot Flaşlama**

**1\. Adım: Loader Dosyasını Gönderme**

> * RKDevTool penceresinde üstteki **Advanced Function** (Gelişmiş Fonksiyonlar) sekmesine geçin.  
* En üstteki **Boot:** satırının sağındaki **...** butonuna basarak klasördeki MiniLoaderAll.bin dosyasını seçin.  
> * Altındaki **Download** (veya DownloadBoot) butonuna basın.  
* Sağdaki log ekranında mavi renkle Download Boot OK çıktısını görün.

**2\. Adım: SPI Belleğe Geçiş (Switch Storage)**

> * Aynı ekranda sağ taraftaki depolama listesinden **SPINOR** (veya SPI) seçeneğini seçin.  
> * **Switch Storage** butonuna tıklayın.  
> * Sağdaki log ekranında depolama türünün SPINOR moduna geçtiğini teyit edin.

**3\. Adım: Resmi Bootloader'ı SPI'a Yazma (Asıl Çözüm)**

> * RKDevTool'un ilk sekmesi olan **Download Image** sekmesine geçin.  
> * Tablodaki satırların bulunduğu boş bir yere sağ tıklayın ve **Import Configuration** (Yapılandırmayı İçe Aktar) seçeneğini seçin.  
* Klasörünüzdeki rk3588\_linux\_spiflash.cfg dosyasını seçip **Aç** butonuna tıklayın.  
> * Tablo otomatik olarak resmi adreslerle güncellenecektir:  
  * En alttaki **Loader** kısmında MiniLoaderAll.bin seçili olmalıdır.  
  * Tablodaki ilgili satırda rkspi\_loader.img seçili, Address kısmında 0x00000000 ve başındaki kutucuk işaretli olmalıdır.  
> * En alttaki **Write by Address** seçeneğinin işaretli olduğundan emin olun.  
> * **Run** butonuna basın.  
* Sağ panelde Download Image OK yazısını gördüğünüzde işlem tamamdır.

### **Aşama 5: Sistemi NVMe SSD ile Başlatma ve Doğrulama**

> 1. Bilgisayara bağlı olan Type-C kablosunu çekin.  
> 2. Aşama 1'de hazırlandığı üzere önceki depolama aygıtının çıkarılmış ve NVMe SSD nin takılı olduğunu teyit edin.  
> 3. Orijinal Type-C güç adaptörünü ve HDMI kablosunu bağlayın.  
> 4. Kart açıldığında SPI çipindeki resmi U-Boot doğrudan PCIe hattını tetikler, NVMe SSD yi bulur, yeşil durum LED'i düzenli yanıp sönmeye başlar ve doğrudan Ubuntu masaüstü/giriş ekranı açılır.  
5. Terminal açıldığında kök dizinin NVMe üzerinde çalıştığı şu komutla doğrulanır:  
   findmnt /  
   **Doğrulama Çıktısı:** TARGET: / \-\> SOURCE: /dev/nvme0n1p1

## **5\. Hızlı Sorun Giderme Tablosu**

| Belirti / Hata | Temel Neden | Uygulanan Kesin Çözüm   |
| :---- | :---- | :---- |
| **Klonlanan SSD Açılmıyor / Kilitleniyor** | Canlı sistemden kopyalama sırasında GPT/UUID tablolarının bozulması | M.2 SSD karta takılıyken laptop terminalinden SSH ağ akışı (dd) ile ham .img olarak sıfırdan yazdırıldı |
| **RKDevTool Download Boot Fail Hatası** | Uyumsuz Git kaynaklı loader dosyası kullanımı | Doğrulanmış gerçek (\~300 KB) binary MiniLoaderAll.bin dosyası kullanıldı |
| **MaskROM Aygıtı Görünmüyor** |  Windows sürücü çakışması | pnputil ile eski sürücüler temizlendi, DriverAssistant\_v5.12 ile tek sürücü kuruldu |
| **Yeşil LED Hiç Yanmıyor / Tepki Yok** | flash\_erase ile SPI Flash silindi ama U-Boot yazılmadı (PCIe başlatılamadı) | MaskROM modunda SPINOR seçilip rk3588\_linux\_spiflash.cfg ile rkspi\_loader.img flaşlandı |
| **Sistem BIOS / PXE Ekranına Düşüyor** | Anakartta EDK2 UEFI kaldı ve diskte EFI arıyor | SPI Flash'taki UEFI silinip resmi Rockchip U-Boot mimarisine dönüldü |

## **6\. Sonuç ve Önemli Çıkarımlar**

Orange Pi 5 üzerinde harici USB disklerle uğraşmak veya EDK2 UEFI kurmaya çalışmak stabiliteyi bozan gereksiz adımlardır. En yüksek performanslı, kararlı ve sorunsuz yapılandırma:

> * Anakart SPI Flash üzerinde resmi Rockchip U-Boot barındırmak,  
> * İşletim sistemini laptop üzerinden SSH ağ akışıyla doğrudan Orange Pi 5 üzerindeki M.2 NVMe SSD'ye ham .img olarak yazdırmak,  
> * Canlı klonlama ve UEFI arayüzü gibi kararsız yöntemlerden tamamen uzak durmaktır.
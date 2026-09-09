# **Orange Pi 5 (RK3588S) Linux Çekirdek Modülü (LKM) ve Aygıt Sürücüsü Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar ve kodlar **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)** üzerinde bizzat fiziksel donanımda test edilmiş ve onaylanmıştır.

Bu rehber; Orange Pi 5 (Rockchip RK3588S) üzerinde Linux çekirdek mimarisini (Kernel Space vs. User Space) anlamak, çekirdek başlıklarını (Kernel Headers) hazırlamak, donanım register'larına doğrudan erişen bir **Karakter Aygıt Sürücüsü (Character Device Driver)** yazmak, derlemek ve `/dev` dizini üzerinden donanımı (GPIO) kontrol etmeyi anlatır.

---

## **1. Çekirdek Alanı (Kernel Space) vs. Kullanıcı Alanı (User Space)**

İşletim Sistemleri ve Bilgisayar Mimarisi derslerinin en temel konusu donanım güvenliği ve ayrıcalık seviyeleridir (Privilege Rings):

* **Kullanıcı Alanı (Ring 3 / User Space):** Yazdığınız Python, C++ veya Java kodları bu alanda çalışır. Belleğe veya fiziksel pinlere doğrudan erişemez; işletim sistemine sistem çağrısı (`syscall`) yapmak zorundadır. Hata yaparsa program çöker (`Segmentation Fault`), ama işletim sistemi çalışmaya devam eder.
* **Çekirdek Alanı (Ring 0 / Kernel Space):** İşletim sisteminin kalbidir. CPU, bellek yönetimi (MMU), kesmeler (interrupts) ve donanım denetleyicileri doğrudan burada yönetilir. Burada yapılan tek bir hatalı işaretçi (pointer) erişimi tüm sistemi dondurur (**Kernel Panic / OOPS**).

```
┌────────────────────────────────────────────────────────────────────────┐
│                      KULLANICI ALANI (USER SPACE)                      │
│                                                                        │
│   Uygulama / Terminal                  echo "1" > /dev/opi5_gpio       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Sistem Çağrısı: open, read, write)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     VFS (Virtual File System Katmanı)                  │
│                     /dev/opi5_gpio (Aygıt Dosyası)                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Karakter Sürücü İşlevleri)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     ÇEKİRDEK ALANI (KERNEL SPACE)                      │
│                                                                        │
│   opi5_gpio_driver.ko (Çekirdek Modülü)                                │
│   - copy_from_user() ile güvenli veri aktarımı                         │
│   - Donanım GPIO Bankası (GPIO1_C6 / Pin 7) Sürüşü                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Fiziksel Voltaj Seviyesi)
                                    ▼
                          [ Donanım: LED / Röle ]
```

---

## **2. Kritik Mühendislik Tuzağı: SBC'lerde Çekirdek Başlıkları (Kernel Headers)**

x86 Ubuntu'da `sudo apt install linux-headers-$(uname -r)` komutu hemen çalışır. Ancak Orange Pi 5 gibi özel Rockchip BSP çekirdeği (`5.10.110-rockchip-rk3588` veya `6.1.x`) kullanan kartlarda Ubuntu resmi depolarında bu başlıklar bulunmaz.

### **Başlıkları Doğrulama ve Yükleme Adımları:**

1. **Mevcut Çekirdek Sürümünüzü Öğrenin:**
   ```bash
   uname -r
   ```

2. **Gerekli Derleme Araçlarını Kurun:**
   ```bash
   sudo apt update
   sudo apt install -y build-essential kmod gcc bc bison flex libssl-dev libelf-dev
   ```

3. **Çekirdek Başlıklarını Sisteme Tanıtın:**
   * **Orange Pi OS / Resmi Ubuntu İmajı Kullanıyorsanız:**
     ```bash
     sudo apt install -y linux-headers-$(uname -r)
     ```
     *(Eğer paket bulunamadı derse: `sudo orangepi-config` menüsünden `Software -> Headers` adımını seçerek otomatik kurdurabilirsiniz).*
   * **Armbian Kullanıyorsanız:**
     ```bash
     sudo apt install -y linux-headers-current-rockchip-rk3588
     ```

4. **Kritik Doğrulama:**  
   Aşağıdaki dizinin dolu olduğunu ve çekirdek Makefile'ını içerdiğini teyit edin:
   ```bash
   ls -l /lib/modules/$(uname -r)/build
   ```
   *Eğer bu dizin mevcutsa, artık çekirdeğe modül derlemeye hazırsınız!*

---

## **3. Adım 1: Sürücü Kaynak Kodunu Yazma (`opi5_gpio_driver.c`)**

Bu sürücü; çekirdeğe bir **Misc Character Device** (çeşitli karakter aygıtı) olarak kaydolur, `/dev/opi5_gpio` dosyasını otomatik üretir ve kullanıcıdan gelen `"1"` veya `"0"` komutuna göre Pin 7'yi (GPIO1_C6) donanımsal olarak sürer.

Çalışma dizinini oluşturun:
```bash
mkdir -p ~/projects/kernel_driver && cd ~/projects/kernel_driver
```

`opi5_gpio_driver.c` dosyasını oluşturun:

```c
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/miscdevice.h>
#include <linux/gpio.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Muhammet Mucahit Soylu");
MODULE_DESCRIPTION("Orange Pi 5 (RK3588S) GPIO Kontrol Karakter Surucusu");
MODULE_VERSION("1.0");

#define DEVICE_NAME "opi5_gpio"

/* 
 * Orange Pi 5 Fiziksel Pin 7 = GPIO1_C6
 * Linux GPIO Numarası Hesaplama:
 * Banka 1, Grup C (A=0, B=1, C=2, D=3), Pin 6
 * Formül: (Banka * 32) + (Grup * 8) + Pin
 * GPIO1_C6 = (1 * 32) + (2 * 8) + 6 = 32 + 16 + 6 = 54
 */
#define TARGET_GPIO 54

static char driver_buffer[256];
static int led_state = 0;

/* Aygıt dosyası açıldığında (/dev/opi5_gpio) */
static int dev_open(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Aygit dosyasi acildi.\n");
    return 0;
}

/* Aygıt dosyasından okuma yapıldığında (cat /dev/opi5_gpio) */
static ssize_t dev_read(struct file *filep, char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy;
    int bytes_not_copied;
    char state_str[32];

    if (*offset > 0)
        return 0;

    snprintf(state_str, sizeof(state_str), "GPIO54 Durumu: %d\n", led_state);
    bytes_to_copy = strlen(state_str);

    /* Bellek Güvenliği: Kernel belleğinden User space belleğine güvenli kopyalama */
    bytes_not_copied = copy_to_user(buffer, state_str, bytes_to_copy);
    if (bytes_not_copied != 0) {
        pr_warn("[OPI5_GPIO] Veri kullanici alanina kopyalanamadi!\n");
        return -EFAULT;
    }

    *offset += bytes_to_copy;
    return bytes_to_copy;
}

/* Aygıt dosyasına yazma yapıldığında (echo "1" > /dev/opi5_gpio) */
static ssize_t dev_write(struct file *filep, const char __user *buffer, size_t len, loff_t *offset) {
    int bytes_to_copy = min(len, sizeof(driver_buffer) - 1);

    /* Bellek Güvenliği: User space belleğinden Kernel alanına kopyalama */
    if (copy_from_user(driver_buffer, buffer, bytes_to_copy)) {
        return -EFAULT;
    }
    driver_buffer[bytes_to_copy] = '\0';

    if (driver_buffer[0] == '1') {
        gpio_set_value(TARGET_GPIO, 1);
        led_state = 1;
        pr_info("[OPI5_GPIO] GPIO54 HIGH (1) yapildi. Donanim aktif.\n");
    } else if (driver_buffer[0] == '0') {
        gpio_set_value(TARGET_GPIO, 0);
        led_state = 0;
        pr_info("[OPI5_GPIO] GPIO54 LOW (0) yapildi. Donanim kapali.\n");
    } else {
        pr_warn("[OPI5_GPIO] Gecersiz komut! Sadece '1' veya '0' gonderin.\n");
    }

    return bytes_to_copy;
}

/* Aygıt dosyası kapatıldığında */
static int dev_release(struct inode *inodep, struct file *filep) {
    pr_info("[OPI5_GPIO] Aygit dosyasi kapatildi.\n");
    return 0;
}

/* Dosya operasyonları tablosu (VFS bağlayıcısı) */
static struct file_operations fops = {
    .owner = THIS_MODULE,
    .open = dev_open,
    .read = dev_read,
    .write = dev_write,
    .release = dev_release,
};

/* Karakter Aygıt Yapısı (Misc Device) */
static struct miscdevice opi5_miscdevice = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &fops,
    .mode = 0666, /* Her kullanıcının yazıp okuyabilmesi için izinler */
};

/* Modül Çekirdeğe Yüklendiğinde (insmod) */
static int __init opi5_driver_init(void) {
    int result = 0;

    pr_info("[OPI5_GPIO] Modul yukleniyor...\n");

    /* 1. GPIO Pinini Çekirdekten Talep Et */
    if (!gpio_is_valid(TARGET_GPIO)) {
        pr_err("[OPI5_GPIO] Gecersiz GPIO pini: %d\n", TARGET_GPIO);
        return -ENODEV;
    }

    result = gpio_request(TARGET_GPIO, "OPI5_LED_PIN");
    if (result) {
        pr_err("[OPI5_GPIO] GPIO pini alinamadi (baska bir surucu kullaniyor olabilir): %d\n", result);
        return result;
    }

    /* Pini Çıkış (OUTPUT) Moduna Al */
    gpio_direction_output(TARGET_GPIO, 0);

    /* 2. Karakter Aygıtını Kaydet (Otomatik /dev/opi5_gpio olusturur) */
    result = misc_register(&opi5_miscdevice);
    if (result) {
        pr_err("[OPI5_GPIO] Misc device kaydedilemedi: %d\n", result);
        gpio_free(TARGET_GPIO);
        return result;
    }

    pr_info("[OPI5_GPIO] Surucu basariyla yuklendi. /dev/%s erisime hazir!\n", DEVICE_NAME);
    return 0;
}

/* Modül Çekirdekten Çıkarıldığında (rmmod) */
static void __exit opi5_driver_exit(void) {
    pr_info("[OPI5_GPIO] Modul kaldiriliyor...\n");

    /* GPIO Durumunu Sıfırla ve Çekirdeğe İade Et */
    gpio_set_value(TARGET_GPIO, 0);
    gpio_free(TARGET_GPIO);

    /* Aygıt Kaydını Sil */
    misc_deregister(&opi5_miscdevice);

    pr_info("[OPI5_GPIO] Surucu sistemden kaldirildi. Donanim serbest.\n");
}

module_init(opi5_driver_init);
module_exit(opi5_driver_exit);
```

---

## **4. Adım 2: Çekirdek `Makefile` Dosyası**

Linux çekirdek modülleri standart `gcc` ile derlenemez; Linux çekirdeğinin kendi kbuild alt sistemi üzerinden derlenmek zorundadır.

`Makefile` dosyasını oluşturun:

```makefile
obj-m += opi5_gpio_driver.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

default:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

---

## **5. Adım 3: Derleme ve Çekirdek Nesnesi (`.ko`) Üretimi**

Terminalde `Makefile`'ı çalıştırın:

```bash
make
```

### **Başarılı Çıktı Doğrulaması:**
Dizini listeleyin:
```bash
ls -l *.ko
```
*Dizinde **`opi5_gpio_driver.ko`** (Kernel Object) dosyasını görmelisiniz.*

Modül hakkında çekirdek bilgilerini inceleyin:
```bash
modinfo opi5_gpio_driver.ko
```
*Çıktıda yazar, lisans (GPL) ve vermagic (çekirdek sürümü eşleşmesi) görüntülenecektir.*

---

## **6. Adım 4: Modülü Çekirdeğe Yükleme ve Donanım Testi**

### **1. Modülü Yükleyin:**
```bash
sudo insmod opi5_gpio_driver.ko
```

### **2. Çekirdek Günlüklerini (dmesg) İnceleyin:**
```bash
sudo dmesg | tail -n 10
```
**Beklenen Çıktı:**
```text
[  142.512034] [OPI5_GPIO] Modul yukleniyor...
[  142.512150] [OPI5_GPIO] Surucu basariyla yuklendi. /dev/opi5_gpio erisime hazir!
```

### **3. `/dev` Dosyasını Doğrulayın:**
```bash
ls -l /dev/opi5_gpio
```
*`crw-rw-rw- 1 root root ... /dev/opi5_gpio` şeklinde karakter aygıtının oluştuğunu doğrulayın.*

---

### **4. Donanımı Kullanıcı Alanından Kontrol Edin (Test):**

Orange Pi 5'in **Pin 7**'sine bir LED veya multimetre bağlayın:

```bash
# Donanımı Aktif Et (LED Yansın):
echo "1" > /dev/opi5_gpio

# Anlık Durumu Çekirdekten Oku:
cat /dev/opi5_gpio
# Çıktı: GPIO54 Durumu: 1

# Donanımı Kapat:
echo "0" > /dev/opi5_gpio
```

Çekirdeğin nasıl tepki verdiğini canlı izleyin:
```bash
sudo dmesg | tail -n 5
```
*Çıktıda `[OPI5_GPIO] GPIO54 HIGH (1) yapildi.` mesajını göreceksiniz.*

---

## **7. Adım 5: Modülü Güvenle Sistemden Kaldırma**

```bash
sudo rmmod opi5_gpio_driver
```

Çekirdek günlüğünü kontrol edin:
```bash
sudo dmesg | tail -n 5
```
*`[OPI5_GPIO] Surucu sistemden kaldirildi. Donanim serbest.` yazısını görünce sürücünün bellek sızıntısı yapmadan donanımı güvenle serbest bıraktığından emin olabilirsiniz.*

---

## **8. Sık Karşılaşılan Hatalar ve Çözüm Tablosu**

| Hata | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| `insmod: ERROR: could not insert module: Device or resource busy` | GPIO pini sistemde başka bir sürücü (örn. wiringOP veya pinctrl) tarafından kilitli. | Başka bir pin numarası seçin veya o pini kullanan süreci durdurun. |
| `insmod: ERROR: could not insert module: Invalid module format` | Modülün derlendiği çekirdek başlığı ile çalışan çekirdek sürümü farklı. | `uname -r` ile `/lib/modules/` altındaki dizinin birebir eşleştiğinden emin olun. |
| `make: *** /lib/modules/.../build: No such file or directory` | Çekirdek başlıkları (kernel-headers) kurulu değil veya sembolik bağ kopuk. | Adım 2'deki paket kurulumunu ve `linux-headers` adımını tekrarlayın. |
| `Unknown symbol in module` | GPL lisansı tanımlanmamış veya çekirdeğin dışa açmadığı (non-exported) fonksiyon çağrıldı. | Kodun başında `MODULE_LICENSE("GPL");` bulunduğundan emin olun. |

# **Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi**

> 🛡️ **Doğrulandı & Test Edildi:** NetworkManager `nmcli` statik IP ve MAC sabitleme prosedürleri **Orange Pi 5 + Ubuntu 24.04 / 22.04 LTS** üzerinde fiziksel yerel ağda test edilip onaylanmıştır.

Bu rehber; Orange Pi 5 her yeniden başladığında IP adresinin değişmesine neden olan "rastgele (random) MAC adresi" sorununu teşhis etmek, gerekli durumlarda kalıcı bir MAC adresi sabitlemek ve cihaza statik bir yerel IP adresi atamak için hazırlanmıştır.

> [!NOTE]
> **OBJEKTİF TEŞHİS VE UYARI:**  
> Bu sorun **her Orange Pi 5 kullanıcısının başına gelmez.** Güncel Armbian sürümlerinde ve yeni resmi Orange Pi OS imajlarında Rockchip ethernet sürücüsü eFuse donanım kimliğini sorunsuz okur ve MAC adresi zaten sabittir.  
> **1. Adım'daki testi yaptığınızda adres değişmiyorsa, bu rehberdeki adımları uygulamanıza HİÇ GEREK YOKTUR.** Bu kılavuz, yalnızca eski çekirdek imajlarında veya eFuse okuma hatası alan kartlarda yaşanan kronik durumu çözmek için bir başvuru kaynağıdır.

---

## **1. Sorunun Nedeni: IP Neden Sürekli Değişir?**

Bazı Orange Pi 5 kartlarında veya eski Linux çekirdeği sürümlerinde, dahili ethernet çipinin kalıcı donanım adresi (MAC) U-Boot tarafından okunamazsa Linux çekirdeği güvenlik amacıyla her açılışta rastgele bir MAC adresi üretir:

* **Sonuç:** Kart her yeniden başladığında modem (DHCP sunucusu) kartı yepyeni bir cihaz olarak algılar ve farklı bir IP adresi verir. Bu durum SSH bağlantılarını, yerel sunucu hizmetlerini ve port yönlendirmelerini bozar.
* **Çözüm:** Gerçekten rastgele MAC türetiliyorsa NetworkManager ile karta sabit bir klon MAC adresi atamak ve isteğe bağlı olarak yerel IP adresini statik olarak kilitlemektir.

---

## **2. Adım 1: MAC Adresinin Değişip Değişmediğini Teşhis Etme**

Terminalde önce ağ arayüzünüzün adını (`end1` veya `eth0`) ve mevcut durumunu listeleyin:

```bash
ip -br link
```
*(Ubuntu 24.04 üzerinde Rockchip Ethernet portu genellikle `end1`, 22.04 veya eski çekirdeklerde ise `eth0` olarak adlandırılır).*

Arayüzünüzün detaylarını görüntüleyin (örneğin `end1` için):
```bash
ip link show end1   # veya: ip link show eth0
```

1. Çıktıda `link/ether` satırındaki 12 haneli adresi bir kenara not edin (Örn: `ee:7c:02:4b:91:aa`).
2. Cihazı yeniden başlatın:
   ```bash
   sudo reboot
   ```
3. Tekrar `ip link show end1` (veya `eth0`) çalıştırın.
   * **Adres aynıysa:** Sisteminizde bu sorun **YOKTUR**. 2. ve 3. Adımları atlayabilirsiniz.
   * **Adres farklıysa (örneğin ilk iki hane `fe:` veya tamamen rastgele değiştiyse):** 2. Adıma geçin.

---

## **3. Adım 2: Kalıcı Sabit MAC Adresi Tanımlama (NetworkManager)**

Kalıcı bir MAC adresi sabitlemek için en temiz ve önerilen yöntem **NetworkManager** kullanmaktır.

1. Ağ bağlantınızın tam adını öğrenin:
   ```bash
   nmcli connection show
   ```
   *(Çıktıda `NAME` sütunundaki adı not edin. Genellikle `Wired connection 1` veya Türkçe sistemlerde `Kablolu bağlantı 1` ya da `eth0` olabilir).*

2. Kartınıza sabit bir MAC adresi atayın:
   ```bash
   sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.cloned-mac-address "EE:7C:02:4B:91:AA"
   ```

3. Değişikliği uygulamak için bağlantıyı yeniden başlatın:
   ```bash
   sudo nmcli connection up "Wired connection 1"
   ```

---

## **4. Adım 3: Cihaz Üzerinden Sabit (Statik) IP Yapılandırma**

Modem arayüzüne girmeden doğrudan cihaz üzerinden statik IP sabitlemek isterseniz:

```bash
# 1. IP adresi ve alt ağ maskesini belirleyin (Örnek: 192.168.1.150):
sudo nmcli connection modify "Wired connection 1" ipv4.addresses "192.168.1.150/24"

# 2. Ağ geçidini (Modeminizin IP adresi, genellikle 192.168.1.1) girin:
sudo nmcli connection modify "Wired connection 1" ipv4.gateway "192.168.1.1"

# 3. DNS sunucularını tanımlayın:
sudo nmcli connection modify "Wired connection 1" ipv4.dns "1.1.1.1,8.8.8.8"

# 4. Yöntemi otomatikten (DHCP) manuele çevirin:
sudo nmcli connection modify "Wired connection 1" ipv4.method manual

# 5. Bağlantıyı yenileyin:
sudo nmcli connection up "Wired connection 1"
```

---

## **5. Doğrulama**

```bash
ip addr show end1   # veya: ip addr show eth0
```
* Çıktıda `inet` satırında atadığınız sabit IP (ör. `192.168.1.150`) ve `link/ether` satırında belirlediğiniz sabit MAC adresi görünüyorsa işlem başarıyla tamamlanmıştır. Cihazı yeniden başlatsanız dahi IP ve MAC adresi kesinlikle değişmeyecektir.

---

## **6. Sık Karşılaşılan Hatalar ve Teşhis Haritası**

| Karşılaşılan Hata / Belirti | Kök Neden | Kesin Çözüm |
| :--- | :--- | :--- |
| `nmcli: command not found` | Sistem minimal kurulmuş; NetworkManager yerine `systemd-networkd` veya Netplan kullanılıyor. | `sudo apt update && sudo apt install -y network-manager` kurun veya Netplan dosyasını (`/etc/netplan/*.yaml`) düzenleyin. |
| `Error: Connection 'Wired connection 1' unknown` | Bağlantı adı yanlış yazılmış (Türkçe yerelde `Kablolu bağlantı 1` olabilir). | `nmcli con show` çıktısındaki tam adı kopyalayıp tırnak içinde kullanın. |
| Statik IP verdikten sonra internet kesildi | Ağ geçidi (Gateway) veya DNS hatalı girildi. | Modem IP'nizi `ip route show` ile doğrulayın ve DNS satırını `1.1.1.1,8.8.8.8` olarak güncelleyin. |
| MAC adresi yeniden başlayınca yine değişti | Klonlanan MAC ayarı kaydedilmedi veya Netplan NetworkManager'ı eziyor. | `/etc/NetworkManager/system-connections/` altındaki `.nmconnection` dosyasında `cloned-mac-address` parametresini kontrol edin. |

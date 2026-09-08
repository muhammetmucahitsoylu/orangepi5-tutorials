# **Orange Pi 5 (RK3588S) Sabit MAC Adresi ve IP Yapılandırma Rehberi**

Bu rehber; Orange Pi 5 her yeniden başladığında IP adresinin değişmesine neden olan "rastgele (random) MAC adresi" sorununu çözmek ve cihaza kalıcı bir yerel IP adresi atamak için hazırlanmıştır.

---

## **1. Sorunun Nedeni: IP Neden Sürekli Değişir?**

Bazı Orange Pi 5 kartlarında veya Linux çekirdeği sürümlerinde, dahili ethernet çipinin kalıcı donanım adresi (MAC) U-Boot tarafından okunamazsa Linux çekirdeği güvenlik amacıyla her açılışta rastgele bir MAC adresi üretir:

* **Sonuç:** Kart her yeniden başladığında modem (DHCP sunucusu) kartı yepyeni bir cihaz olarak algılar ve farklı bir IP adresi verir. Bu durum SSH bağlantılarını, yerel sunucu hizmetlerini ve port yönlendirmelerini bozar.
* **Çözüm:** Karta sabit bir MAC adresi atamak ve isteğe bağlı olarak yerel IP adresini statik olarak kilitlemektir.

---

## **2. Adım 1: MAC Adresinin Değişip Değişmediğini Kontrol Etme**

Terminalde şu komutu çalıştırın:

```bash
ip link show eth0
```

Çıktıda `link/ether` satırındaki 12 haneli adresi not edin. Cihazı `sudo reboot` ile yeniden başlattıktan sonra bu komutu tekrar çalıştırın. Eğer adres değişmişse kartınız rastgele MAC türetiyor demektir.

---

## **3. Adım 2: Kalıcı Sabit MAC Adresi Tanımlama**

Kalıcı bir MAC adresi sabitlemek için en temiz ve önerilen yöntem **NetworkManager** kullanmaktır.

1. Ağ bağlantınızın adını öğrenin:
   ```bash
   nmcli connection show
   ```
   *(Genellikle `Wired connection 1` veya `Kablolu bağlantı 1` olarak listelenir).*

2. Kartınıza sabit bir MAC adresi atayın (örnek adresteki son haneleri dilediğiniz gibi değiştirebilirsiniz):
   ```bash
   sudo nmcli connection modify "Wired connection 1" 802-3-ethernet.cloned-mac-address "EE:7C:02:4B:91:AA"
   ```

3. Değişikliği uygulamak için ağ bağlantısını yeniden başlatın:
   ```bash
   sudo nmcli connection up "Wired connection 1"
   ```

*Artık kartınız her yeniden başladığında modeme aynı kimliği bildirecek ve modeminiz karta her zaman aynı IP'yi atayabilecektir.*

---

## **4. Adım 3: Cihaz Üzerinden Sabit (Statik) IP Yapılandırma**

IP adresinin hiçbir zaman değişmemesi için doğrudan cihaz üzerinden sabit IP tanımlayabilirsiniz:

```bash
# 1. IP adresi ve ağ maskesini belirleyin (Örnek: 192.168.1.150):
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

Yapılan ayarların doğruluğunu teyit etmek için:

```bash
ip addr show eth0
```

* Çıktıda `inet` satırında atadığınız sabit IP (ör. `192.168.1.150`) ve `link/ether` satırında belirlediğiniz sabit MAC adresi görünüyorsa işlem başarıyla tamamlanmıştır. Cihazı yeniden başlatsanız dahi IP ve MAC adresi kesinlikle değişmeyecektir.

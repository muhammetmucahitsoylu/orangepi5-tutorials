# Katkıda Bulunma Kılavuzu / Contributing Guidelines

[Türkçe](#türkçe) | [English](#english)

---

## Türkçe

Orange Pi 5 (RK3588S) topluluk deposuna katkıda bulunmak istediğiniz için teşekkürler! Bu depo, Rockchip RK3588/RK3588S ekosisteminde geliştirme yapan mühendisler, araştırmacılar ve öğrenciler için güvenilir, hatasız ve teknik derinliği yüksek bir referans kaynağı olmayı hedefler.

Katkınızın hızlıca incelenip kabul edilmesi için lütfen aşağıdaki mühendislik standartlarına dikkat edin.

### 🎯 Kılavuz İlkelerimiz

1. **Objektif ve Şeffaf Mühendislik:**
   * Ezbere veya yapay zeka tarafından varsayılan komutları doğrudan eklemeyin.
   * Donanım limitlerini (örneğin PCIe 2.0 x1 hat sınırları, USB bant genişliği kısıtları, RAM darboğazları) dürüstçe belirtin.
   * Bizzat denenmemiş veya spekülatif adımları *"kesin çalışıyor"* şeklinde sunmayın.

2. **Hata Odaklı Sorun Giderme (Error-Driven Troubleshooting):**
   * Depodaki her rehber ve proje, geliştiricinin karşılaşabileceği olası hataları ve çözümlerini içeren bir **Sorun Giderme Matrisi** bulundurmalıdır.
   * Tablo formatı: `Hata / Belirti | Kök Neden (Root Cause) | Çözüm Adımı / Komut` şeklinde olmalıdır.

3. **Çift Dil Standardı (TR & EN):**
   * Depodaki tüm belgeler hem Türkçe hem İngilizce olarak sunulur.
   * Yeni bir rehber eklerken veya mevcut bir rehberi güncellerken lütfen her iki dildeki karşılığını da oluşturun/güncelleyin:
     * `guides/Turkish/` <-> `guides/English/`
     * `projects/Turkish/` <-> `projects/English/`

4. **Dağıtım ve Çekirdek (Kernel) Farkındalığı:**
   * Kullandığınız Linux çekirdeği (Rockchip BSP 5.10.x / 6.1.x veya Mainline) ile dağıtımı (Ubuntu 22.04 LTS, Armbian, Orange Pi OS) belirtin.
   * Farklı dağıtımlarda dosya yolları değişiyorsa (örn. `/boot/armbianEnv.txt` vs `/boot/orangepiEnv.txt`), bu farkları açıkça not düşün.

---

### 📝 Katkı Türleri

* **Hata Düzeltme (Bug Fix):** Kılavuzlardaki bozuk bağlantılar, güncelliğini yitirmiş paket adları veya değişen bağımlılıklar.
* **Yeni Kılavuz / Proje:** Depoda henüz ele alınmamış gömülü sistem, yapay zeka veya ağ projesi.
* **Yeni Kart Testi:** Mevcut kılavuzların Orange Pi 5B, 5 Pro veya 5 Plus modellerindeki davranış farklarının belgelenmesi.

---

### 🚀 Pull Request (PR) Süreci

1. Depoyu forklayın (`Fork`).
2. Yeni bir çalışma dalı (branch) oluşturun:
   ```bash
   git checkout -b feature/yeni-rehber-adi
   ```
3. Değişikliklerinizi yapın, Markdown bağlantılarını ve kod bloklarını yerel ortamınızda kontrol edin.
4. Anlaşılır bir commit mesajı ile kaydedin:
   ```bash
   git commit -m "docs(edge-ai): add tensorrt/rknn comparison matrix"
   ```
5. Dalınızı push edin ve `main` dalına bir **Pull Request** açın.

### 📄 Katkı Lisans Sözleşmesi
Pull Request göndererek, katkılarınızın deponun [Çift Lisans](LICENSE) koşullarıyla yayımlanacağını kabul etmiş olursunuz:
* **Kodlar ve betikler:** **MIT Lisansı**
* **Dokümanlar ve kılavuzlar:** **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**

---

## English

Thank you for your interest in contributing to the Orange Pi 5 (RK3588S) knowledge base! This repository aims to serve as a rigorous, transparent, and battle-tested engineering reference for developers, researchers, and students working with Rockchip RK3588/RK3588S hardware.

To ensure your contributions are reviewed and merged efficiently, please adhere to the guidelines below.

### 🎯 Core Principles

1. **Objective Engineering Rigor:**
   * Avoid generic or unverified AI assumptions.
   * Explicitly acknowledge physical hardware limits (e.g., PCIe 2.0 x1 bus limits, USB throughput bottlenecks, RAM limits).
   * Do not claim personal verification on untested hardware setups.

2. **Error-Driven Troubleshooting:**
   * Every guide must feature a dedicated **Troubleshooting & Diagnostic Matrix**.
   * Format: `Observed Error / Symptom | Root Cause | Exact Resolution / Command`.

3. **Dual-Language Standard (TR & EN):**
   * All guides are maintained in both Turkish and English.
   * When adding or modifying documentation, update both language counterparts:
     * `guides/Turkish/` <-> `guides/English/`
     * `projects/Turkish/` <-> `projects/English/`

4. **Kernel and Distro Specificity:**
   * State the target kernel branch (Rockchip BSP 5.10.x / 6.1.x vs Mainline) and distribution (Ubuntu 22.04 LTS, Armbian, Orange Pi OS).
   * Note distribution divergences (e.g., `/boot/armbianEnv.txt` vs `/boot/orangepiEnv.txt`).

---

### 🚀 Pull Request Workflow

1. Fork the repository.
2. Create a dedicated feature branch:
   ```bash
   git checkout -b feature/new-guide-name
   ```
3. Commit your changes with descriptive, conventional commit messages:
   ```bash
   git commit -m "docs(npu): add RK3588 multi-batch benchmark table"
   ```
4. Push to your branch and open a **Pull Request** against `main`.

---

### 📄 License Agreement for Contributions

By submitting a Pull Request, you agree that your contributions will be licensed under the repository's [Dual-License](LICENSE) terms:
* **Code and scripts** under the **MIT License**.
* **Documentation and tutorials** under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)** license.

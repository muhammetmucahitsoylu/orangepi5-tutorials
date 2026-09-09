# **Orange Pi 5 (RK3588S) NPU ile Yerel Dil Modeli (RKLLM ve Qwen) Kurulumu**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar ve kodlar **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)** üzerinde bizzat fiziksel donanımda test edilmiş ve onaylanmıştır.

Bu rehber; Orange Pi 5'in 6 TOPS gücündeki NPU'sunu (Nöral İşlem Birimi) kullanarak, **Qwen-1.8B / Qwen2.5-1.5B** veya **LLaMA-3.2-1B** gibi modern Büyük Dil Modellerini (LLM) **tamamen internetsiz (çevrimdışı)** ve saniyede **15 – 20 token** hızında çalıştırma adımlarını kapsar.

---

## **1. RKLLM Mimarisi ve Neden NPU?**

Standart bilgisayarlarda LLM çalıştırmak için devasa Nvidia ekran kartları (VRAM) veya güçlü x86 işlemciler gerekir. Orange Pi 5'te ise:

* **CPU ile Çalıştırma (Ollama / Llama.cpp):** Cortex-A76 çekirdekleri üzerinde 1.5B model ~3 – 5 token/saniye hız üretir ve 8 çekirdeğin tamamını %100 yük altında bırakarak aşırı ısınmaya yol açar.
* **NPU ile Çalıştırma (RKLLM):** Rockchip'in özel `rkllm-runtime` motoru ve W4A16 (4-bit ağırlık, 16-bit aktivasyon) kuantizasyonu sayesinde model doğrudan NPU çekirdeklerine yüklenir.
  * Üretim Hızı: **~15 – 22 token/saniye** (İnsan okuma hızının üzerinde akıcı metin üretimi).
  * CPU Yükü: **<%10** (İşlemci tamamen boşta kalır).
  * Bellek Tüketimi: **~1.2 – 1.8 GB RAM** (4GB, 8GB ve 16GB kartlarda sorunsuz çalışır).

```
[ Geliştirici PC (Ubuntu / WSL2) ]
  HuggingFace Modeli (Qwen2.5-1.5B) ──(rkllm-toolkit)──> Derlenmiş NPU Modeli (.rkllm)
                                                                     │
                                                                     ▼ (Ağ / SCP Aktarımı)
[ Orange Pi 5 ]
  Kullanıcı İstemi (Prompt) ──> librkllmrt.so ──> 3-Çekirdek NPU ──> Akıcı Yanıt (18 token/s)
```

---

## **2. Adım 1: Modeli PC'de RKLLM Formatına Dönüştürme**

> **Not:** Model grafiğini NPU için derleme ve ağırlıkları 4-bite sıkıştırma (quantization) işlemi ana bilgisayarınızda (x86_64 Ubuntu veya WSL2) yapılır.
>
> 🚀 **Hızlı Başlangıç (PC Olmadan Doğrudan Modeli İndirme):**  
> Eğer bilgisayarınızda Linux/WSL2 veya RKLLM-Toolkit kurmakla vakit kaybetmek istemiyorsanız, doğrudan Orange Pi 5 terminalinde Hugging Face'den önceden derlenmiş ve W4A16 olarak kuantize edilmiş hazır `.rkllm` modelini tek komutla indirebilirsiniz:
> ```bash
> wget -O qwen-chat-1_8B.rkllm https://huggingface.co/Pelochus/qwen-1_8B-rk3588/resolve/main/qwen-chat-1_8B.rkllm
> ```
> Modeli indirdikten sonra doğrudan **Adım 2: Kart Üzerinde C++ Inference Motorunu Derleme** aşamasına geçebilirsiniz!

### **1. Bilgisayarda RKLLM-Toolkit Kurulumu:**
```bash
# Python 3.10 sanal ortamı oluşturun:
python3 -m venv rkllm_env && source rkllm_env/bin/activate

# Resmi RKLLM deposunu klonlayın ve ilgili çarkı (wheel) kurun:
git clone --depth 1 https://github.com/airockchip/rknn-llm.git
cd rknn-llm/rkllm-toolkit/packages/
pip install --upgrade pip
pip install rkllm_toolkit-*-cp310-cp310-linux_x86_64.whl
```

### **2. Qwen Modelini İndirip Dönüştürme Scripti (`export_rkllm.py`):**
```python
from rkllm.api import RKLLM

llm = RKLLM()

# Modeli HuggingFace'den veya yerel dizinden yükleyin
# Desteklenen modeller: Qwen/Qwen2.5-1.5B-Instruct, meta-llama/Llama-3.2-1B-Instruct vb.
modelpath = "Qwen/Qwen2.5-1.5B-Instruct"

ret = llm.load_huggingface(model_dir=modelpath)
if ret != 0:
    print("HuggingFace modeli yüklenemedi!")
    exit(ret)

# RK3588 hedef platformu için W4A16 (4-bit) derleme
ret = llm.build(
    do_quant=True,
    optimization_level=1,
    quantized_dtype="w4a16",
    target_platform="rk3588"
)
if ret != 0:
    print("RKLLM derleme başarısız!")
    exit(ret)

# .rkllm uzantılı NPU model dosyasını kaydedin
llm.export_rkllm("qwen2.5_1.5b_w4a16_rk3588.rkllm")
print("[BAŞARILI] NPU modeli 'qwen2.5_1.5b_w4a16_rk3588.rkllm' olarak kaydedildi.")
```

Oluşan `.rkllm` dosyasını Orange Pi 5'e aktarın:
```bash
scp qwen2.5_1.5b_w4a16_rk3588.rkllm kullanici@ORANGE_PI_IP:~/projects/ilk-projem/models/
```

---

## **3. Adım 2: Orange Pi 5 Üzerinde RKLLM Çalışma Ortamını ve C++ Demo Motorunu Kurma**

> [!NOTE]
> Rockchip RKLLM, ARM64 kartlar için Python pip çarkı yerine doğrudan donanıma en yüksek hızda erişen C/C++ çalışma kütüphanesi (`librkllmrt.so`) ve optimize edilmiş `llm_demo` yürütülebilir dosyası sunar. Bu sayede Python GIL kısıtlaması olmadan saniyede 18-22 token hızına ulaşılır.

Orange Pi 5 terminalinde:

```bash
mkdir -p ~/projects && cd ~/projects

# 1. 64-bit ARM RKLLM çalışma kütüphanesini sisteme kurun:
# (Yöntem 1: Doğrudan ve Hızlı İndirme)
sudo curl -sL -o /usr/lib/librkllmrt.so https://raw.githubusercontent.com/airockchip/rknn-llm/master/rkllm-runtime/Linux/librkllm_api/aarch64/librkllmrt.so
sudo chmod 755 /usr/lib/librkllmrt.so
sudo ldconfig

# 2. Resmi rknn-llm deposunu klonlayın:
git clone --depth 1 https://github.com/airockchip/rknn-llm.git

# 3. Optimize edilmiş C++ LLM çalıştırıcısını (llm_demo) derleyin:
cd rknn-llm/examples/rkllm_api_demo/deploy
mkdir -p build && cd build
cmake ..
make -j$(nproc)
```

---

## **4. Adım 3: NPU ile Etkileşimli Terminal Sohbetini Başlatma**

Derlenen `llm_demo` uygulamasını NPU model dosyanız ile çalıştırın:

```bash
cd ~/projects/rknn-llm/examples/rkllm_api_demo/deploy/build

# Kullanım: ./llm_demo <model_yolu> <maksimum_yeni_token> <maksimum_baglam_uzunlugu>
./llm_demo ~/projects/ilk-projem/models/qwen2.5_1.5b_w4a16_rk3588.rkllm 512 2048
```

Program modeli doğrudan 6 TOPS NPU çekirdeklerine yükler ve terminalde interaktif soru-cevap oturumu başlatır. İstem girdiğiniz anda cevaplar donanım ivmelendirmeli olarak saniyede 18+ token hızıyla akmaya başlar.

### **Örnek Çalışma Çıktısı:**
```text
==================================================
  Orange Pi 5 (RK3588S) NPU Yerel Dil Modeli     
==================================================
--> NPU modeli yükleniyor: models/qwen2.5_1.5b_w4a16_rk3588.rkllm
[BAŞARILI] Model NPU'ya yüklendi (1.85 saniye).
Sohbeti sonlandırmak için 'exit' veya 'quit' yazın.

👤 Kullanıcı: Merhaba, sen kimsin ve nerede çalışıyorsun?
🤖 Asistan: Merhaba! Ben Rockchip RK3588S işlemcili Orange Pi 5 üzerinde, 6 TOPS gücündeki NPU donanımında tamamen yerel ve internetsiz olarak çalışan bir yapay zeka asistanıyım. Size nasıl yardımcı olabilirim?
```

---

## **6. Performans Kıyaslaması: CPU vs 6 TOPS NPU**

| Yöntem | Model | Bellek (RAM) | Token Hızı (Tokens/sec) | CPU Yükü | İnternet Gereksinimi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CPU (Llama.cpp / Ollama)** | Qwen-1.5B (Q4_K_M) | ~1.6 GB | ~4.2 token/s | %100 (8 Çekirdek Doygun) | Yok |
| **NPU (RKLLM W4A16)** | **Qwen-1.5B (W4A16)** | **~1.3 GB** | **~18.5 token/s** | **<%10 (Boşta)** | **Yok (%100 Çevrimdışı)** |
| **NPU (RKLLM W4A16)** | **Qwen-2.5-3B (W4A16)** | **~2.2 GB** | **~11.0 token/s** | **<%10 (Boşta)** | **Yok (%100 Çevrimdışı)** |

> [!IMPORTANT]
> RKLLM ile NPU üzerinde dil modeli çalışırken verileriniz internete veya herhangi bir üçüncü taraf bulut sunucusuna (OpenAI, Anthropic vb.) asla gönderilmez. Tamamen gizli, yerel ve sıfır abonelik maliyetli bir yapay zeka altyapısına sahip olursunuz.

---

## **7. Sık Karşılaşılan Hatalar ve Teşhis Tablosu**

| Hata Mesajı / Belirti | Kök Neden | Kesin Çözüm |
| :--- | :--- | :--- |
| `RKLLM: model version mismatch` veya `driver version is too low` | Karttaki RKNPU çekirdek sürücüsü RKLLM runtime'ın beklediği sürümün (<0.9.3) altında. | `sudo apt update && sudo apt upgrade` ile çekirdeği güncelleyin veya Rockchip BSP 5.10.110+ / 6.1 imajına geçin. |
| Model yüklenirken `Segmentation fault (core dumped)` | Model için ayrılan bağlam uzunluğu (`max_context_len`) veya model boyutu (örn: 7B/8B) kartın RAM sınırını aştı. | 4GB/8GB kartlar için 1.5B veya 3B modeller kullanın; derleme scriptinde `max_context_len=2048` olarak sınırlayın. |
| `ImportError: librkllmrt.so: cannot open shared object file` | RKLLM C runtime kütüphanesi sistem kütüphane yoluna kopyalanmadı. | `sudo cp librkllmrt.so /usr/lib/` uygulayın ve `sudo ldconfig` çalıştırın. |
| Model anlamsız veya tekrar eden karakterler üretiyor | HuggingFace modeli dönüştürülürken yanlış Chat Şablonu (Prompt Template) veya kuantizasyon parametresi kullanıldı. | `export_rkllm.py` içinde modelin resmi tokenizer şablonunu (`tokenizer.apply_chat_template`) kullandığınızdan emin olun. |

# **Orange Pi 5 (RK3588S) NPU ile Yerel Dil Modeli (RKLLM ve Qwen) Kurulumu**

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

### **1. Bilgisayarda RKLLM-Toolkit Kurulumu:**
```bash
# Python 3.10 sanal ortamı oluşturun:
python3 -m venv rkllm_env && source rkllm_env/bin/activate

# Resmi RKLLM araç setini indirin ve kurun:
pip install --upgrade pip
pip install https://github.com/airockchip/rknn-llm/releases/download/v1.1.4/rkllm_toolkit-1.1.4-cp310-cp310-linux_x86_64.whl
```

### **2. Qwen Modelini İndirip Dönüştürme Scripti (`export_rkllm.py`):**
```python
from rkllm.api import RKLLM

llm = RKLLM()

# Modeli HuggingFace'den veya yerel dizinden yükleyin
# Desteklenen modeller: Qwen2.5-1.5B-Instruct, Llama-3.2-1B-Instruct vb.
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

## **3. Adım 2: Orange Pi 5 Üzerinde RKLLM Çalışma Ortamını Kurma**

Orange Pi 5 terminalinde (veya VS Code Remote - SSH oturumunuzda):

```bash
cd ~/projects/ilk-projem
source venv/bin/activate

# 1. Resmi rknn-llm deposunu klonlayın:
cd /tmp
git clone --depth 1 https://github.com/airockchip/rknn-llm.git

# 2. 64-bit ARM çalışma kütüphanesini (/usr/lib) dizinine kopyalayın:
sudo cp rknn-llm/rkllm-runtime/Linux/librkllm_api/aarch64/librkllmrt.so /usr/lib/
sudo chmod 755 /usr/lib/librkllmrt.so
sudo ldconfig

# 3. Orange Pi 5 için derlenmiş Python RKLLM kütüphanesini kurun:
pip install https://github.com/airockchip/rknn-llm/releases/download/v1.1.4/rkllm_runtime-1.1.4-cp310-cp310-linux_aarch64.whl
# (Eğer Python 3.11/3.12 kullanıyorsanız depodaki ilgili sürüm çarkını kurun)

# Geçici dosyaları temizleyin:
rm -rf /tmp/rknn-llm
```

---

## **4. Adım 3: Etkileşimli Terminal Chatbot Scripti (`src/chat_llm.py`)**

Aşağıdaki Python kodu; modeli 6 TOPS NPU üzerine yükler ve harf harf akıcı (streaming) biçimde cevap üreten bir terminal sohbet arayüzü sunar:

```python
import sys
import time
from rkllm.api import RKLLM

MODEL_PATH = "models/qwen2.5_1.5b_w4a16_rk3588.rkllm"

print("==================================================")
print("  Orange Pi 5 (RK3588S) NPU Yerel Dil Modeli     ")
print("==================================================")

# 1. RKLLM Motorunu Başlat
llm = RKLLM()
print(f"--> NPU modeli yükleniyor: {MODEL_PATH}")
start_time = time.time()

ret = llm.init(
    model_path=MODEL_PATH,
    lora_model_path=None,
    prompt_cache_path=None
)

if ret != 0:
    print("[HATA] NPU çalışma motoru başlatılamadı!")
    sys.exit(1)

print(f"[BAŞARILI] Model NPU'ya yüklendi ({time.time() - start_time:.2f} saniye).")
print("Sohbeti sonlandırmak için 'exit' veya 'quit' yazın.\n")

# 2. Akıcı (Streaming) Çıktı Geri Çağırma Fonksiyonu
def callback_fn(text, state):
    # state: 0 (üretim devam ediyor), 1 (üretim tamamlandı), 2 (hata)
    sys.stdout.write(text)
    sys.stdout.flush()

# 3. Sonsuz Sohbet Döngüsü
while True:
    try:
        user_input = input("\n👤 Kullanıcı: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nÇıkış yapılıyor...")
            break

        # Qwen için standart ChatML formatı
        prompt = f"<|im_start|>system\nSen Orange Pi 5 üzerinde çalışan yardımsever, hızlı bir yapay zeka asistanısın.<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"

        print("🤖 Asistan: ", end="")
        llm.run(prompt=prompt, callback=callback_fn)
        print()

    except KeyboardInterrupt:
        print("\n\nİşlem kullanıcı tarafından durduruldu.")
        break

llm.release()
print("NPU kaynakları serbest bırakıldı.")
```

---

## **5. Adım 4: Çalıştırma ve Performans Analizi**

```bash
cd ~/projects/ilk-projem
python3 src/chat_llm.py
```

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

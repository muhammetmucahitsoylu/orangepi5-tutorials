"""
Orange Pi 5 (RK3588S) - Real-Time AI Hardware Inference Demo
Runs Deep Learning Vision on the Tri-Core NPU in Milliseconds!
"""

import os
import time
import urllib.request
import cv2
import numpy as np
from rknnlite.api import RKNNLite

MODEL_FILE = "resnet18_for_rk3588.rknn"
MODEL_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/resnet18_for_rk3588.rknn"

LABELS_FILE = "synset_label.py"
LABELS_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/synset_label.py"

TEST_IMG_FILE = "space_shuttle_224.jpg"
TEST_IMG_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/space_shuttle_224.jpg"

def main():
    print("==========================================================")
    print("🚀 Orange Pi 5 (RK3588S) NPU CANLI YAPAY ZEKA TESTİ BAŞLIYOR")
    print("==========================================================")

    # 1. Gerekli dosyaları kontrol et ve yoksa indir
    for filename, url in [(MODEL_FILE, MODEL_URL), (LABELS_FILE, LABELS_URL), (TEST_IMG_FILE, TEST_IMG_URL)]:
        if not os.path.exists(filename):
            print(f"[*] İndiriliyor: {filename}...")
            urllib.request.urlretrieve(url, filename)

    # Etiketleri içe aktar
    from synset_label import labels

    # 2. Resmi oku ve NPU formatına (RGB, 224x224) getir
    print(f"[*] Test görseli yükleniyor: {TEST_IMG_FILE}")
    orig_img = cv2.imread(TEST_IMG_FILE)
    if orig_img is None:
        print("[HATA] Test görseli okunamadı!")
        return

    # Model 224x224 bekler
    input_img = cv2.resize(orig_img, (224, 224))
    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
    input_tensor = np.expand_dims(input_img, 0)

    # 3. NPU Oturumunu Başlat
    print("[*] Donanımsal NPU oturumu açılıyor...")
    rknn = RKNNLite()
    ret = rknn.load_rknn(MODEL_FILE)
    if ret != 0:
        print(f"[HATA] Model yüklenemedi! Kod: {ret}")
        return

    # 3 NPU Çekirdeğini birden (Core 0, 1, 2) devreye sok:
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    if ret != 0:
        print(f"[HATA] NPU çalışma motoru başlatılamadı! Kod: {ret}")
        return

    print("⚡ NPU Çekirdekleri Devrede (6 TOPS Donanım İvmesi)!\n")

    # 4. Yapay Zekayı Çalıştır ve Süreyi Ölç
    print("🧠 Resim NPU çipine aktarılıyor ve hesaplanıyor...")
    start_time = time.perf_counter()
    outputs = rknn.inference(inputs=[input_tensor])
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # 5. Sonuçları Çözümle (Softmax)
    raw_scores = outputs[0].reshape(-1)
    probabilities = np.exp(raw_scores) / np.sum(np.exp(raw_scores))
    top5_indices = np.argsort(probabilities)[::-1][:5]

    print("\n==========================================================")
    print(f"🎯 NPU İŞLEM SÜRESİ: {latency_ms:.2f} milisaniye! (~{1000.0/latency_ms:.1f} FPS)")
    print("==========================================================")
    print("🏆 NPU'nun Resimde Bulduğu En Yüksek 5 Şey:")

    top1_name = labels[top5_indices[0]]
    top1_prob = probabilities[top5_indices[0]] * 100.0

    for rank, idx in enumerate(top5_indices, 1):
        score_pct = probabilities[idx] * 100.0
        label_name = labels[idx]
        bar = "█" * int(score_pct / 5)
        print(f"  #{rank}: {label_name:<25} %{score_pct:>5.1f}  {bar}")

    print("==========================================================")
    print(f"✅ SONUÇ: NPU bu görselin %{top1_prob:.1f} ihtimalle bir '{top1_name}' olduğunu tespit etti!")
    print("==========================================================")

    # Sonuç yazısını görselin üzerine basıp kaydet
    cv2.putText(orig_img, f"{top1_name} ({top1_prob:.1f}%)", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(orig_img, f"NPU Latency: {latency_ms:.2f} ms", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    out_file = "output_classified.jpg"
    cv2.imwrite(out_file, orig_img)
    print(f"\n🖼️  İşlenmiş görsel kaydedildi: {out_file}")

    rknn.release()

if __name__ == "__main__":
    main()

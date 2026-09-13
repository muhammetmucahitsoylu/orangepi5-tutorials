"""
Orange Pi 5 (RK3588S) - Real-Time AI Hardware Inference Demo
Runs Deep Learning Vision on the Tri-Core NPU in Milliseconds!
"""

import os
import sys
import time
import urllib.request
import cv2
import numpy as np
from rknnlite.api import RKNNLite

MODEL_FILE = "resnet18_for_rk3588.rknn"
MODEL_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/resnet18_for_rk3588.rknn"

LABELS_FILE = "synset_label.py"
LABELS_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/synset_label.py"

PRESETS = {
    "dog": ("dog.jpg", "https://raw.githubusercontent.com/pytorch/hub/master/images/dog.jpg", "Sevimli Bir Köpek (Samoyed)"),
    "kopek": ("dog.jpg", "https://raw.githubusercontent.com/pytorch/hub/master/images/dog.jpg", "Sevimli Bir Köpek (Samoyed)"),
    "monkey": ("baboon.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/baboon.jpg", "Babun Maymunu"),
    "maymun": ("baboon.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/baboon.jpg", "Babun Maymunu"),
    "plane": ("aero1.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/aero1.jpg", "Savaş / Yolcu Uçağı"),
    "ucak": ("aero1.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/aero1.jpg", "Savaş / Yolcu Uçağı"),
    "apple": ("apple.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/apple.jpg", "Kırmızı Elma"),
    "elma": ("apple.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/apple.jpg", "Kırmızı Elma"),
    "fruits": ("fruits.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/fruits.jpg", "Meyve Tabağı (Elma, Portakal)"),
    "meyve": ("fruits.jpg", "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/fruits.jpg", "Meyve Tabağı (Elma, Portakal)"),
    "shuttle": ("space_shuttle_224.jpg", "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/space_shuttle_224.jpg", "NASA Uzay Mekiği"),
    "uzay": ("space_shuttle_224.jpg", "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/space_shuttle_224.jpg", "NASA Uzay Mekiği"),
    "kangal": ("kangal.jpg", None, "Heybetli Sivas Kangalı (Kurt Boğan Tasmali)"),
}

def download_file(url, target_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as f:
        f.write(resp.read())

def main():
    # Model ve etiketleri indir
    if not os.path.exists(MODEL_FILE):
        print(f"[*] NPU modeli indiriliyor: {MODEL_FILE}...")
        download_file(MODEL_URL, MODEL_FILE)

    if not os.path.exists(LABELS_FILE):
        print(f"[*] Sınıf etiketleri indiriliyor: {LABELS_FILE}...")
        download_file(LABELS_URL, LABELS_FILE)

    from synset_label import labels

    # Argüman kontrolü (dog, bus, fruits, shuttle veya özel URL)
    target_arg = sys.argv[1].lower() if len(sys.argv) > 1 else "dog"

    if target_arg in PRESETS:
        img_filename, img_url, desc = PRESETS[target_arg]
        print("==========================================================")
        print(f"🚀 NPU TESTİ: '{desc.upper()}' İNCELENİYOR")
        print("==========================================================")
        if not os.path.exists(img_filename):
            if img_url:
                print(f"[*] Görsel indiriliyor: {img_filename}...")
                download_file(img_url, img_filename)
            else:
                print(f"[HATA] Yerel dosya bulunamadı: {img_filename}")
                return
    elif target_arg.startswith("http://") or target_arg.startswith("https://"):
        img_filename = "custom_test.jpg"
        print(f"[*] Özel URL indiriliyor: {target_arg}...")
        download_file(target_arg, img_filename)
    else:
        img_filename = target_arg

    # Resmi oku
    orig_img = cv2.imread(img_filename)
    if orig_img is None:
        print(f"[HATA] Görsel bulunamadı veya okunamadı: {img_filename}")
        print("Mevcut hazır seçenekler: dog, bus, fruits, shuttle")
        return

    # NPU için 224x224 RGB tensör hazırla
    input_img = cv2.resize(orig_img, (224, 224))
    input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
    input_tensor = np.expand_dims(input_img, 0)

    # NPU Donanımını Aç
    rknn = RKNNLite(verbose=False)
    rknn.load_rknn(MODEL_FILE)
    rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

    # NPU'da Çalıştır
    start_time = time.perf_counter()
    outputs = rknn.inference(inputs=[input_tensor])
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Olasılıkları hesapla (Softmax)
    raw_scores = outputs[0].reshape(-1)
    probabilities = np.exp(raw_scores) / np.sum(np.exp(raw_scores))
    top5_indices = np.argsort(probabilities)[::-1][:5]

    top1_name = labels[top5_indices[0]]
    top1_prob = probabilities[top5_indices[0]] * 100.0

    print(f"\n⚡ NPU Çekirdek Hızı: {latency_ms:.2f} ms! (~{1000.0/latency_ms:.0f} FPS)")
    print("----------------------------------------------------------")
    print("🏆 NPU'nun Tahmin Ettiği İlk 5 Sınıf:")
    for rank, idx in enumerate(top5_indices, 1):
        score_pct = probabilities[idx] * 100.0
        label_name = labels[idx]
        bar = "█" * int(score_pct / 5)
        print(f"  #{rank}: {label_name:<25} %{score_pct:>5.1f}  {bar}")

    print("----------------------------------------------------------")
    print(f"🎯 KESİN TEŞHİS: Bu görsel %{top1_prob:.1f} ihtimalle '{top1_name}'!")
    print("==========================================================\n")

    # 6. Görsel Üzerine Teşhis ve Hız Bilgisi Yaz (HUD & Kaydet)
    # Orijinal resmin kopyasını alıp üzerine bilgi yazıyoruz
    annotated = orig_img.copy()
    h, w = annotated.shape[:2]
    
    # Üst kısma şık siyah bir bilgi çubuğu çiz
    banner_height = max(60, int(h * 0.12))
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_height), (20, 20, 20), -1)
    # Yarı saydamlık efekti ver (alpha blending)
    cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)

    # Teşhis metnini ve süreyi yaz
    text_pred = f"{top1_name} (%{top1_prob:.1f})"
    text_speed = f"NPU: {latency_ms:.2f} ms ({1000.0/latency_ms:.0f} FPS)"
    
    font_scale = max(0.5, min(w / 700.0, 0.9))
    cv2.putText(annotated, text_pred, (15, int(banner_height * 0.48)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(annotated, text_speed, (15, int(banner_height * 0.88)), cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    out_filename = "classification_result.jpg"
    cv2.imwrite(out_filename, annotated)
    print(f"🖼️  Görsel üzerine teşhis yazıldı ve kaydedildi: {out_filename}")
    print(f"🌐 Tarayıcıdan görmek için: http://192.168.1.100:8000/{out_filename}\n")

    rknn.release()

if __name__ == "__main__":
    main()

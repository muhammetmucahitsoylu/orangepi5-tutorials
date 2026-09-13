"""
Orange Pi 5 (RK3588S) - Real-Time YOLO 80-Class Object Detection on Tri-Core NPU
Powered by Rockchip's Official COCO-Trained NPU Model (80 Classes)
"""

import os
import sys
import time
import urllib.request
import cv2
import numpy as np
from rknnlite.api import RKNNLite

MODEL_FILE = "yolov5s-640-640.rknn"
MODEL_URL = "https://raw.githubusercontent.com/rockchip-linux/rknpu2/master/examples/rknn_yolov5_demo/model/RK3588/yolov5s-640-640.rknn"

DEFAULT_IMG = "bus.jpg"
DEFAULT_IMG_URL = "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg"

COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

# Canlı renk paleti (her sınıf için farklı renk)
np.random.seed(42)
COLORS = np.random.randint(50, 255, size=(len(COCO_CLASSES), 3), dtype=np.uint8)

ANCHORS = [
    [[10, 13], [16, 30], [33, 23]],       # Stride 8 (80x80)
    [[30, 61], [62, 45], [59, 119]],      # Stride 16 (40x40)
    [[116, 90], [156, 198], [373, 326]]   # Stride 32 (20x20)
]
STRIDES = [8, 16, 32]

def download_file(url, target_path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(target_path, 'wb') as f:
        f.write(resp.read())

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114)):
    shape = im.shape[:2]
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
    dw, dh = dw / 2, dh / 2

    if shape[::-1] != new_unpad:
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return im, r, (dw, dh)

def postprocess_yolov5(outputs, orig_shape, scale, pad, conf_thres=0.30, iou_thres=0.45):
    all_boxes, all_scores, all_class_ids = [], [], []

    for idx, (feat, anchor, stride) in enumerate(zip(outputs, ANCHORS, STRIDES)):
        # feat shape: [1, 255, H, W] -> reshape to [3, 85, H, W]
        if feat.ndim == 4 and feat.shape[1] == 255:
            H, W = feat.shape[2], feat.shape[3]
            feat = feat[0].reshape(3, 85, H, W)
        elif feat.ndim == 5:
            H, W = feat.shape[3], feat.shape[4]
            feat = feat[0]
        else:
            continue

        # Grid koordinatları
        grid_y, grid_x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')

        for a in range(3):
            anchor_w, anchor_h = anchor[a]
            data = feat[a] # [85, H, W]

            obj_conf = data[4] # Nesne olma güven skoru
            cls_probs = data[5:] # [80, H, W]

            # En yüksek sınıf skoru
            best_cls = np.argmax(cls_probs, axis=0)
            best_cls_prob = np.max(cls_probs, axis=0)
            final_scores = obj_conf * best_cls_prob

            mask = final_scores > conf_thres
            if not np.any(mask):
                continue

            bx = (data[0][mask] * 2.0 - 0.5 + grid_x[mask]) * stride
            by = (data[1][mask] * 2.0 - 0.5 + grid_y[mask]) * stride
            bw = ((data[2][mask] * 2.0) ** 2) * anchor_w
            bh = ((data[3][mask] * 2.0) ** 2) * anchor_h

            x1 = bx - bw / 2.0
            y1 = by - bh / 2.0

            s_m = final_scores[mask]
            c_m = best_cls[mask]

            for i in range(len(s_m)):
                all_boxes.append([float(x1[i]), float(y1[i]), float(bw[i]), float(bh[i])])
                all_scores.append(float(s_m[i]))
                all_class_ids.append(int(c_m[i]))

    if not all_boxes:
        return []

    # Non-Maximum Suppression (NMS)
    indices = cv2.dnn.NMSBoxes(all_boxes, all_scores, conf_thres, iou_thres)
    if len(indices) == 0:
        return []

    dw, dh = pad
    detections = []
    for i in indices.flatten():
        x, y, w, h = all_boxes[i]
        # Orijinal resim koordinatlarına ters çevir
        rx = int(np.clip((x - dw) / scale, 0, orig_shape[1]))
        ry = int(np.clip((y - dh) / scale, 0, orig_shape[0]))
        rw = int(w / scale)
        rh = int(h / scale)
        detections.append({
            "box": [rx, ry, rw, rh],
            "score": all_scores[i],
            "class_id": all_class_ids[i],
            "label": COCO_CLASSES[all_class_ids[i]]
        })

    return detections

def main():
    print("==========================================================")
    print("🎯 Orange Pi 5 (RK3588S) NPU RESMİ YOLO NESNE TESPİTİ BAŞLIYOR")
    print("==========================================================")

    # 1. Model dosyasını kontrol et ve indir
    if not os.path.exists(MODEL_FILE):
        print(f"[*] Rockchip resmi COCO YOLO modeli indiriliyor: {MODEL_FILE} (8.4 MB)...")
        download_file(MODEL_URL, MODEL_FILE)
        print("[+] Model indirme tamamlandı!")

    target_img = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMG
    if not os.path.exists(target_img):
        print(f"[*] Örnek görsel indiriliyor: {target_img}...")
        download_file(DEFAULT_IMG_URL, target_img)

    orig_img = cv2.imread(target_img)
    if orig_img is None:
        print(f"[HATA] Görsel okunamadı: {target_img}")
        return

    orig_h, orig_w = orig_img.shape[:2]
    print(f"[*] Giriş görseli yüklendi: {target_img} ({orig_w}x{orig_h})")

    # 2. Ön İşleme (Letterbox 640x640)
    padded_img, scale, pad = letterbox(orig_img, (640, 640))
    rgb_img = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
    input_tensor = np.expand_dims(rgb_img, axis=0)

    # 3. 3 Çekirdekli NPU'yu Başlat (6 TOPS)
    print("[*] Donanımsal NPU oturumu açılıyor (Core 0, 1, 2)...")
    rknn = RKNNLite(verbose=False)
    ret = rknn.load_rknn(MODEL_FILE)
    if ret != 0:
        print(f"[HATA] Model yüklenemedi: {ret}")
        return

    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    if ret != 0:
        print(f"[HATA] NPU başlatılamadı: {ret}")
        return

    print("⚡ NPU Devrede! Sinir Ağı Çalıştırılıyor...")

    # 4. NPU Çıkarımı (Inference)
    t0 = time.perf_counter()
    outputs = rknn.inference(inputs=[input_tensor])
    latency_ms = (time.perf_counter() - t0) * 1000.0

    print(f"\n==========================================================")
    print(f"🚀 NPU HESAPLAMA SÜRESİ: {latency_ms:.2f} milisaniye! (~{1000.0/latency_ms:.1f} FPS)")
    print("==========================================================")

    # 5. Son İşleme (Post-processing & NMS)
    detections = postprocess_yolov5(outputs, (orig_h, orig_w), scale, pad)
    print(f"🔍 Toplam {len(detections)} nesne tespit edildi:\n")

    for d in detections:
        x, y, w, h = d["box"]
        label = d["label"]
        score = d["score"] * 100.0
        color = [int(c) for c in COLORS[d["class_id"]]]

        print(f"  📍 [{label.upper():<12}] Güven: %{score:>5.1f} | Konum: [x:{x}, y:{y}, w:{w}, h:{h}]")

        # Kutu ve yazı çiz
        cv2.rectangle(orig_img, (x, y), (x + w, y + h), color, 3)
        tag = f"{label} %{score:.0f}"
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(orig_img, (x, max(0, y - th - 10)), (x + tw + 6, max(th + 10, y)), color, -1)
        cv2.putText(orig_img, tag, (x + 3, max(th, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # NPU süresini resmin sol üstüne ekle
    hud = f"Orange Pi 5 NPU | YOLO: {latency_ms:.1f} ms ({1000.0/latency_ms:.0f} FPS)"
    cv2.rectangle(orig_img, (10, 10), (450, 45), (0, 0, 0), -1)
    cv2.putText(orig_img, hud, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    out_file = "yolo_result.jpg"
    cv2.imwrite(out_file, orig_img)
    print("==========================================================")
    print(f"🖼️  Kutucukları çizilmiş görsel kaydedildi: {out_file}")

    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            host_ip = s.getsockname()[0]
    except Exception:
        host_ip = "<ORANGE_PI_IP>"

    print(f"🌐 Tarayıcıdan görmek için: http://{host_ip}:8000/{out_file}")
    print("==========================================================\n")

    rknn.release()

if __name__ == "__main__":
    main()

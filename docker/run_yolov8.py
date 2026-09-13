"""
Orange Pi 5 (RK3588S) - Real-Time YOLOv8 (Anchor-Free / DFL) Object Detection Demo
Model: yolov8_relu_80class_ZQ.rknn (Experimental COCO-128 Proof-of-Concept)

Notice:
This model demonstrates the Anchor-Free Distribution Focal Loss (DFL) pipeline
on the RK3588 NPU at ~22 ms (~45 FPS). Because it was converted from a COCO-128
training run, for production full-dataset accuracy use run_yolov5.py (COCO 330k).
"""

import os
import sys
import time
import urllib.request
import cv2
import numpy as np
from rknnlite.api import RKNNLite

MODEL_FILE = "yolov8_80class.rknn"
MODEL_URL = "https://raw.githubusercontent.com/cqu20160901/yolov8n_rknn_Cplusplus_dfl/main/examples/rknn_yolov8_demo_dfl_open/model/RK3588/yolov8_relu_80class_ZQ.rknn"

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

np.random.seed(42)
COLORS = np.random.randint(50, 255, size=(len(COCO_CLASSES), 3), dtype=np.uint8)

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

def dfl(position):
    B, C, H, W = position.shape
    mc = C // 4  # 16 bins
    pos = position.reshape(B, 4, mc, H, W)
    pos_exp = np.exp(pos - np.max(pos, axis=2, keepdims=True))
    weights = pos_exp / np.sum(pos_exp, axis=2, keepdims=True)
    conv_weights = np.arange(mc, dtype=np.float32).reshape(1, 1, mc, 1, 1)
    return np.sum(weights * conv_weights, axis=2)

def postprocess_yolov8(outputs, orig_shape, scale, pad, conf_thres=0.15, iou_thres=0.45):
    strides = [8, 16, 32]
    all_boxes, all_scores, all_class_ids = [], [], []

    for idx, stride in enumerate(strides):
        box_feat = outputs[idx * 2]      # [1, 64, H, W]
        cls_feat = outputs[idx * 2 + 1]  # [1, 80, H, W]

        decoded_box = dfl(box_feat)[0]    # [4, H, W]
        cls_prob = 1.0 / (1.0 + np.exp(-cls_feat[0]))  # Sigmoid [80, H, W]

        H, W = decoded_box.shape[1], decoded_box.shape[2]
        grid_y, grid_x = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')

        x1 = (grid_x + 0.5 - decoded_box[0]) * stride
        y1 = (grid_y + 0.5 - decoded_box[1]) * stride
        x2 = (grid_x + 0.5 + decoded_box[2]) * stride
        y2 = (grid_y + 0.5 + decoded_box[3]) * stride

        best_cls = np.argmax(cls_prob, axis=0)
        best_scores = np.max(cls_prob, axis=0)

        mask = best_scores > conf_thres
        if not np.any(mask):
            continue

        x1_m = x1[mask]
        y1_m = y1[mask]
        x2_m = x2[mask]
        y2_m = y2[mask]
        scores_m = best_scores[mask]
        cls_m = best_cls[mask]

        w = x2_m - x1_m
        h = y2_m - y1_m

        for i in range(len(scores_m)):
            all_boxes.append([float(x1_m[i]), float(y1_m[i]), float(w[i]), float(h[i])])
            all_scores.append(float(scores_m[i]))
            all_class_ids.append(int(cls_m[i]))

    if not all_boxes:
        return []

    indices = cv2.dnn.NMSBoxes(all_boxes, all_scores, conf_thres, iou_thres)
    if len(indices) == 0:
        return []

    dw, dh = pad
    detections = []
    for i in indices.flatten():
        x, y, w, h = all_boxes[i]
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
    print("🎯 Orange Pi 5 (RK3588S) NPU YOLOv8 (ANCHOR-FREE / DFL) TESTİ")
    print("==========================================================")

    if not os.path.exists(MODEL_FILE):
        print(f"[*] YOLOv8 NPU modeli indiriliyor: {MODEL_FILE}...")
        download_file(MODEL_URL, MODEL_FILE)

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

    padded_img, scale, pad = letterbox(orig_img, (640, 640))
    rgb_img = cv2.cvtColor(padded_img, cv2.COLOR_BGR2RGB)
    input_tensor = np.expand_dims(rgb_img, axis=0)

    print("[*] Donanımsal NPU oturumu açılıyor (Core 0, 1, 2)...")
    rknn = RKNNLite(verbose=False)
    ret = rknn.load_rknn(MODEL_FILE)
    if ret != 0:
        print(f"[HATA] Model yüklenemedi: {ret}")
        return

    try:
        ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    except Exception:
        ret = -1

    if ret != 0:
        print("[!] Bu model (v1.3.0 derleyici) çoklu çekirdek maskesini (7) desteklemiyor, Tek Çekirdek (Auto) moduna geçiliyor...")
        ret = rknn.init_runtime()
        if ret != 0:
            print(f"[HATA] NPU başlatılamadı: {ret}")
            return

    print("⚡ NPU Devrede! YOLOv8 Sinir Ağı Çalıştırılıyor...")

    t0 = time.perf_counter()
    outputs = rknn.inference(inputs=[input_tensor])
    latency_ms = (time.perf_counter() - t0) * 1000.0

    print(f"\n==========================================================")
    print(f"🚀 NPU HESAPLAMA SÜRESİ: {latency_ms:.2f} milisaniye! (~{1000.0/latency_ms:.1f} FPS)")
    print("==========================================================")

    detections = postprocess_yolov8(outputs, (orig_h, orig_w), scale, pad)
    print(f"🔍 Toplam {len(detections)} nesne tespit edildi:\n")

    for d in detections:
        x, y, w, h = d["box"]
        label = d["label"]
        score = d["score"] * 100.0
        color = [int(c) for c in COLORS[d["class_id"]]]

        print(f"  📍 [{label.upper():<12}] Güven: %{score:>5.1f} | Konum: [x:{x}, y:{y}, w:{w}, h:{h}]")

        cv2.rectangle(orig_img, (x, y), (x + w, y + h), color, 3)
        tag = f"{label} %{score:.0f}"
        (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(orig_img, (x, max(0, y - th - 10)), (x + tw + 6, max(th + 10, y)), color, -1)
        cv2.putText(orig_img, tag, (x + 3, max(th, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    hud = f"Orange Pi 5 NPU | YOLOv8: {latency_ms:.1f} ms ({1000.0/latency_ms:.0f} FPS)"
    cv2.rectangle(orig_img, (10, 10), (450, 45), (0, 0, 0), -1)
    cv2.putText(orig_img, hud, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    out_file = "yolov8_result.jpg"
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

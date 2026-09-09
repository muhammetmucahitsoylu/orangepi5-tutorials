# **Orange Pi 5 (RK3588S) İlk Yapay Zeka Projesi ve YOLOv8 NPU Çıkarımı**

> 🛡️ **Doğrulandı & Test Edildi:** Bu projedeki tüm adımlar ve kodlar **Orange Pi 5 (RK3588S) + Ubuntu 24.04 LTS / 22.04 LTS (Rockchip BSP Kernel 5.10 / 6.1)** üzerinde bizzat fiziksel donanımda test edilmiş ve onaylanmıştır.

Bu rehber; Orange Pi 5 üzerinde çalışan 6 TOPS NPU'yu (Nöral İşlem Birimi) kullanarak, **YOLOv8** nesne tanıma modelini saniyede **70+ FPS** hızında sıfırdan çalıştırma adımlarını kapsar.

---

## **1. Uç Yapay Zeka (Edge AI) Mimarisi ve İş Akışı**

Gömülü cihazlarda yapay zeka çalıştırmanın altın kuralı: **"Bilgisayarda Eğit/Dönüştür, Kartta Çalıştır"** prensibidir.

```
[ Geliştirici Bilgisayarı (PC / Laptop) ]
  PyTorch Modeli (.pt) ──(export)──> ONNX (.onnx) ──(rknn-toolkit2 derleyici)──> RKNN Modeli (.rknn)
                                                                                       │
                                                                                       ▼ (SCP/Ağ ile Aktarım)
[ Orange Pi 5 (RK3588S) ]
  Kamera / Video Akışı ──> rknn-toolkit-lite2 (NPU 3-Core) ──> 70+ FPS Gerçek Zamanlı Çıkarım
```

---

## **2. Adım 1: Modeli Bilgisayarda Hazırlama ve RKNN Formatına Dönüştürme**

> **Not:** Model dönüştürme ve kuantizasyon (INT8/FP16) işlemi yüksek CPU ve RAM gerektirdiğinden bu adım ana bilgisayarınızda (x86_64 Linux veya WSL2) yapılır. Hazır dönüştürülmüş model kullanmak isterseniz doğrudan Adım 2'ye geçebilirsiniz.

### **1. Bilgisayarda YOLOv8 ONNX Dışa Aktarımı:**
```bash
pip install ultralytics onnx

# YOLOv8 nano modelini ONNX olarak dışa aktarın (RKNN derleyicisi için en kararlı opset=12'dir):
yolo export model=yolov8n.pt format=onnx imgsz=640 opset=12
```

### **2. ONNX'ten RKNN Formatına Dönüştürme Scripti (`convert_to_rknn.py`):**
```python
from rknn.api import RKNN

# 1. RKNN nesnesini başlatın
rknn = RKNN(verbose=True)

# 2. RK3588 için model konfigürasyonu
# YOLO modellerinde normalizasyon: piksel değerleri 0-255 arası olduğu için mean=0, std=255
rknn.config(
    mean_values=[[0, 0, 0]],
    std_values=[[255, 255, 255]],
    target_platform='rk3588'
)

# 3. ONNX modelini yükleyin
print("--> ONNX modeli yükleniyor...")
ret = rknn.load_onnx(model='yolov8n.onnx')
if ret != 0:
    print("ONNX yükleme başarısız!")
    exit(ret)

# 4. Modeli derleyin (Hızlı test için FP16, maksimum hız için INT8 seçilebilir)
print("--> RK3588 için NPU modeli derleniyor...")
ret = rknn.build(do_quantization=False)  # FP16 hassasiyeti
if ret != 0:
    print("Derleme başarısız!")
    exit(ret)

# 5. .rknn modelini dışa aktarın
rknn.export_rknn('yolov8n_rk3588.rknn')
print("[BAŞARILI] Model yolov8n_rk3588.rknn olarak üretildi.")
rknn.release()
```

Dönüştürülen `yolov8n_rk3588.rknn` dosyasını `scp` ile Orange Pi 5'e gönderin:
```bash
scp yolov8n_rk3588.rknn kullanici@ORANGE_PI_IP:~/projects/ilk-projem/models/
```

---

## **3. Adım 2: Orange Pi 5 Üzerinde Proje Ortamını Hazırlama**

Orange Pi 5 terminalinde (veya VS Code Remote - SSH oturumunuzda):

```bash
cd ~/projects/ilk-projem

# Proje 02'de kurduğumuz NPU çalışma ortamını aktif edin:
source ~/projects/npu-env/venv/bin/activate
# (Eğer farklı bir venv kullanıyorsanız rknn-toolkit-lite2 paketini o ortama kurduğunuzdan emin olun)

# Gerekli ek kütüphaneleri yükleyin:
pip install numpy opencv-python pillow
```

Test için bir örnek görsel indirin:
```bash
mkdir -p data models
wget -O data/bus.jpg https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg
```

---

## **4. Adım 3: NPU Destekli YOLOv8 Çıkarım Kodu (`src/yolov8_npu.py`)**

Aşağıdaki script; resmi `rknn-toolkit-lite2` motorunu kullanarak görseli NPU'ya besler, 3 çekirdeği tam kapasite çalıştırır ve nesneleri tespit edip kutu içine alır:

```python
import cv2
import numpy as np
import time
from rknnlite.api import RKNNLite

# COCO Veri Seti 80 Sınıf Etiketi
CLASSES = [
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

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114)):
    """Görseli en-boy oranını bozmadan 640x640 boyutuna padding ile sığdırır."""
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

def postprocess(predictions, conf_thres=0.4, iou_thres=0.45):
    """YOLOv8 çıktı matrisini (1, 84, 8400) işler ve NMS uygular."""
    preds = np.squeeze(predictions[0]).T  # (8400, 84)
    boxes = preds[:, :4]
    scores = preds[:, 4:]
    class_ids = np.argmax(scores, axis=1)
    confidences = np.max(scores, axis=1)

    mask = confidences > conf_thres
    boxes = boxes[mask]
    confidences = confidences[mask]
    class_ids = class_ids[mask]

    if len(boxes) == 0:
        return [], [], []

    # Format dönüşümü: cx, cy, w, h -> x1, y1, w, h
    x = boxes[:, 0] - boxes[:, 2] / 2
    y = boxes[:, 1] - boxes[:, 3] / 2
    w = boxes[:, 2]
    h = boxes[:, 3]
    boxes_for_nms = np.stack([x, y, w, h], axis=1).tolist()

    indices = cv2.dnn.NMSBoxes(boxes_for_nms, confidences.tolist(), conf_thres, iou_thres)
    
    final_boxes, final_confs, final_classes = [], [], []
    for i in indices:
        idx = i if isinstance(i, int) else i[0]
        final_boxes.append(boxes_for_nms[idx])
        final_confs.append(confidences[idx])
        final_classes.append(class_ids[idx])

    return final_boxes, final_confs, final_classes

def main():
    MODEL_PATH = "models/yolov8n_rk3588.rknn"
    IMAGE_PATH = "data/bus.jpg"

    # 1. RKNN Motorunu Başlat ve 3 NPU Çekirdeğini de Ata
    print("--> NPU Motoru yükleniyor...")
    rknn = RKNNLite()
    if rknn.load_rknn(MODEL_PATH) != 0:
        print(f"Model yüklenemedi: {MODEL_PATH}")
        return

    # RK3588'in 3 NPU çekirdeğini birden (6 TOPS) devreye sok
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    if ret != 0:
        print("NPU Runtime başlatılamadı!")
        return

    # 2. Görseli Yükle ve Ön İşleme (OpenCV BGR formatını modelin beklediği RGB formatına çevirin)
    orig_img = cv2.imread(IMAGE_PATH)
    img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
    img_padded, scale, (dw, dh) = letterbox(img_rgb, (640, 640))
    input_data = np.expand_dims(img_padded, axis=0)

    # 3. NPU Çıkarımını Gerçekleştir (Süre Ölçümü)
    print("--> NPU Çıkarımı yapılıyor...")
    start_time = time.perf_counter()
    outputs = rknn.inference(inputs=[input_data])
    infer_time = (time.perf_counter() - start_time) * 1000

    print(f"[NPU PERFORMANSI] Çıkarım Süresi: {infer_time:.2f} ms (~{1000/infer_time:.1f} FPS)")

    # 4. Çıktıyı İşle ve Çiz
    boxes, confs, class_ids = postprocess(outputs)
    
    for box, conf, cls_id in zip(boxes, confs, class_ids):
        x, y, w, h = box
        # Orijinal görsel koordinatlarına geri dönüştür
        orig_x = int((x - dw) / scale)
        orig_y = int((y - dh) / scale)
        orig_w = int(w / scale)
        orig_h = int(h / scale)

        label = f"{CLASSES[cls_id]}: {conf:.2f}"
        cv2.rectangle(orig_img, (orig_x, orig_y), (orig_x + orig_w, orig_y + orig_h), (0, 255, 0), 2)
        cv2.putText(orig_img, label, (orig_x, max(20, orig_y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        print(f"Tespit: {label}")

    output_path = "data/bus_detected.jpg"
    cv2.imwrite(output_path, orig_img)
    print(f"[SONUÇ] Tespit edilen görsel '{output_path}' olarak kaydedildi.")

    rknn.release()

if __name__ == "__main__":
    main()
```

---

## **5. Adım 4: Scripti Çalıştırma ve Çıkarım Performansı**

```bash
python3 src/yolov8_npu.py
```

### **Konsol Çıktısı:**
```text
--> NPU Motoru yükleniyor...
--> NPU Çıkarımı yapılıyor...
[NPU PERFORMANSI] Çıkarım Süresi: 13.84 ms (~72.3 FPS)
Tespit: bus: 0.88
Tespit: person: 0.83
Tespit: person: 0.79
Tespit: person: 0.75
[SONUÇ] Tespit edilen görsel 'data/bus_detected.jpg' olarak kaydedildi.
```

---

## **6. Performans Kıyaslaması: CPU vs 6 TOPS NPU**

| Yöntem / Donanım | Gecikme Süresi (Latency) | Kare Hızı (FPS) | CPU Çekirdek Yükü |
| :--- | :--- | :--- | :--- |
| **Cortex-A76 (CPU Tek Çekirdek - ONNX)** | ~280 ms | ~3.5 FPS | %100 (Tek Çekirdek Doygun) |
| **Cortex-A76 (CPU 4 Çekirdek Multi-Thread)** | ~95 ms | ~10.5 FPS | %400 (Tüm Performans Çekirdekleri Doygun) |
| **RK3588 3-Çekirdek NPU (rknn-lite2)** | **~13.8 ms** | **~72.3 FPS** | **<%15 (İşlemci Tamamen Boşta)** |

> [!TIP]
> NPU kullanımının en büyük avantajı yalnızca hız değildir. Çıkarım yaparken CPU çekirdekleri boş kaldığı için kart üzerinde aynı anda web sunucusu, veritabanı veya kontrol algoritmaları sıfır takılma ile çalışmaya devam eder.

---

## **7. Sık Karşılaşılan Hatalar ve Teşhis Tablosu**

| Hata Mesajı / Belirti | Kök Neden | Kesin Çözüm |
| :--- | :--- | :--- |
| `AssertionError: The shape of input is invalid` | Tensör boyutu hatası. RKNN-Lite varsayılan olarak **NHWC** `(1, 640, 640, 3)` bekler; PyTorch alışkanlığıyla `(1, 3, 640, 640)` NCHW formatı verildi. | `np.transpose(2, 0, 1)` yapmayın! Giriş görüntüsünü `(640, 640, 3)` olarak tutup sadece `np.expand_dims(img, axis=0)` uygulayın. |
| `AttributeError: 'NoneType' object has no attribute 'shape'` | `cv2.imread()` hedef görseli bulamadı. | `data/bus.jpg` dosya yolunu kontrol edin veya mutlak (absolute) yol verin. |
| `Build failed: dataset is required when do_quantization=True` | INT8 kuantizasyon kalibrasyon veri seti (`dataset.txt`) olmadan derlenmeye çalışıldı. | Kalibrasyon veri setiniz yoksa scriptteki gibi `do_quantization=False` (FP16 modu) ile derleyin. |
| Çıktıda kutular alakasız yerlere çiziliyor | Giriş görüntüsü BGR bırakıldı veya model derlenirken `mean_values`/`std_values` normalizasyonu yanlış verildi. | `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)` yapıldığından ve derleme scriptinde `mean=0, std=255` verildiğinden emin olun. |

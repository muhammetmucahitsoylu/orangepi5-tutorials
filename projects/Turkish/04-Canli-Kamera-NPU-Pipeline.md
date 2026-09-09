# **Orange Pi 5 (RK3588S) Canlı Kamera ve NPU Bilgisayarlı Görü Pipeline Rehberi**

Bu rehber; Orange Pi 5'in **6 TOPS NPU (Sinirsel İşlem Birimi)** donanımını kullanarak bir **USB Web Kamerası** veya **RTSP IP Kamera** akışından canlı görüntü alan, sıfır gecikme (zero-latency) için çoklu iş parçacığı (multi-threading) mimarisiyle kareleri yakalayan, **YOLOv8** ile nesne tespiti yapan ve sonuçları gerçek zamanlı telemetri verileriyle (FPS, NPU sıcaklığı, gecikme) tarayıcıya yansıtan uçtan uca bir görüntü işleme pipeline'ı kurmayı anlatır.

---

## **1. Sistem Mimarisi: Neden Sıradan Bir Döngü Yetersizdir?**

Bilgisayarlı görü projelerinde yeni başlayanların en sık yaptığı hata; kamera okuma, model çıkarımı ve görüntü göstermeyi tek bir `while True` döngüsünde ardışık çalıştırmaktır.

```
Hatalı (Ardışık) Tasarım:
[ Kamera Oku (30ms) ] ──> [ NPU Çıkarımı (15ms) ] ──> [ Çizim & Stream (10ms) ] ──> TOPLAM: 55ms (~18 FPS)
*Kamera donanım tamponu (buffer) dolar, video 2-3 saniye geriden gelmeye başlar (RTSP / UVC Lag)!
```

Orange Pi 5 üzerinde kuracağımız profesyonel **Asenkron Pipeline** mimarisi:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Kamera Girişi (USB / RTSP)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  İş Parçacığı 1: Kamera Okuyucu (Dedicated Camera Thread)             │
│  - Donanım tamponunu sürekli temizler (cap.grab)                       │
│  - Sadece en güncel kareyi (latest_frame) RAM'de tutar (Sıfır Gecikme) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (En güncel kare)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  İş Parçacığı 2: NPU YOLOv8 Çıkarım Motoru (RKNN-Lite2)                │
│  - 3 Çekirdekli NPU (Core 0, 1, 2) paralel donanım hızlandırma         │
│  - Bounding box ve sınıf etiketleme                                   │
│  - Anlık FPS ve SoC Sıcaklık Telemetrisi                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Web Dağıtımı: MJPEG HTTP Sunucusu (Flask / Threaded Stream)           │
│  - Herhangi bir istemci (Telefon, PC, Tablet) kurulumsuz tarayıcıdan izler│
│  - `http://ORANGE_PI_IP:5000` üzerinden sıfır istemci bağımlılığı      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **2. Kritik Donanım ve Sürücü Detayları**

1. **Headless (Ekransız) Çökme Koruması:** Orange Pi 5 sunucu olarak ekransız çalışırken `cv2.imshow()` çağrılırsa kod şu hatayla derhal çöker:
   ```
   qt.qpa.plugin: Could not find the platform plugin "xcb" ...
   ```
   Bu yüzden görüntü doğrudan Web MJPEG akışına yönlendirilir; X11 veya monitör gerekmez.
2. **USB UVC Kameralarda MJPEG Format Zorunluluğu:** Standart USB kameralar Linux altında varsayılan olarak `YUYV` ham piksel formatında açılır ve USB 2.0 bant genişliği yüzünden 5 FPS'e kilitlenir. OpenCV üzerinde FourCC `MJPG` olarak zorlanmalıdır.
3. **RTSP IP Kamera Akış Gecikmesi:** FFmpeg varsayılan olarak 30-50 kareyi belleğe tamponlar. Bu durum 2-3 saniye yayın gecikmesi yaratır. Çözüm, low-delay bayrakları tanımlamaktır.
4. **Büyük Tuzak: USB UVC vs. MIPI CSI (Rockchip RKAIQ ISP Mayın Tarlası):**
   * **USB Web Kameraları (Tak-Çalıştır):** Dahili ISP barındırır, doğrudan donanımsal MJPEG/YUYV çıktısı verir ve `cv2.VideoCapture(0)` ile sıfır konfigürasyonla çalışır.
   * **MIPI CSI Kameralar (OV13850, IMX415 vb.):** Orange Pi 5 üzerindeki 3 adet MIPI CSI portu ham Bayer (RAW) piksel verisi alır. Bu veriyi işlemek, otomatik pozlama (AE), beyaz dengesi (AWB) ve netleme (AF) sağlamak için Rockchip'in kapalı kaynak **RKAIQ 3A Server (`librkaiq.so` / `rkaiq_3A_server`)** arka plan servisi zorunludur!
   * *Neden Tak-Çalıştır Değildir?* RKAIQ servisi başlatılmadan `/dev/video11` doğrudan `cv2.VideoCapture` ile açılırsa görüntü zifiri karanlık veya donmuş kalır. MIPI CSI kullanırken OpenCV'ye özel GStreamer pipeline'ı (`v4l2src device=/dev/video11 ! video/x-raw,format=NV12 ... ! appsink`) tanımlanmalıdır. Hızlı ve sorunsuz geliştirme için bu rehberde USB UVC / RTSP standartlaştırılmıştır.

---

## **3. Adım 1: Gerekli Paketlerin Kurulması**

Orange Pi 5 terminalinde:

```bash
# Sistem video ve derleme araçları
sudo apt update
sudo apt install -y v4l-utils python3-pip python3-opencv

# Python web ve görüntü kütüphaneleri
pip3 install flask numpy pillow
```

### **Kamera Bağlantısını Doğrulama:**
USB kamera takılıysa `/dev/video*` aygıtlarını listeleyin:
```bash
v4l2-ctl --list-devices
```
*Çıktıda kameranızın `/dev/video0` veya `/dev/video1` olarak tanındığını doğrulayın.*

---

## **4. Adım 2: YOLOv8 RKNN Modelini Hazırlama**

03. Projede derlediğiniz `yolov8n_rk3588.rknn` model dosyasını veya resmi depodan sağlanan modeli kullanacağız:

```bash
mkdir -p ~/projects/camera-pipeline && cd ~/projects/camera-pipeline

# 1. Seçenek (Önerilen): 03. Projede ürettiğiniz modeli kopyalayın:
if [ -f ~/projects/ilk-projem/models/yolov8n_rk3588.rknn ]; then
    cp ~/projects/ilk-projem/models/yolov8n_rk3588.rknn ./yolov8n.rknn
    echo "Model 03. Projeden başarıyla kopyalandı."
fi

# 2. Seçenek: Eğer model henüz elinizde yoksa, airockchip rknn_model_zoo resmi deposundan çekin:
# git clone --depth 1 https://github.com/airockchip/rknn_model_zoo.git
# cp rknn_model_zoo/examples/yolov8/model/RK3588/yolov8n.rknn ./yolov8n.rknn
```

---

## **5. Adım 3: Asenkron Görüntü İşleme Pipeline Kodu (`pipeline.py`)**

Aşağıdaki script; bağımsız kamera okuma iş parçacığını, RKNN NPU çıkarım döngüsünü ve Flask MJPEG web sunucusunu tek bir yüksek performanslı mimaride birleştirir:

```python
import os
import cv2
import time
import threading
import numpy as np
from flask import Flask, Response, render_template_string
from rknnlite.api import RKNNLite

# --- AYARLAR ---
MODEL_PATH = "yolov8n.rknn"
CAMERA_SOURCE = 0          # USB kamera için 0, RTSP kamera için: "rtsp://admin:pass@192.168.1.50:554/stream"
INPUT_SIZE = 640
OBJ_THRESH = 0.45
NMS_THRESH = 0.50

# COCO 80 Sınıf Listesi
CLASSES = ("person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
           "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
           "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
           "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
           "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
           "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
           "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
           "sofa", "pottedplant", "bed", "diningtable", "toilet", "vtvmonitor", "laptop", "mouse",
           "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
           "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush")

# Renk paleti
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# Paylaşılan küresel durum değişkenleri
latest_raw_frame = None
latest_processed_frame = None
frame_lock = threading.Lock()
is_running = True
telemetry = {"fps": 0.0, "latency": 0.0, "temp": 0.0, "objects": 0}

# --- YARDIMCI FONKSİYONLAR ---
def get_soc_temp():
    """Orange Pi 5 dahili sıcaklık sensörünü okur"""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

def filter_boxes(boxes, box_confidences, box_class_probs):
    boxes = boxes.reshape(-1, 4)
    box_confidences = box_confidences.reshape(-1)
    box_class_probs = box_class_probs.reshape(-1, box_class_probs.shape[-1])

    _cls = np.argmax(box_class_probs, axis=-1)
    _cls_scores = np.max(box_class_probs, axis=-1)
    _scores = box_confidences * _cls_scores
    _mask = _scores > OBJ_THRESH

    boxes = boxes[_mask]
    classes = _cls[_mask]
    scores = _scores[_mask]
    return boxes, classes, scores

def nms_boxes(boxes, scores):
    x = boxes[:, 0]
    y = boxes[:, 1]
    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]

    areas = w * h
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x[i], x[order[1:]])
        yy1 = np.maximum(y[i], y[order[1:]])
        xx2 = np.minimum(x[i] + w[i], x[order[1:]] + w[order[1:]])
        yy2 = np.minimum(y[i] + h[i], y[order[1:]] + h[order[1:]])

        w_inter = np.maximum(0.0, xx2 - xx1 + 1)
        h_inter = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w_inter * h_inter

        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= NMS_THRESH)[0]
        order = order[inds + 1]

    return keep

# --- 1. KAMERA İŞ PARÇACIĞI (SIFIR GECİKME) ---
def camera_capture_thread():
    global latest_raw_frame, is_running
    
    # RTSP düşük gecikme parametreleri
    if isinstance(CAMERA_SOURCE, str) and CAMERA_SOURCE.startswith("rtsp"):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
        cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(CAMERA_SOURCE)
        # USB kamera için MJPEG formatını zorla
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("[-] Hata: Kamera akışı başlatılamadı!")
        is_running = False
        return

    print("[+] Kamera akışı başarıyla bağlandı.")
    while is_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        
        with frame_lock:
            latest_raw_frame = frame

    cap.release()

# --- 2. NPU ÇIKARIM VE İŞLEME DÖNGÜSÜ ---
def npu_inference_thread():
    global latest_raw_frame, latest_processed_frame, is_running, telemetry
    
    # RKNN Başlat
    rknn = RKNNLite()
    if rknn.load_rknn(MODEL_PATH) != 0:
        print("[-] Model yüklenemedi!")
        is_running = False
        return

    # 3 Çekirdeği (Core 0, 1, 2) aktif et
    if rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2) != 0:
        print("[-] NPU Runtime başlatılamadı!")
        is_running = False
        return

    print("[+] NPU 3 Çekirdekli Motor Aktif. Çıkarım başladı...")
    
    fps_counter = 0
    fps_timer = time.time()

    while is_running:
        frame = None
        with frame_lock:
            if latest_raw_frame is not None:
                frame = latest_raw_frame.copy()

        if frame is None:
            time.sleep(0.005)
            continue

        start_t = time.time()
        orig_h, orig_w = frame.shape[:2]

        # NPU Giriş Boyutlandırması (640x640) ve BGR -> RGB Dönüşümü
        input_img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = np.expand_dims(input_img, axis=0)

        # NPU Çıkarımı
        outputs = rknn.rknn_run(inputs=[input_img])

        # YOLOv8 Çıktı Post-Processing
        # RKNN YOLOv8 çıktısı genelde (1, 84, 8400) veya 3 dallıdır
        # Kutu ve sınıf ayrıştırma
        pred = np.squeeze(outputs[0])
        pred = pred.transpose() # (8400, 84)

        boxes = pred[:, :4]
        class_scores = pred[:, 4:]

        # Koordinat dönüştürme (center_x, center_y, w, h -> x1, y1, x2, y2)
        x1 = (boxes[:, 0] - boxes[:, 2] / 2) * (orig_w / INPUT_SIZE)
        y1 = (boxes[:, 1] - boxes[:, 3] / 2) * (orig_h / INPUT_SIZE)
        x2 = (boxes[:, 0] + boxes[:, 2] / 2) * (orig_w / INPUT_SIZE)
        y2 = (boxes[:, 1] + boxes[:, 3] / 2) * (orig_h / INPUT_SIZE)

        formatted_boxes = np.stack([x1, y1, x2, y2], axis=-1)
        classes = np.argmax(class_scores, axis=-1)
        scores = np.max(class_scores, axis=-1)

        mask = scores > OBJ_THRESH
        valid_boxes = formatted_boxes[mask]
        valid_scores = scores[mask]
        valid_classes = classes[mask]

        indices = cv2.dnn.NMSBoxes(
            valid_boxes.tolist(), 
            valid_scores.tolist(), 
            OBJ_THRESH, 
            NMS_THRESH
        )

        detected_count = 0
        if len(indices) > 0:
            for idx in indices.flatten():
                bx = valid_boxes[idx].astype(int)
                cls_id = valid_classes[idx]
                score = valid_scores[idx]
                label = f"{CLASSES[cls_id]}: {score:.2f}"
                color = COLORS[cls_id]

                cv2.rectangle(frame, (bx[0], bx[1]), (bx[2], bx[3]), color, 2)
                cv2.putText(frame, label, (bx[0], max(20, bx[1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                detected_count += 1

        latency = (time.time() - start_t) * 1000.0

        # Telemetri Hesaplama
        fps_counter += 1
        if time.time() - fps_timer >= 1.0:
            telemetry["fps"] = fps_counter / (time.time() - fps_timer)
            telemetry["latency"] = latency
            telemetry["temp"] = get_soc_temp()
            telemetry["objects"] = detected_count
            fps_counter = 0
            fps_timer = time.time()

        # Telemetriyi Kare Üzerine Çiz
        overlay_text = f"FPS: {telemetry['fps']:.1f} | NPU Latency: {telemetry['latency']:.1f}ms | SoC: {telemetry['temp']:.1f}C | Objects: {detected_count}"
        cv2.rectangle(frame, (0, 0), (orig_w, 35), (20, 20, 20), -1)
        cv2.putText(frame, overlay_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2, cv2.LINE_AA)

        with frame_lock:
            latest_processed_frame = frame

    rknn.release()

# --- 3. FLASK WEB SUNUCUSU VE CANLI YAYIN ---
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Orange Pi 5 (RK3588S) NPU Vision Stream</title>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; margin: 0; padding: 20px; }
        h1 { color: #38bdf8; margin-bottom: 5px; }
        .stream-card { display: inline-block; background: #1e293b; padding: 15px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); margin-top: 15px; }
        img { max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #334155; }
        .meta { margin-top: 10px; font-size: 14px; color: #94a3b8; }
    </style>
</head>
<body>
    <h1>🍊 Orange Pi 5 Real-Time NPU Vision Pipeline</h1>
    <p>6 TOPS NPU + YOLOv8 + Multi-Threaded Low-Latency Capture</p>
    <div class="stream-card">
        <img src="/video_feed" alt="Canlı Akış">
        <div class="meta">Canlı MJPEG Akışı | Doğrudan NPU Donanım Hızlandırmalı Çıkarım</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

def generate_stream():
    while is_running:
        frame = None
        with frame_lock:
            if latest_processed_frame is not None:
                frame = latest_processed_frame.copy()

        if frame is None:
            time.sleep(0.01)
            continue

        # JPEG formatında sıkıştır
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    t_cam = threading.Thread(target=camera_capture_thread, daemon=True)
    t_npu = threading.Thread(target=npu_inference_thread, daemon=True)

    t_cam.start()
    t_npu.start()

    print("[*] Web Sunucusu Başlatılıyor: http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
```

---

## **6. Adım 4: Canlı Akışı Başlatma ve Doğrulama**

```bash
cd ~/projects/camera-pipeline
python3 pipeline.py
```

### **Yayını İzleme:**
Aynı ağdaki herhangi bir bilgisayar veya telefonun tarayıcısından:
```text
http://ORANGE_PI_IP:5000
```
adresine gidin.
* Ekranda kameranızın canlı görüntüsü, tespit edilen nesnelerin sınır çizgileri (bounding boxes) ve üst bantta anlık **FPS (30-60 FPS)**, **NPU gecikme süresi (12-18 ms)** ve **SoC sıcaklığı** canlı olarak akacaktır.

---

## **7. Adım 5: 7/24 Arka Planda Çalışan `systemd` Servisi Yapma**

Orange Pi 5 her açıldığında bilgisayarlı görü sunucusunun otomatik ayağa kalkması için:

```bash
sudo tee /etc/systemd/system/npu-camera.service <<EOF
[Unit]
Description=Orange Pi 5 Real-Time NPU Camera Vision Pipeline
After=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=/home/orangepi/projects/camera-pipeline
ExecStart=/usr/bin/python3 /home/orangepi/projects/camera-pipeline/pipeline.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Servisi etkinleştirin ve başlatın
sudo systemctl daemon-reload
sudo systemctl enable npu-camera.service
sudo systemctl start npu-camera.service
```

Durum kontrolü:
```bash
sudo systemctl status npu-camera.service
```

---

## **8. Sık Karşılaşılan Sorunlar ve Çözümleri**

| Sorun | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| **Kamera 5 FPS'te takılıyor** | USB kamera varsayılan YUYV modunda açılıyor. | Kodda `cv2.CAP_PROP_FOURCC = MJPG` ayarlandığından emin olun. |
| **RTSP yayını 3 saniye gecikmeli geliyor** | FFmpeg kare tamponu (buffer) biriktiriyor. | `OPENCV_FFMPEG_CAPTURE_OPTIONS` içine `nobuffer` ve `low_delay` bayraklarını ekleyin. |
| **`cv2.error: (-215:Assertion failed)`** | Model girdi boyutu ile yeniden boyutlandırılan kare uyuşmuyor. | Resmin `(640, 640)` boyutuna indirgendiğini ve kanal sayısının 3 olduğunu kontrol edin. |
| **NPU Core 0/1/2 meşgul hatası** | Başka bir süreç (örn. arka planda kalan Python) NPU'yu kilitledi. | `sudo fuser -v /dev/rknpu*` ile işlemi bulun ve `kill -9` ile sonlandırın. |

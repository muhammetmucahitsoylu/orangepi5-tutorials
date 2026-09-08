# **Orange Pi 5 (RK3588S) First AI Project and YOLOv8 NPU Inference Guide**

This guide covers building a complete end-to-end Edge AI vision application on the Orange Pi 5, running the **YOLOv8** object detection model at **70+ FPS** using the 6 TOPS 3-core Neural Processing Unit (NPU).

---

## **1. Edge AI Architecture & Workflow**

The golden rule of embedded edge machine learning is: **"Train & Convert on PC, Infer on Edge"**.

```
[ Developer Host (PC / Laptop / WSL2) ]
  PyTorch Model (.pt) ──(export)──> ONNX (.onnx) ──(rknn-toolkit2 compiler)──> RKNN Model (.rknn)
                                                                                     │
                                                                                     ▼ (SCP / Network Transfer)
[ Orange Pi 5 (RK3588S) ]
  Camera / Video Stream ──> rknn-toolkit-lite2 (3-Core NPU) ──> 70+ FPS Real-Time Inference
```

---

## **2. Step 1: Model Preparation and RKNN Compilation on Host PC**

> **Note:** Quantization (INT8/FP16) and model graph compilation require high host memory and x86_64 toolchains. Perform this step on your development PC (Linux or WSL2). If you already have a compiled `.rknn` model, skip directly to Step 2.

### **1. Export YOLOv8 to ONNX on Host PC:**
```bash
pip install ultralytics onnx

# Export YOLOv8 nano model to ONNX (opset=12 is most stable for RKNN compilation):
yolo export model=yolov8n.pt format=onnx imgsz=640 opset=12
```

### **2. Convert ONNX to RKNN Format Script (`convert_to_rknn.py`):**
```python
from rknn.api import RKNN

# 1. Initialize RKNN instance
rknn = RKNN(verbose=True)

# 2. Configure model for RK3588
# YOLO normalization: pixel values 0-255 -> mean=0, std=255
rknn.config(
    mean_values=[[0, 0, 0]],
    std_values=[[255, 255, 255]],
    target_platform='rk3588'
)

# 3. Load ONNX graph
print("--> Loading ONNX model...")
ret = rknn.load_onnx(model='yolov8n.onnx')
if ret != 0:
    print("Failed to load ONNX model!")
    exit(ret)

# 4. Build model (FP16 for quick verification, INT8 for max throughput)
print("--> Compiling NPU model for RK3588...")
ret = rknn.build(do_quantization=False)  # FP16 precision
if ret != 0:
    print("Compilation failed!")
    exit(ret)

# 5. Export .rknn model
rknn.export_rknn('yolov8n_rk3588.rknn')
print("[SUCCESS] Model exported as yolov8n_rk3588.rknn")
rknn.release()
```

Transfer the resulting `yolov8n_rk3588.rknn` to the Orange Pi 5 via `scp`:
```bash
scp yolov8n_rk3588.rknn user@ORANGE_PI_IP:~/projects/ilk-projem/models/
```

---

## **3. Step 2: Project Setup on Orange Pi 5**

Inside your Orange Pi 5 terminal (or VS Code Remote - SSH session):

```bash
cd ~/projects/ilk-projem
source venv/bin/activate

# Install computer vision prerequisites
pip install numpy opencv-python pillow
```

Download a test sample image:
```bash
mkdir -p data models
wget -O data/bus.jpg https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg
```

---

## **4. Step 3: NPU-Accelerated YOLOv8 Inference Script (`src/yolov8_npu.py`)**

The following script loads the model onto all 3 NPU cores via `rknn-toolkit-lite2`, executes hardware inference, and renders bounding boxes:

```python
import cv2
import numpy as np
import time
from rknnlite.api import RKNNLite

# COCO Dataset 80 Class Labels
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
    """Resize image preserving aspect ratio with symmetric border padding."""
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
    """Process YOLOv8 output matrix (1, 84, 8400) and run Non-Maximum Suppression."""
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

    # Coordinate transform: cx, cy, w, h -> x1, y1, w, h
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

    # 1. Initialize RKNN engine and bind all 3 NPU cores
    print("--> Loading NPU engine...")
    rknn = RKNNLite()
    if rknn.load_rknn(MODEL_PATH) != 0:
        print(f"Failed to load model: {MODEL_PATH}")
        return

    # Activate full 6 TOPS across Core0, Core1, and Core2
    ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)
    if ret != 0:
        print("Failed to initialize NPU runtime!")
        return

    # 2. Image Loading and Preprocessing (Convert OpenCV BGR to RGB expected by model)
    orig_img = cv2.imread(IMAGE_PATH)
    img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
    img_padded, scale, (dw, dh) = letterbox(img_rgb, (640, 640))
    input_data = np.expand_dims(img_padded, axis=0)

    # 3. Hardware NPU Inference & Timing
    print("--> Performing NPU inference...")
    start_time = time.perf_counter()
    outputs = rknn.inference(inputs=[input_data])
    infer_time = (time.perf_counter() - start_time) * 1000

    print(f"[NPU PERFORMANCE] Latency: {infer_time:.2f} ms (~{1000/infer_time:.1f} FPS)")

    # 4. Post-processing and Annotation
    boxes, confs, class_ids = postprocess(outputs)
    
    for box, conf, cls_id in zip(boxes, confs, class_ids):
        x, y, w, h = box
        # Scale back to original image coordinates
        orig_x = int((x - dw) / scale)
        orig_y = int((y - dh) / scale)
        orig_w = int(w / scale)
        orig_h = int(h / scale)

        label = f"{CLASSES[cls_id]}: {conf:.2f}"
        cv2.rectangle(orig_img, (orig_x, orig_y), (orig_x + orig_w, orig_y + orig_h), (0, 255, 0), 2)
        cv2.putText(orig_img, label, (orig_x, max(20, orig_y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        print(f"Detected: {label}")

    output_path = "data/bus_detected.jpg"
    cv2.imwrite(output_path, orig_img)
    print(f"[RESULT] Annotated image saved to '{output_path}'")

    rknn.release()

if __name__ == "__main__":
    main()
```

---

## **5. Step 4: Execution & Verification**

```bash
python3 src/yolov8_npu.py
```

### **Sample Output:**
```text
--> Loading NPU engine...
--> Performing NPU inference...
[NPU PERFORMANCE] Latency: 13.84 ms (~72.3 FPS)
Detected: bus: 0.88
Detected: person: 0.83
Detected: person: 0.79
Detected: person: 0.75
[RESULT] Annotated image saved to 'data/bus_detected.jpg'
```

---

## **6. Performance Comparison: CPU vs 6 TOPS NPU**

| Runtime / Target | Latency | Throughput (FPS) | CPU Core Utilization |
| :--- | :--- | :--- | :--- |
| **Cortex-A76 (CPU Single-Core - ONNX)** | ~280 ms | ~3.5 FPS | 100% (Single Core Saturated) |
| **Cortex-A76 (CPU 4-Core Multi-Thread)** | ~95 ms | ~10.5 FPS | 400% (All Big Cores Saturated) |
| **RK3588 3-Core NPU (rknn-lite2)** | **~13.8 ms** | **~72.3 FPS** | **< 15% (Host CPU Idle)** |

> [!TIP]
> Offloading computer vision tasks to the NPU leaves the 8 CPU cores free to handle networking, web sockets, database transactions, and robotics PID loops with zero jitter or frame drops.

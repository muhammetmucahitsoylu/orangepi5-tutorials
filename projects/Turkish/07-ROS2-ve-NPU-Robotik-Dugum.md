# **Orange Pi 5 (RK3588S) ROS 2 Kurulumu ve NPU Robotik Düğüm Rehberi**

Bu rehber; Orange Pi 5 (Rockchip RK3588S) üzerine endüstri standardı robotik işletim sistemi **ROS 2 (Robot Operating System - Humble Hawksbill)** kurulumunu, DDS haberleşme mimarisi optimizasyonunu ve **6 TOPS NPU** donanımını kullanarak kamera görüntüsünden nesne tespit edip robotun hareket motorlarına yönlendiren **NPU Algılama Düğümü (Perception Node)** geliştirmeyi anlatır.

---

## **1. Neden Orange Pi 5 ve ROS 2?**

Modern otonom mobil robotlarda (AMR), insansız hava araçlarında (İHA) ve servis robotlarında sensör verilerinin işlenmesi devasa işlem gücü gerektirir:
* **Geleneksel Darboğaz:** Raspberry Pi 4 gibi kartlarda görüntü işleme CPU'yu %100 yükler ve robotun navigasyon algoritmaları (Nav2, SLAM) kilitlenir.
* **Orange Pi 5 Avantajı:** 8 çekirdekli CPU navigasyon ve motor kontrolünü yürütürken; **3 çekirdekli 6 TOPS NPU**, CPU'ya sıfır yük bindirerek 70+ FPS yapay zeka çıkarımı yapar. ROS 2 topic mimarisi ile bu veriler mikro saniyeler içinde navigasyon katmanına iletilir.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Orange Pi 5 (RK3588S) ROS 2 Mimarisi                 │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────┴────────────────────────────────────┐
│  Kamera / Sensör Düğümü (Camera Node)                                  │
│  - USB / CSI / IP kameradan görüntü yakalar                            │
│  - Topic: `/camera/image_raw` [sensor_msgs/msg/Image]                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (DDS Paylaşımlı Bellek)
┌───────────────────────────────────┴────────────────────────────────────┐
│  NPU Algılama Düğümü (Perception Node - RKNN YOLOv8)                   │
│  - 3 Çekirdekli NPU'da çıkarım yapar (CPU Yükü: ~%2)                   │
│  - Nesne koordinatlarını hesaplar                                      │
│  - Topic: `/detected_objects` [std_msgs/msg/String (JSON Coordinates)] │
│  - Topic: `/camera/annotated_image` [sensor_msgs/msg/Image]            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────┴────────────────────────────────────┐
│  Otonom Karar & Motor Kontrol Düğümü (Nav2 / Motor Node)               │
│  - Nesneyi takip eder veya engelden kaçar                              │
│  - Topic: `/cmd_vel` [geometry_msgs/msg/Twist] -> Motor Sürücüler      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **2. Kritik Robotik Mimarisi: ROS 2 DDS & Bellek Ayarları**

ARM64 tek kart bilgisayarlarda ROS 2 çalıştırırken karşılaşılan en büyük tuzaklar:
1. **Multicast & Ağ Kilitlenmesi:** ROS 2'nin varsayılan DDS katmanı (FastDDS / CycloneDDS), yerel ağdaki tüm ROS 2 cihazlarıyla otomatik eşleşmek için multicast paketleri yollar. Ev veya okul Wi-Fi ağında yüzlerce paket döngüye girip CPU'yu boğabilir. Çözüm: Kendi robotunuza özel bir `ROS_DOMAIN_ID` atamaktır.
2. **Locale (Karakter Kodlama) Hatası:** ROS 2 Python araçları sistem yereli UTF-8 olmadığında `UnicodeEncodeError` ile çöker.
3. **Masaüstü (Desktop) vs Sunucu (Base) Kurulumu:** Ekransız çalışan bir robota devasa GUI paketlerini (`ros-humble-desktop`) kurmak 3GB+ boşuna RAM ve NVMe harcar. Robotun kendisine `ros-humble-ros-base` kurulmalıdır.

---

## **3. Adım 1: UTF-8 Doğrulama ve ROS 2 Apt Deposu Kurulumu**

Orange Pi 5 terminalinde:

```bash
# 1. UTF-8 Yerelini Doğrulayın ve Ayarlayın:
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Ubuntu Universe Deposunu Etkinleştirin:
sudo apt install -y software-properties-common curl gnupg lsb-release
sudo add-apt-repository universe

# 3. Resmi ROS 2 GPG Anahtarını Ekleyin:
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 4. ROS 2 Apt Kaynağını Listeye Ekleyin (ARM64 Resmi Depo):
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

---

## **4. Adım 2: ROS 2 Humble / Jazzy ve Geliştirici Araçlarının Kurulumu**

> [!NOTE]
> **Ubuntu Sürüm Uyumluluğu:**
> * **Ubuntu 22.04 LTS (Jammy):** Standart LTS sürümü **`ros-humble`** paketleridir.
> * **Ubuntu 24.04 LTS (Noble):** 24.04 üzerinde ROS 2 kuruyorsanız `humble` yerine **`jazzy`** (ROS 2 Jazzy Jalisco) paketlerini seçin (`ros-jazzy-ros-base`, `ros-jazzy-cv-bridge`, vb.).

```bash
# Paket listesini güncelleyin
sudo apt update

# Ubuntu sürümünüze göre dağıtım adını belirleyin:
# Ubuntu 24.04 (Noble) -> jazzy | Ubuntu 22.04 (Jammy) -> humble
ROS_DISTRO=$(source /etc/os-release && [ "$UBUNTU_CODENAME" = "noble" ] && echo "jazzy" || echo "humble")
echo "Seçilen ROS 2 Dağıtımı: $ROS_DISTRO"

# Hafif ROS-Base ve geliştirici araçlarını kurun:
sudo apt install -y ros-${ROS_DISTRO}-ros-base \
                    ros-dev-tools \
                    python3-colcon-common-extensions \
                    python3-rosdep \
                    ros-${ROS_DISTRO}-cv-bridge \
                    ros-${ROS_DISTRO}-vision-msgs

# rosdep veritabanını başlatın:
sudo rosdep init 2>/dev/null || true
rosdep update
```

### **Kabuk Ortamı Yapılandırması (`~/.bashrc`):**
Her terminal açıldığında ROS 2 ortamının otomatik yüklenmesi ve çakışmaları önlemek için:
```bash
echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source /opt/ros/${ROS_DISTRO}/setup.bash
```

### **Doğrulama (Çekirdek İletişim Testi):**
```bash
ros2 topic list
```
*Hata vermeden `/parameter_events` ve `/rosout` topic'leri listeleniyorsa ROS 2 çekirdeği kusursuz çalışıyor demektir.*

---

## **5. Adım 3: Robotik Çalışma Alanı (Workspace) ve Paket Mimarisi**

Robot algılama düğümümüzü barındıracak standart ROS 2 çalışma alanını oluşturalım:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Python tabanlı ROS 2 algılama paketini oluşturun:
ros2 pkg create --build-type ament_python --node-name npu_detector opi5_perception
```

---

## **6. Adım 4: NPU Algılama Düğümü Kodu (`npu_detector.py`)**

Bu düğüm; kameradan gelen ham ROS görüntüsünü alır, OpenCV matrisine çevirir, RK3588 NPU üzerinde YOLOv8 ile işler ve tespit edilen nesnelerin sınıfı, güven skoru ve merkez koordinatlarını (X, Y) robotun navigasyon sistemi için yayınlar (publish eder):

Dosyayı düzenleyin:
`~/ros2_ws/src/opi5_perception/opi5_perception/npu_detector.py`

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import json
import os
from rknnlite.api import RKNNLite

MODEL_PATH = "/home/orangepi/projects/camera-pipeline/yolov8n.rknn"
INPUT_SIZE = 640
OBJ_THRESH = 0.45
NMS_THRESH = 0.50

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

class NPUPerceptionNode(Node):
    def __init__(self):
        super().__init__('npu_perception_node')
        
        self.bridge = CvBridge()
        
        # NPU RKNN Motorunu Başlat
        self.get_logger().info("[*] RKNN NPU Modeli yükleniyor...")
        self.rknn = RKNNLite()
        if self.rknn.load_rknn(MODEL_PATH) != 0:
            self.get_logger().error("[-] Hata: RKNN model dosyası yüklenemedi!")
            return
            
        # 3 Çekirdekli NPU'yu devreye sok
        if self.rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2) != 0:
            self.get_logger().error("[-] Hata: NPU runtime başlatılamadı!")
            return
        self.get_logger().info("[+] RK3588S 3 Çekirdekli NPU Başarıyla Başlatıldı!")

        # Abonelik (Subscriber): Kameradan gelen görüntüyü dinle
        self.sub_cam = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Yayıncılar (Publishers): Tespit koordinatları ve etiketli görüntü
        self.pub_detections = self.create_publisher(String, '/detected_objects', 10)
        self.pub_annotated = self.create_publisher(Image, '/camera/annotated_image', 10)

    def image_callback(self, msg):
        try:
            # ROS Image -> OpenCV BGR Matrisi
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"CvBridge hatası: {str(e)}")
            return

        orig_h, orig_w = frame.shape[:2]

        # Görüntüyü NPU formatına getir (640x640, RGB)
        input_img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = np.expand_dims(input_img, axis=0)

        # NPU Donanımsal Çıkarım
        outputs = self.rknn.rknn_run(inputs=[input_img])

        # YOLOv8 Çıktı Çözümleme
        pred = np.squeeze(outputs[0]).transpose()
        boxes = pred[:, :4]
        class_scores = pred[:, 4:]

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

        detections_payload = []

        if len(indices) > 0:
            for idx in indices.flatten():
                bx = valid_boxes[idx].astype(int)
                cls_id = int(valid_classes[idx])
                score = float(valid_scores[idx])
                cls_name = CLASSES[cls_id]

                # Robot navigasyonu için merkez koordinatları (Center X, Center Y)
                center_x = int((bx[0] + bx[2]) / 2)
                center_y = int((bx[1] + bx[3]) / 2)

                detections_payload.append({
                    "class": cls_name,
                    "confidence": round(score, 2),
                    "bbox": [int(bx[0]), int(bx[1]), int(bx[2]), int(bx[3])],
                    "center": [center_x, center_y]
                })

                # Görüntü üzerine kutu çiz
                cv2.rectangle(frame, (bx[0], bx[1]), (bx[2], bx[3]), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 4, (0, 0, 255), -1)
                cv2.putText(frame, f"{cls_name} {score:.2f}", (bx[0], max(20, bx[1] - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 1. Koordinatları ROS topic'ine bas (JSON String)
        out_msg = String()
        out_msg.data = json.dumps(detections_payload)
        self.pub_detections.publish(out_msg)

        # 2. İşlenmiş görüntüyü ROS topic'ine bas
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.pub_annotated.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f"Görüntü yayınlama hatası: {str(e)}")

    def destroy_node(self):
        self.rknn.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = NPUPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## **7. Adım 5: Bağımlılıklar ve Derleme (`colcon build`)**

### **`package.xml` Dosyasını Güncelleyin:**
`~/ros2_ws/src/opi5_perception/package.xml` dosyasına şu bağımlılıkları ekleyin:
```xml
  <exec_depend>rclpy</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>cv_bridge</exec_depend>
  <exec_depend>python3-opencv</exec_depend>
```

### **Paketi Derleyin:**
```bash
cd ~/ros2_ws
colcon build --symlink-install

# Yeni derlenen paketi kabuk ortamına tanıtın:
source install/setup.bash
```

---

## **8. Adım 6: Canlı Test ve Doğrulama**

Sistemi test etmek için iki ayrı terminal kullanacağız:

### **Terminal 1: Test Kamera Yayıncısı Başlatın:**
Eğer elinizde bir ROS kamera sürücüsü henüz yoksa, OpenCV ile `/camera/image_raw` yayınlayan hızlı bir test düğümü başlatabilirsiniz (veya USB kamerayı bağlayın):
```bash
# Standart v4l2 kamera düğümünü kurup çalıştırabilirsiniz:
sudo apt install -y ros-humble-v4l2-camera
ros2 run v4l2_camera v4l2_camera_node
```

### **Terminal 2: NPU Algılama Düğümünü Başlatın:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run opi5_perception npu_detector
```

### **Terminal 3: Robotun Gördüğü Koordinatları İzleyin:**
```bash
ros2 topic echo /detected_objects
```
**Beklenen JSON Çıktısı:**
```json
[{"class": "person", "confidence": 0.88, "bbox": [120, 85, 340, 470], "center": [230, 277]}]
```
*Robotunuz kamerada gördüğü insanın veya engelin piksel merkezini mikrosaniyeler içinde aldı! Bu koordinatları kullanarak doğrudan motor kontrol düğümünüze (`cmd_vel`) dönüş veya ileri komutu verebilirsiniz.*

---

## **9. Sık Karşılaşılan Sorunlar ve Çözümleri**

| Sorun | Kök Neden | Çözüm |
| :--- | :--- | :--- |
| **`cv_bridge` kütüphanesi Python sürümü uyuşmazlığı** | Python 3.10 dışı ortamlarda binary uyumsuzluğu. | `sudo apt install ros-humble-cv-bridge` ile resmi binary paketini kullanın. |
| **`colcon build` bellek yetersizliği hatası** | Tüm CPU çekirdekleri paralel derlerken RAM doldu. | `colcon build --parallel-workers 2` parametresiyle iş parçacığı sayısını sınırlandırın. |
| **Robot mesajları gecikmeli alıyor** | DDS multicast trafiği ağ kartını tıkıyor. | `export ROS_DOMAIN_ID=42` tanımlayarak benzersiz bir alan kimliği oluşturun. |
| **`Package 'opi5_perception' not found`** | Çalışma alanı ortam değişkeni yüklenmedi. | `source ~/ros2_ws/install/setup.bash` komutunu çalıştırın. |

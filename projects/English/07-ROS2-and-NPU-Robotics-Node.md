# **Orange Pi 5 (RK3588S) ROS 2 Setup and NPU Robotics Node Guide**

This guide provides an end-to-end walkthrough for deploying the industry-standard robotic framework **ROS 2 (Robot Operating System - Humble Hawksbill)** on the Orange Pi 5 (Rockchip RK3588S), tuning DDS network topology, and building a high-throughput **NPU Perception Node** that detects obstacles/objects in real time using the **6 TOPS NPU** and publishes coordinate vectors to autonomous navigation stacks.

---

## **1. Why Orange Pi 5 for ROS 2?**

Autonomous Mobile Robots (AMR), drones, and automated rovers require heavy parallel computing for simultaneous sensor ingestion and path planning:
* **The Traditional SBC Bottleneck:** On boards like the Raspberry Pi 4, running neural networks saturates all CPU cores to 100%, starving critical RTOS schedulers, LiDAR SLAM, and Nav2 controllers.
* **The Orange Pi 5 Advantage:** While the 8-core CPU executes Nav2, kinematics, and motor controllers; the **tri-core 6 TOPS NPU** offloads vision inference at 70+ FPS with **~2% CPU overhead**. Target centroids are dispatched across ROS 2 DDS topics in sub-milliseconds.

```
┌────────────────────────────────────────────────────────────────────────┐
│                  Orange Pi 5 (RK3588S) ROS 2 Topology                  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────┴────────────────────────────────────┐
│  Camera / Sensor Node                                                  │
│  - Ingests frames from USB / CSI / RTSP source                         │
│  - Topic: `/camera/image_raw` [sensor_msgs/msg/Image]                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼ (DDS Shared Memory)
┌───────────────────────────────────┴────────────────────────────────────┐
│  NPU Perception Node (RKNN YOLOv8)                                     │
│  - Executes inference across tri-core NPU (CPU load: ~2%)             │
│  - Calculates obstacle centroids & bounds                              │
│  - Topic: `/detected_objects` [std_msgs/msg/String (JSON Coordinates)] │
│  - Topic: `/camera/annotated_image` [sensor_msgs/msg/Image]            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────┴────────────────────────────────────┐
│  Autonomous Navigation & Actuation (Nav2 / Motor Node)                 │
│  - Obstacle avoidance or visual target following                       │
│  - Topic: `/cmd_vel` [geometry_msgs/msg/Twist] -> Motor Controllers    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **2. Architecture & Networking Considerations**

1. **Multicast Storm Prevention (`ROS_DOMAIN_ID`):** ROS 2 DDS layers (FastDDS / CycloneDDS) use UDP multicast for dynamic peer discovery. On shared networks (lab, campus, or home Wi-Fi), cross-talk between multiple robots can saturate network interfaces. Assigning an explicit `ROS_DOMAIN_ID` isolates traffic.
2. **System Locale:** ROS 2 tooling strictly mandates UTF-8 encoding. Non-UTF-8 configurations raise fatal `UnicodeEncodeError` exceptions in Python CLI tools.
3. **Headless Base Footprint:** Deploying `ros-humble-ros-base` instead of the full desktop bundle saves >3GB of storage and 400MB+ of resident RAM.

---

## **3. Step 1: Locale Configuration & Repository Setup**

On your Orange Pi 5 terminal:

```bash
# 1. Verify & Configure UTF-8 Locale:
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Enable Ubuntu Universe:
sudo apt install -y software-properties-common curl gnupg lsb-release
sudo add-apt-repository universe

# 3. Import Official ROS 2 GPG Key:
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 4. Add Official ROS 2 ARM64 Repository:
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

---

## **4. Step 2: Install ROS 2 Humble / Jazzy & Robotics Tooling**

> [!NOTE]
> **Ubuntu Release Compatibility:**
> * **Ubuntu 22.04 LTS (Jammy):** The official standard LTS distribution is **`ros-humble`**.
> * **Ubuntu 24.04 LTS (Noble):** If running on Ubuntu 24.04, substitute `humble` with **`jazzy`** (ROS 2 Jazzy Jalisco) packages (`ros-jazzy-ros-base`, `ros-jazzy-cv-bridge`, and `source /opt/ros/jazzy/setup.bash`).

```bash
sudo apt update

# Automatically detect ROS 2 distribution from Ubuntu release:
# (Ubuntu 24.04 Noble -> jazzy | Ubuntu 22.04 Jammy -> humble)
ROS_DISTRO=$(source /etc/os-release && [ "$UBUNTU_CODENAME" = "noble" ] && echo "jazzy" || echo "humble")
echo "Selected ROS 2 Distribution: $ROS_DISTRO"

# Install base ROS 2 packages and developer tools:
sudo apt install -y ros-${ROS_DISTRO}-ros-base \
                    ros-dev-tools \
                    python3-colcon-common-extensions \
                    python3-rosdep \
                    ros-${ROS_DISTRO}-cv-bridge \
                    ros-${ROS_DISTRO}-vision-msgs

# Initialize rosdep
sudo rosdep init 2>/dev/null || true
rosdep update
```

### **Persist Environment Configuration (`~/.bashrc`):**
```bash
echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source /opt/ros/${ROS_DISTRO}/setup.bash
```

### **Verify Node Communication:**
```bash
ros2 topic list
```
*Confirms `/parameter_events` and `/rosout` are operational.*

---

## **5. Step 3: Workspace & Package Generation**

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Scaffold python perception package
ros2 pkg create --build-type ament_python --node-name npu_detector opi5_perception
```

---

## **6. Step 4: Implement NPU Perception Node (`npu_detector.py`)**

Edit `~/ros2_ws/src/opi5_perception/opi5_perception/npu_detector.py`:

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
        
        # Initialize RKNN NPU Engine
        self.get_logger().info("[*] Initializing RKNN NPU Engine...")
        self.rknn = RKNNLite()
        if self.rknn.load_rknn(MODEL_PATH) != 0:
            self.get_logger().error("[-] Failed to load RKNN model file!")
            return
            
        # Target tri-core NPU accelerator
        if self.rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2) != 0:
            self.get_logger().error("[-] Failed to initialize NPU runtime!")
            return
        self.get_logger().info("[+] Tri-core RK3588S NPU operational!")

        # Subscriber: Raw sensor stream
        self.sub_cam = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Publishers: Object coordinates and visual debug stream
        self.pub_detections = self.create_publisher(String, '/detected_objects', 10)
        self.pub_annotated = self.create_publisher(Image, '/camera/annotated_image', 10)

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"CvBridge decode error: {str(e)}")
            return

        orig_h, orig_w = frame.shape[:2]

        # Model input formatting
        input_img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = np.expand_dims(input_img, axis=0)

        # Forward pass on NPU
        outputs = self.rknn.rknn_run(inputs=[input_img])

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

                center_x = int((bx[0] + bx[2]) / 2)
                center_y = int((bx[1] + bx[3]) / 2)

                detections_payload.append({
                    "class": cls_name,
                    "confidence": round(score, 2),
                    "bbox": [int(bx[0]), int(bx[1]), int(bx[2]), int(bx[3])],
                    "center": [center_x, center_y]
                })

                cv2.rectangle(frame, (bx[0], bx[1]), (bx[2], bx[3]), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 4, (0, 0, 255), -1)
                cv2.putText(frame, f"{cls_name} {score:.2f}", (bx[0], max(20, bx[1] - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Publish target coordinates as JSON
        out_msg = String()
        out_msg.data = json.dumps(detections_payload)
        self.pub_detections.publish(out_msg)

        # Publish debug annotated image
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.pub_annotated.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish debug image: {str(e)}")

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

## **7. Step 5: Compilation via `colcon`**

### **Add Dependencies to `package.xml`:**
Open `~/ros2_ws/src/opi5_perception/package.xml`:
```xml
  <exec_depend>rclpy</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>cv_bridge</exec_depend>
  <exec_depend>python3-opencv</exec_depend>
```

### **Build Package:**
```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

---

## **8. Step 6: Testing & Telemetry Verification**

### **1. Launch Camera Publisher:**
```bash
sudo apt install -y ros-humble-v4l2-camera
ros2 run v4l2_camera v4l2_camera_node
```

### **2. Launch NPU Perception Node:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 run opi5_perception npu_detector
```

### **3. Inspect Target Vectors:**
```bash
ros2 topic echo /detected_objects
```
**Sample JSON Stream:**
```json
[{"class": "person", "confidence": 0.88, "bbox": [120, 85, 340, 470], "center": [230, 277]}]
```
*The autonomous navigation planner (Nav2) directly consumes these target centroids to steer robotic kinematics with zero CPU vision load.*

---

## **9. Troubleshooting & Common Issues**

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **`cv_bridge` ABI mismatch** | Attempting to link non-system Python builds. | Install system apt binary: `sudo apt install ros-humble-cv-bridge`. |
| **`colcon` Out of Memory** | Exhausted RAM during concurrent package compilation. | Restrict workers: `colcon build --parallel-workers 2`. |
| **DDS high latency or message loss** | Multicast traffic congestion across local subnet. | Set unique isolated domain: `export ROS_DOMAIN_ID=42`. |
| **`Package not found`** | Workspace overlay not sourced in current shell. | Execute `source ~/ros2_ws/install/setup.bash`. |

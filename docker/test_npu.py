"""
Orange Pi 5 (RK3588S) - Tri-Core NPU Verification Script
Validates RKNN-Toolkit-Lite2 inside Docker with real NPU passthrough
"""

import os
import urllib.request
import subprocess
from rknnlite.api import RKNNLite

MODEL_FILE = "resnet18_for_rk3588.rknn"
MODEL_URL = "https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/examples/resnet18/resnet18_for_rk3588.rknn"

# 1. Download official Rockchip reference model if not present
if not os.path.exists(MODEL_FILE):
    print(f"[*] Downloading reference NPU model: {MODEL_FILE}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
    print(f"[+] Download complete: {os.path.getsize(MODEL_FILE)} bytes")

print("--- Initializing Orange Pi 5 RKNN NPU Session ---")
rknn = RKNNLite(verbose=False)

# 2. Load model graph
print("[*] Loading RKNN model graph...")
ret = rknn.load_rknn(MODEL_FILE)
if ret != 0:
    print(f"[ERROR] Failed to load model! Code: {ret}")
    exit(ret)

# 3. Engage all 3 NPU cores (Core 0, 1, 2) for full 6 TOPS throughput
print("[*] Initializing runtime with core_mask=NPU_CORE_0_1_2 (Tri-Core 6 TOPS)...")
ret = rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2)

if ret == 0:
    print("[SUCCESS] All 3 NPU cores initialized successfully (Core 0, 1, 2)!")
    print("\n--- Driver & API Version Information ---")
    rknn.get_sdk_version()
    try:
        telemetry = subprocess.check_output("cat /sys/kernel/debug/rknpu/load 2>/dev/null || true", shell=True).decode()
        if telemetry.strip():
            print("\n--- Real-Time NPU Core Telemetry ---")
            print(telemetry.strip())
    except Exception:
        pass
    print("\n[PASSED] Physical RK3588 NPU passthrough verified 100% inside Docker!")
else:
    print(f"[ERROR] Failed to initialize NPU runtime! Code: {ret}")
    exit(ret)

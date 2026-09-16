#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Smart Zoom & Super-Resolution Benchmark
Compares classical interpolation (Nearest, Bilinear, Bicubic, Lanczos) vs. 
Neural Super-Resolution (FSRCNN, ESPCN) on Orange Pi 5 (RK3588S).
"""

import os
import sys
import time
import argparse
import cv2
from cv2 import dnn_superres
import numpy as np

def get_soc_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read().strip()) / 1000.0
    except Exception:
        return 0.0

def crop_center(frame, crop_w, crop_h):
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    x1 = max(0, cx - crop_w // 2)
    y1 = max(0, cy - crop_h // 2)
    x2 = min(w, x1 + crop_w)
    y2 = min(h, y1 + crop_h)
    return frame[y1:y2, x1:x2], (x1, y1, x2, y2)

def annotate_tile(img, title, latency_ms=None, subtitle=None):
    out = img.copy()
    h, w = out.shape[:2]
    
    # Top banner overlay
    banner_h = 42
    overlay = out.copy()
    cv2.rectangle(overlay, (0, 0), (w, banner_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, out, 0.25, 0, out)
    
    # Title
    cv2.putText(out, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Subtitle or latency
    sub_text = ""
    if latency_ms is not None:
        sub_text += f"{latency_ms:.2f} ms ({1000.0 / max(latency_ms, 0.001):.1f} FPS)"
    if subtitle:
        sub_text += f" | {subtitle}" if sub_text else subtitle
        
    if sub_text:
        cv2.putText(out, sub_text, (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 200), 1, cv2.LINE_AA)
        
    # Border
    cv2.rectangle(out, (0, 0), (w - 1, h - 1), (60, 60, 60), 1)
    return out

def main():
    parser = argparse.ArgumentParser(description="AI Super-Resolution Zoom Benchmark for Orange Pi 5")
    parser.add_argument("--source", type=str, default="0", help="Camera index (e.g. 0) or image file path")
    parser.add_argument("--scale", type=int, choices=[2, 4], default=2, help="Upscale factor (2 or 4)")
    parser.add_argument("--crop-size", type=int, default=240, help="Width/Height of the cropped ROI")
    parser.add_argument("--output", type=str, default="zoom_comparison.jpg", help="Output comparison image path")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup iterations for accurate timing")
    parser.add_argument("--runs", type=int, default=15, help="Benchmark iterations to average")
    args = parser.parse_args()

    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    scale = args.scale
    
    print("=" * 72)
    print("🎯 ORANGE PI 5 (RK3588S) AI SMART ZOOM & SUPER-RESOLUTION BENCHMARK")
    print("=" * 72)
    print(f"[*] Target Scale Factor : {scale}x Digital Zoom")
    print(f"[*] Input Source        : {args.source}")
    print(f"[*] ROI Crop Window     : {args.crop_size}x{args.crop_size} px")
    print(f"[*] Output Target       : {args.output}")

    # 1. Acquire Input Frame
    if args.source.isdigit():
        cam_idx = int(args.source)
        print(f"[*] Opening hardware camera index {cam_idx} (FourCC: MJPG, 1920x1080)...")
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        if not cap.isOpened():
            print(f"[HATA] Cannot open camera index {cam_idx}!")
            sys.exit(1)
            
        # Discard first few warmup frames
        for _ in range(10):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print("[HATA] Failed to capture valid frame from camera!")
            sys.exit(1)
    else:
        if not os.path.exists(args.source):
            print(f"[HATA] Image file not found: {args.source}")
            sys.exit(1)
        frame = cv2.imread(args.source)
        if frame is None:
            print(f"[HATA] Cannot decode image: {args.source}")
            sys.exit(1)

    orig_h, orig_w = frame.shape[:2]
    print(f"[OK] Source frame captured successfully: {orig_w}x{orig_h} px")

    # 2. Extract Center ROI
    roi_lowres, bbox = crop_center(frame, args.crop_size, args.crop_size)
    target_w = args.crop_size * scale
    target_h = args.crop_size * scale
    print(f"[*] Extracted Low-Res ROI : {roi_lowres.shape[1]}x{roi_lowres.shape[0]} px at bbox {bbox}")
    print(f"[*] Target Zoomed Output  : {target_w}x{target_h} px")

    # 3. Initialize AI Models
    print("\n[*] Loading Deep Learning Super-Resolution Models...")
    
    # FSRCNN
    fsrcnn_path = os.path.join(models_dir, f"FSRCNN_x{scale}.pb")
    sr_fsrcnn = None
    if os.path.exists(fsrcnn_path):
        sr_fsrcnn = dnn_superres.DnnSuperResImpl_create()
        sr_fsrcnn.readModel(fsrcnn_path)
        sr_fsrcnn.setModel("fsrcnn", scale)
        sr_fsrcnn.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        sr_fsrcnn.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print(f"  [+] FSRCNN x{scale} loaded: {fsrcnn_path}")
    else:
        print(f"  [-] FSRCNN model not found at: {fsrcnn_path}")

    # ESPCN
    espcn_path = os.path.join(models_dir, f"ESPCN_x{scale}.pb")
    sr_espcn = None
    if os.path.exists(espcn_path):
        sr_espcn = dnn_superres.DnnSuperResImpl_create()
        sr_espcn.readModel(espcn_path)
        sr_espcn.setModel("espcn", scale)
        sr_espcn.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        sr_espcn.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print(f"  [+] ESPCN x{scale} loaded: {espcn_path}")
    else:
        print(f"  [-] ESPCN model not found at: {espcn_path}")

    # Rockchip RK3588 Tri-Core NPU Model
    try:
        from rknnlite.api import RKNNLite
    except ImportError:
        RKNNLite = None

    rknn_sr = None
    rknn_path = os.path.join(models_dir, "super_resolution_rk3588.rknn")
    if RKNNLite is not None and os.path.exists(rknn_path):
        try:
            rknn = RKNNLite()
            if rknn.load_rknn(rknn_path) == 0 and rknn.init_runtime(core_mask=RKNNLite.NPU_CORE_0_1_2) == 0:
                rknn_sr = rknn
                print(f"  [+] RK3588 NPU ESPCN (Tri-Core 6 TOPS) loaded: {rknn_path}")
        except Exception as e:
            print(f"  [-] Failed to load NPU model: {e}")

    results = {}

    def run_npu_sr(img, sharpen=False):
        resized = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
        ycrcb = cv2.cvtColor(resized, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        y_in = (y.astype(np.float32) / 255.0).reshape(1, 1, 224, 224)
        out = rknn_sr.inference(inputs=[y_in])
        out_y = np.clip(out[0][0, 0] * 255.0, 0, 255).astype(np.uint8)
        cr_up = cv2.resize(cr, (672, 672), interpolation=cv2.INTER_CUBIC)
        cb_up = cv2.resize(cb, (672, 672), interpolation=cv2.INTER_CUBIC)
        merged = cv2.merge([out_y, cr_up, cb_up])
        res = cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)
        if sharpen:
            yc = cv2.cvtColor(res, cv2.COLOR_BGR2YCrCb)
            yp, cp1, cp2 = cv2.split(yc)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            yp = clahe.apply(yp)
            res = cv2.cvtColor(cv2.merge([yp, cp1, cp2]), cv2.COLOR_YCrCb2BGR)
            gauss = cv2.GaussianBlur(res, (0, 0), 2.0)
            res = cv2.addWeighted(res, 2.4, gauss, -1.4, 0)
        if (res.shape[1], res.shape[0]) != (target_w, target_h):
            res = cv2.resize(res, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        return res

    # 4. Benchmark Methods
    methods = [
        ("Nearest Neighbor", lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_NEAREST)),
        ("Bilinear",         lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)),
        ("Bicubic (Standard)",lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)),
        ("Lanczos-4",        lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)),
    ]

    if sr_fsrcnn is not None:
        methods.append((f"FSRCNN x{scale} (CPU AI)", lambda img: sr_fsrcnn.upsample(img)))
    if sr_espcn is not None:
        methods.append((f"ESPCN x{scale} (CPU AI)",  lambda img: sr_espcn.upsample(img)))
    if rknn_sr is not None:
        methods.append(("RK3588 NPU (ESPCN 3x AI)", lambda img: run_npu_sr(img, False)))
        methods.append(("NPU + Smart Enhancer",      lambda img: run_npu_sr(img, True)))

    print("\n[*] Running Timing Benchmarks (Warmup: %d, Runs: %d)..." % (args.warmup, args.runs))
    print("-" * 72)
    print(f"{'Algorithm / Method':<26} | {'Type':<10} | {'Latency (ms)':<14} | {'Est. FPS':<10}")
    print("-" * 72)

    for name, func in methods:
        # Warmup
        for _ in range(args.warmup):
            _ = func(roi_lowres)
            
        # Timed runs
        timings = []
        out_img = None
        for _ in range(args.runs):
            t0 = time.perf_counter()
            out_img = func(roi_lowres)
            t1 = time.perf_counter()
            timings.append((t1 - t0) * 1000.0)
            
        avg_ms = float(np.mean(timings))
        fps = 1000.0 / max(avg_ms, 0.0001)
        algo_type = "NPU 6 TOPS" if "NPU" in name else ("CPU AI" if "AI" in name else "Classical")
        print(f"{name:<26} | {algo_type:<10} | {avg_ms:8.2f} ms     | {fps:7.1f} FPS")
        results[name] = {"img": out_img, "ms": avg_ms, "fps": fps}

    print("-" * 72)
    soc_temp = get_soc_temperature()
    if soc_temp > 0:
        print(f"[*] Orange Pi 5 SoC Temperature after benchmark: {soc_temp:.1f} °C")

    # 5. Composite Comparison Grid
    print(f"\n[*] Generating multi-panel comparison visualization: {args.output}...")
    
    tiles = []
    # 1. Bicubic (Standard)
    if "Bicubic (Standard)" in results:
        tiles.append(annotate_tile(results["Bicubic (Standard)"]["img"], f"1. Bicubic Standard ({scale}x)", results["Bicubic (Standard)"]["ms"], "Blurry Baseline"))
    # 2. Lanczos-4
    if "Lanczos-4" in results:
        tiles.append(annotate_tile(results["Lanczos-4"]["img"], f"2. Lanczos-4 Classical ({scale}x)", results["Lanczos-4"]["ms"], "Edge Ringing"))
    # 3. FSRCNN (CPU AI)
    fsrcnn_key = f"FSRCNN x{scale} (CPU AI)"
    if fsrcnn_key in results:
        tiles.append(annotate_tile(results[fsrcnn_key]["img"], f"3. FSRCNN ({scale}x CPU AI)", results[fsrcnn_key]["ms"], "Sharp Edges"))
    # 4. ESPCN (CPU AI)
    espcn_key = f"ESPCN x{scale} (CPU AI)"
    if espcn_key in results:
        tiles.append(annotate_tile(results[espcn_key]["img"], f"4. ESPCN ({scale}x CPU AI)", results[espcn_key]["ms"], "Real-Time CPU"))
    # 5. RK3588 NPU (ESPCN 3x AI)
    if "RK3588 NPU (ESPCN 3x AI)" in results:
        tiles.append(annotate_tile(results["RK3588 NPU (ESPCN 3x AI)"]["img"], "5. RK3588 NPU (ESPCN 3x)", results["RK3588 NPU (ESPCN 3x AI)"]["ms"], "Tri-Core 6 TOPS"))
    # 6. NPU + Smart Enhancer
    if "NPU + Smart Enhancer" in results:
        tiles.append(annotate_tile(results["NPU + Smart Enhancer"]["img"], "6. NPU + Smart Enhancer", results["NPU + Smart Enhancer"]["ms"], "Max Clarity / CLAHE"))

    if len(tiles) >= 6:
        row1 = np.hstack(tiles[:3])
        row2 = np.hstack(tiles[3:6])
        grid = np.vstack([row1, row2])
    elif len(tiles) >= 4:
        row1 = np.hstack(tiles[:2])
        row2 = np.hstack(tiles[2:4])
        grid = np.vstack([row1, row2])
    elif len(tiles) >= 2:
        grid = np.hstack(tiles[:2])
    else:
        grid = tiles[0]

    # Add master title header
    header = np.zeros((60, grid.shape[1], 3), dtype=np.uint8)
    cv2.putText(header, f"Orange Pi 5 (RK3588S) AI Smart Zoom: NPU (6 TOPS) vs. CPU AI vs. Classical Interpolation", 
                (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 255, 255), 2, cv2.LINE_AA)
    final_output = np.vstack([header, grid])

    cv2.imwrite(args.output, final_output)
    print(f"[SUCCESS] Benchmark complete! Comparison saved to: {args.output}")

    if rknn_sr is not None:
        rknn_sr.release()

if __name__ == "__main__":
    main()

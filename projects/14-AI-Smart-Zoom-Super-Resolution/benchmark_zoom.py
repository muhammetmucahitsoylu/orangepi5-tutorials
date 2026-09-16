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
        cap = cv2.VideoCapture(cam_idx)
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

    results = {}

    # 4. Benchmark Methods
    methods = [
        ("Nearest Neighbor", lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_NEAREST)),
        ("Bilinear",         lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LINEAR)),
        ("Bicubic (Standard)",lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_CUBIC)),
        ("Lanczos-4",        lambda img: cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)),
    ]

    if sr_fsrcnn is not None:
        methods.append((f"FSRCNN x{scale} (AI)", lambda img: sr_fsrcnn.upsample(img)))
    if sr_espcn is not None:
        methods.append((f"ESPCN x{scale} (AI)",  lambda img: sr_espcn.upsample(img)))

    print("\n[*] Running Timing Benchmarks (Warmup: %d, Runs: %d)..." % (args.warmup, args.runs))
    print("-" * 72)
    print(f"{'Algorithm / Method':<24} | {'Type':<10} | {'Latency (ms)':<14} | {'Est. FPS':<10}")
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
        algo_type = "Neural Net" if "(AI)" in name else "Classical"
        print(f"{name:<24} | {algo_type:<10} | {avg_ms:8.2f} ms     | {fps:7.1f} FPS")
        results[name] = {"img": out_img, "ms": avg_ms, "fps": fps}

    print("-" * 72)
    soc_temp = get_soc_temperature()
    if soc_temp > 0:
        print(f"[*] Orange Pi 5 SoC Temperature after benchmark: {soc_temp:.1f} °C")

    # 5. Composite Comparison Grid
    print(f"\n[*] Generating multi-panel comparison visualization: {args.output}...")
    
    # We will build a 2x3 or 2x2 grid
    tiles = []
    # 1. Bicubic (Standard)
    if "Bicubic (Standard)" in results:
        tiles.append(annotate_tile(results["Bicubic (Standard)"]["img"], f"1. Standard Bicubic Zoom ({scale}x)", results["Bicubic (Standard)"]["ms"], "Blurry Baseline"))
    # 2. Lanczos-4
    if "Lanczos-4" in results:
        tiles.append(annotate_tile(results["Lanczos-4"]["img"], f"2. Lanczos-4 Classical ({scale}x)", results["Lanczos-4"]["ms"], "Edge Ringing"))
    # 3. FSRCNN (AI)
    fsrcnn_key = f"FSRCNN x{scale} (AI)"
    if fsrcnn_key in results:
        tiles.append(annotate_tile(results[fsrcnn_key]["img"], f"3. FSRCNN Neural Zoom ({scale}x)", results[fsrcnn_key]["ms"], "Sharp Edges / AI"))
    # 4. ESPCN (AI)
    espcn_key = f"ESPCN x{scale} (AI)"
    if espcn_key in results:
        tiles.append(annotate_tile(results[espcn_key]["img"], f"4. ESPCN Sub-Pixel ({scale}x)", results[espcn_key]["ms"], "Real-Time AI"))

    if len(tiles) >= 4:
        row1 = np.hstack([tiles[0], tiles[1]])
        row2 = np.hstack([tiles[2], tiles[3]])
        grid = np.vstack([row1, row2])
    elif len(tiles) >= 2:
        grid = np.hstack(tiles[:2])
    else:
        grid = tiles[0]

    # Add master title header
    header = np.zeros((60, grid.shape[1], 3), dtype=np.uint8)
    cv2.putText(header, f"Orange Pi 5 (RK3588S) AI Digital Zoom vs. Classical Interpolation ({scale}x Zoom)", 
                (20, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)
    final_output = np.vstack([header, grid])

    cv2.imwrite(args.output, final_output)
    print(f"[SUCCESS] Benchmark complete! Comparison saved to: {args.output}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ONNX to RKNN Super-Resolution Model Converter
Compiles ESPCN / Sub-Pixel CNN to Rockchip RK3588 NPU binary format.
"""

import os
import sys
from rknn.api import RKNN

def convert_super_resolution():
    model_dir = os.path.dirname(os.path.abspath(__file__))
    onnx_path = os.path.join(model_dir, "super-resolution-10.onnx")
    rknn_path = os.path.join(model_dir, "super_resolution_rk3588.rknn")
    
    if not os.path.exists(onnx_path):
        print(f"[ERROR] ONNX model not found: {onnx_path}")
        sys.exit(1)
        
    rknn = RKNN(verbose=False)
    
    print("=" * 68)
    print("🚀 CONVERTING SUPER-RESOLUTION ONNX TO RK3588 NPU BINARY (.rknn)")
    print("=" * 68)
    print(f"[*] Input ONNX Path     : {onnx_path}")
    print(f"[*] Target Hardware     : Rockchip RK3588 / RK3588S")
    print(f"[*] Input Tensor Shape  : [1, 1, 224, 224] (Y-Luminance)")
    print(f"[*] Expected Output     : [1, 1, 672, 672] (3x Super-Res)")
    print(f"[*] Output Binary       : {rknn_path}")
    
    print("\n--> Step 1: Configuring RKNN Target Platform (rk3588)...")
    rknn.config(
        target_platform='rk3588',
        optimization_level=3
    )
    
    print("--> Step 2: Loading ONNX graph...")
    ret = rknn.load_onnx(
        model=onnx_path,
        inputs=['input'],
        input_size_list=[[1, 1, 224, 224]]
    )
    if ret != 0:
        print(f"[ERROR] load_onnx failed with error code: {ret}")
        sys.exit(ret)
        
    print("--> Step 3: Compiling Graph for RK3588 NPU...")
    ret = rknn.build(do_quantization=False)
    if ret != 0:
        print(f"[ERROR] build failed with error code: {ret}")
        sys.exit(ret)
        
    print("--> Step 4: Exporting .rknn binary...")
    ret = rknn.export_rknn(rknn_path)
    if ret != 0:
        print(f"[ERROR] export_rknn failed with error code: {ret}")
        sys.exit(ret)
        
    print("\n" + "=" * 68)
    print(f"✅ SUCCESS: RKNN model saved to: {rknn_path}")
    print(f"   Model Size: {os.path.getsize(rknn_path):,} bytes")
    print("=" * 68)
    rknn.release()

if __name__ == "__main__":
    convert_super_resolution()

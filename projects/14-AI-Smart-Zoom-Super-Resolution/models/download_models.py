#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-trained Super-Resolution Model Downloader
Downloads FSRCNN (x2, x4) and ESPCN (x2, x4) models for real-time AI zoom.
"""

import os
import urllib.request

RELEASE_BASE = "https://github.com/muhammetmucahitsoylu/orangepi5-tutorials/releases/download/v2.0.0"

MODELS = {
    "super_resolution_rk3588.rknn": f"{RELEASE_BASE}/super_resolution_rk3588.rknn",
    "super-resolution-10.onnx": f"{RELEASE_BASE}/super-resolution-10.onnx",
    "ESPCN_x2.pb":  f"{RELEASE_BASE}/ESPCN_x2.pb",
    "ESPCN_x4.pb":  f"{RELEASE_BASE}/ESPCN_x4.pb",
    "FSRCNN_x2.pb": f"{RELEASE_BASE}/FSRCNN_x2.pb",
    "FSRCNN_x4.pb": f"{RELEASE_BASE}/FSRCNN_x4.pb",
}

def main():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[*] Checking Super-Resolution models in: {cur_dir}")
    
    for filename, url in MODELS.items():
        target = os.path.join(cur_dir, filename)
        if os.path.exists(target) and os.path.getsize(target) > 1000:
            print(f"  [OK] {filename} exists ({os.path.getsize(target):,} bytes)")
        else:
            print(f"  [>] Downloading {filename} from Release v2.0.0...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req) as resp, open(target, 'wb') as f:
                    f.write(resp.read())
                print(f"  [DONE] Saved {filename} ({os.path.getsize(target):,} bytes)")
            except Exception as e:
                print(f"  [ERROR] Failed to download {filename}: {e}")
    
    print("[*] All Super-Resolution models are ready!")

if __name__ == "__main__":
    main()
